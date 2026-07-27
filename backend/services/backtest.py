"""
Backtesting harness — replays historical Binance data through the real
strategy engines.

Live paper trading produces a few hundred trades a week, all from whatever
market regime happens to be running. This replays months of history in
minutes, so a strategy can be judged across rallies, crashes and chop.

The strategies are used *unmodified*. Instead of rewriting them for replay,
each one is handed:

  * a ReplayExchange that serves historical candles up to a moving cursor
  * a simulated clock, so timeouts and rebalances fire on market time rather
    than wall-clock time (a backtest runs far faster than real time, so
    unpatched timeouts would never trigger)
  * a patched asyncio.sleep that advances that clock instead of waiting

This matters: whatever the backtest proves is true of the code that actually
trades, not of a parallel reimplementation that might quietly differ.
"""

from __future__ import annotations

import asyncio
import time as _time_module
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Any

import pandas as pd

from backend.schemas.bot import DEFAULT_CONFIGS, STRATEGY_LABELS
from backend.services import costs, metrics
from backend.services.bot_runner import STRATEGY_MAP

CACHE_DIR = Path(__file__).resolve().parents[2] / "backtest_data"

# Strategies ask for these; all are derived from 1m candles.
_TF_PANDAS = {"1m": "1min", "3m": "3min", "5m": "5min", "15m": "15min",
              "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1D"}


class BacktestComplete(BaseException):
    """Raised when history runs out.

    Deliberately a BaseException: every strategy wraps its loop in
    `except Exception` to survive exchange errors, so an ordinary exception
    would be swallowed and the backtest would spin forever.
    """


class Clock:
    """Simulated market time, advanced by the strategies' own sleep calls."""

    def __init__(self, start: datetime):
        self._now = start.timestamp()

    def now(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += max(float(seconds), 1.0)  # never stall on sleep(0)

    @property
    def dt(self) -> datetime:
        return datetime.fromtimestamp(self._now, UTC)


class _LoopProxy:
    """Delegates to the real event loop but reports simulated time."""

    def __init__(self, real, clock: Clock):
        self._real, self._clock = real, clock

    def time(self) -> float:
        return self._clock.now()

    def __getattr__(self, name):
        return getattr(self._real, name)


class _AsyncioShim:
    """asyncio with sleep that advances market time instead of waiting."""

    def __init__(self, clock: Clock):
        self._clock = clock

    async def sleep(self, seconds: float = 0, *args, **kwargs):
        self._clock.advance(seconds)
        await asyncio.sleep(0)  # let other tasks run, but consume no real time

    def get_running_loop(self):
        return _LoopProxy(asyncio.get_running_loop(), self._clock)

    def get_event_loop(self):
        return _LoopProxy(asyncio.get_event_loop(), self._clock)

    def __getattr__(self, name):
        return getattr(asyncio, name)


class _TimeShim:
    def __init__(self, clock: Clock):
        self._clock = clock

    def time(self) -> float:
        return self._clock.now()

    def __getattr__(self, name):
        return getattr(_time_module, name)


class ReplayExchange:
    """Serves historical candles and prices as of the clock's current time."""

    def __init__(self, data: dict[str, pd.DataFrame], clock: Clock):
        self._clock = clock
        self._base = data
        self._frames: dict[tuple[str, str], pd.DataFrame] = {}
        self._arrays_cache: dict[tuple[str, str], tuple] = {}

    def _frame(self, symbol: str, timeframe: str) -> pd.DataFrame:
        key = (symbol, timeframe)
        if key not in self._frames:
            df = self._base[symbol]
            if timeframe == "1m":
                out = df
            else:
                rule = _TF_PANDAS.get(timeframe, "5min")
                # Carry the bin's opening timestamp straight through rather
                # than deriving it from the datetime index: pandas preserves
                # datetime64[ms] here, so an assumed-nanosecond conversion
                # silently produces timestamps 10^6 too small.
                out = (
                    df.set_index("dt")
                    .resample(rule)
                    .agg({"timestamp": "first", "open": "first", "high": "max",
                          "low": "min", "close": "last", "volume": "sum"})
                    .dropna()
                    .reset_index()
                )
                out["timestamp"] = out["timestamp"].astype("int64")
            self._frames[key] = out
        return self._frames[key]

    def _arrays(self, symbol: str, timeframe: str):
        """Raw numpy views, built once — slicing these is far cheaper than
        re-slicing a DataFrame on every poll of every symbol."""
        key = (symbol, timeframe)
        if key not in self._arrays_cache:
            df = self._frame(symbol, timeframe)
            self._arrays_cache[key] = (
                df["timestamp"].to_numpy(),
                df[["timestamp", "open", "high", "low", "close", "volume"]].to_numpy(),
                df["close"].to_numpy(),
            )
        return self._arrays_cache[key]

    def _cursor(self, stamps) -> int:
        """Index of the last candle that has closed at the current sim time."""
        return int(stamps.searchsorted(self._clock.now() * 1000, side="right"))

    async def fetch_ohlcv(self, symbol: str, timeframe: str = "1m", limit: int = 100):
        stamps, rows, _ = self._arrays(symbol, timeframe)
        end = self._cursor(stamps)
        if end <= 0:
            return []
        if end >= len(stamps):
            raise BacktestComplete()
        return rows[max(0, end - limit):end].tolist()

    async def fetch_ticker(self, symbol: str):
        stamps, _, closes = self._arrays(symbol, "1m")
        end = self._cursor(stamps)
        if end <= 0:
            return {"last": float(closes[0])}
        if end >= len(stamps):
            raise BacktestComplete()
        return {"last": float(closes[end - 1])}

    async def close(self):
        return None


# ── Historical data ───────────────────────────────────────────────────────────

_KLINE_COLS = ["timestamp", "open", "high", "low", "close", "volume",
               "close_time", "quote_volume", "trades",
               "taker_base", "taker_quote", "ignore"]


def _read_dump(content: bytes) -> pd.DataFrame:
    """Parse one Binance kline archive (CSV inside a zip)."""
    import io
    import zipfile

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        with zf.open(zf.namelist()[0]) as fh:
            head = fh.readline()
            has_header = not head.split(b",")[0].strip().isdigit()
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        with zf.open(zf.namelist()[0]) as fh:
            df = pd.read_csv(fh, header=0 if has_header else None,
                             names=None if has_header else _KLINE_COLS)
    df.columns = _KLINE_COLS[:len(df.columns)]
    # Newer archives stamp microseconds; normalise everything to milliseconds.
    if len(df) and df["timestamp"].iloc[0] > 10**14:
        df["timestamp"] = df["timestamp"] // 1000
    return df[["timestamp", "open", "high", "low", "close", "volume"]]


def _fetch_dumps(symbol: str, days: int) -> pd.DataFrame | None:
    """Pull 1m candles from Binance's public data dumps.

    The trading API is geo-restricted in some regions (HTTP 451) while these
    static archives stay reachable — and they are the same exchange's data,
    so a backtest built on them matches where the bots actually trade.
    """
    import urllib.error
    import urllib.request

    market = symbol.replace("/", "")
    end = datetime.now(UTC).date()
    start = end - timedelta(days=days)

    urls: list[str] = []
    month = datetime(start.year, start.month, 1, tzinfo=UTC).date()
    while month <= end:
        # The current month has no monthly archive yet; fall back to dailies.
        if (month.year, month.month) == (end.year, end.month):
            day = max(month, start)
            while day < end:
                urls.append(f"https://data.binance.vision/data/spot/daily/klines/"
                            f"{market}/1m/{market}-1m-{day:%Y-%m-%d}.zip")
                day += timedelta(days=1)
        else:
            urls.append(f"https://data.binance.vision/data/spot/monthly/klines/"
                        f"{market}/1m/{market}-1m-{month:%Y-%m}.zip")
        month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)

    frames = []
    for i, url in enumerate(urls, 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                frames.append(_read_dump(resp.read()))
            print(f"\r  {symbol}: {i}/{len(urls)} archives...", end="", flush=True)
        except urllib.error.HTTPError as e:
            if e.code != 404:  # 404 just means that day/month isn't published
                print(f"\n  {symbol}: {url.rsplit('/', 1)[-1]} -> HTTP {e.code}")
        except Exception as e:  # noqa: BLE001
            print(f"\n  {symbol}: {type(e).__name__} on {url.rsplit('/', 1)[-1]}")

    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    cutoff = int(datetime.combine(start, datetime.min.time(), UTC).timestamp() * 1000)
    return df[df["timestamp"] >= cutoff].reset_index(drop=True)


async def fetch_history(symbols: list[str], days: int, use_cache: bool = True) -> dict[str, pd.DataFrame]:
    """Download (and cache) 1-minute candles; coarser timeframes are derived."""
    import ccxt.async_support as ccxt

    CACHE_DIR.mkdir(exist_ok=True)
    out: dict[str, pd.DataFrame] = {}
    exchange = ccxt.binance({"options": {"defaultType": "spot"}, "enableRateLimit": True})
    since_dt = datetime.now(UTC) - timedelta(days=days)

    try:
        for symbol in symbols:
            cache = CACHE_DIR / f"{symbol.replace('/', '')}_{days}d_1m.pkl"
            if use_cache and cache.exists():
                out[symbol] = pd.read_pickle(cache)
                print(f"  {symbol}: {len(out[symbol]):,} candles (cached)")
                continue

            # Prefer the public archives: they work from regions where the
            # trading API is blocked, and pull months in a handful of requests.
            dumped = _fetch_dumps(symbol, days)
            if dumped is not None and len(dumped):
                dumped = (dumped.drop_duplicates(subset="timestamp")
                          .sort_values("timestamp").reset_index(drop=True))
                dumped["dt"] = pd.to_datetime(dumped["timestamp"], unit="ms", utc=True)
                dumped.to_pickle(cache)
                out[symbol] = dumped
                print(f"\r  {symbol}: {len(dumped):,} candles (archives)      ")
                continue

            rows: list[list] = []
            since = int(since_dt.timestamp() * 1000)
            while True:
                batch = await exchange.fetch_ohlcv(symbol, "1m", since=since, limit=1000)
                if not batch:
                    break
                rows.extend(batch)
                since = batch[-1][0] + 60_000
                if since > datetime.now(UTC).timestamp() * 1000:
                    break
                print(f"\r  {symbol}: {len(rows):,} candles...", end="", flush=True)

            df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df = df.drop_duplicates(subset="timestamp").sort_values("timestamp").reset_index(drop=True)
            df["dt"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            df.to_pickle(cache)
            out[symbol] = df
            print(f"\r  {symbol}: {len(df):,} candles (downloaded)")
    finally:
        await exchange.close()

    return out


# ── Running one strategy ──────────────────────────────────────────────────────

async def run_strategy(stype: str, data: dict[str, pd.DataFrame],
                       starting_balance: float = 5000.0,
                       params: dict | None = None,
                       max_steps: int = 2_000_000) -> dict[str, Any]:
    """Replay one strategy over the loaded history and summarise the result.

    `params` overrides the strategy defaults, which is what the parameter
    optimiser varies between runs.
    """
    import importlib
    from unittest.mock import patch

    cls = STRATEGY_MAP[stype]
    config = {**DEFAULT_CONFIGS[stype], **(params or {})}
    config["initial_balance"] = starting_balance
    config["investment"] = starting_balance
    # Live bots poll every 5-10s. Replaying that over months would mean
    # millions of steps for no extra fidelity: the finest data available is
    # 1-minute candles, so step once per candle.
    config["poll_interval"] = max(int(config.get("poll_interval", 60)), 60)
    symbols = [s for s in config.get("symbols", list(data)) if s in data]
    if "trigger_symbol" in config:  # correlation strategy
        symbols = [s for s in data]
    config["symbols"] = symbols or list(data)

    # Start after a warm-up window so indicators (e.g. SMA-200 on 15m) are valid.
    first = min(df["dt"].iloc[0] for df in data.values())
    clock = Clock(first.to_pydatetime() + timedelta(days=3))

    exchange = ReplayExchange(data, clock)
    trades: list[dict] = []

    async def log(_bot_id, _message):
        return None

    async def record(_bot_id, _user_id, trade):
        net, fees = costs.net_pnl(trade["entry_price"], trade["exit_price"], trade["size"])
        if trade["reason"] == "MARK":
            net, fees = trade["pnl_usdt"], 0.0
        trades.append({**trade, "pnl_usdt": net, "fees_usdt": fees, "at": clock.dt})

    strategy = cls(bot_id=0, user_id=0, config=config,
                   exchange=exchange, log_fn=log, trade_fn=record)

    module = importlib.import_module(cls.__module__)
    patches = [patch.object(module, "asyncio", _AsyncioShim(clock))]
    if hasattr(module, "time"):
        patches.append(patch.object(module, "time", _TimeShim(clock)))

    for p in patches:
        p.start()
    try:
        await asyncio.wait_for(strategy.run(), timeout=300)
    except BacktestComplete:
        pass
    except (asyncio.TimeoutError, asyncio.CancelledError):
        pass
    except Exception as e:  # noqa: BLE001 — report, don't abort the whole run
        print(f"  ! {stype} aborted: {type(e).__name__}: {e}")
    finally:
        for p in patches:
            p.stop()

    pnls = [t["pnl_usdt"] for t in trades]
    summary = metrics.summarize(pnls, starting_balance)
    summary["strategy"] = stype
    summary["label"] = STRATEGY_LABELS[stype]
    summary["fees_paid"] = round(sum(t["fees_usdt"] for t in trades), 2)
    summary["params"] = dict(params or {})
    return summary


async def run_all(days: int = 30, symbols: list[str] | None = None,
                  starting_balance: float = 5000.0) -> list[dict]:
    symbols = symbols or ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
    print(f"Loading {days}d of 1m history for {', '.join(symbols)}")
    data = await fetch_history(symbols, days)

    span_start = min(df["dt"].iloc[0] for df in data.values())
    span_end = max(df["dt"].iloc[-1] for df in data.values())
    print(f"\nPeriod: {span_start:%Y-%m-%d} -> {span_end:%Y-%m-%d}")

    # How the market itself moved, for context.
    for symbol, df in data.items():
        change = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
        print(f"  {symbol} {change:+.1f}%")

    results = []
    print("\nReplaying strategies...")
    for stype in STRATEGY_MAP:
        summary = await run_strategy(stype, data, starting_balance)
        results.append(summary)
        print(f"  {STRATEGY_LABELS[stype]:<24} {summary['trades']:>5} trades  "
              f"{summary['return_pct']:>+7.2f}%")

    return sorted(results, key=lambda r: r["return_pct"], reverse=True)
