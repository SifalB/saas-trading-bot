"""
Async Multi-Timeframe Confluence Strategy
------------------------------------------
15m  price > EMA-50          → confirmed uptrend
5m   RSI 52-70 + MACD > 0   → momentum building, not overbought
1m   RSI crosses 50 + price > EMA-20 + volume spike → precise entry

Risk management:
  SL: 0.25%  |  TP: 0.40%  |  Breakeven at +0.15%  |  Timeout: 5 min
"""

import asyncio
import time
from datetime import datetime, UTC
from typing import Callable

from . import costs

import pandas as pd


class MtfStrategy:
    def __init__(self, bot_id: int, user_id: int, config: dict,
                 exchange, log_fn: Callable, trade_fn: Callable):
        self.bot_id = bot_id
        self.user_id = user_id
        self.exchange = exchange
        self.log = log_fn
        self.record_trade = trade_fn

        self.symbols: list[str]  = config.get("symbols", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"])
        self.tf_slow: str        = config.get("tf_slow", "15m")
        self.tf_mid: str         = config.get("tf_mid", "5m")
        self.tf_fast: str        = config.get("tf_fast", "1m")
        self.candles: int        = config.get("candles", 100)

        self.ema_trend: int      = config.get("ema_trend_period", 50)
        self.ema_entry: int      = config.get("ema_entry_period", 20)
        self.rsi_period: int     = config.get("rsi_period", 14)
        self.rsi_mid_low: float  = config.get("rsi_mid_low", 52)
        self.rsi_mid_high: float = config.get("rsi_mid_high", 70)
        self.macd_fast: int      = config.get("macd_fast", 12)
        self.macd_slow: int      = config.get("macd_slow", 26)
        self.macd_signal: int    = config.get("macd_signal", 9)
        self.vol_mult: float     = config.get("volume_multiplier", 1.5)

        self.stop_loss_pct: float       = config.get("stop_loss_pct", 0.0025)
        self.take_profit_pct: float     = costs.viable_tp(
            config.get("take_profit_pct", 0.004), config.get("stop_loss_pct", 0.0025))
        self.breakeven_trigger: float   = config.get("breakeven_trigger_pct", 0.0015)
        self.breakeven_buffer: float    = config.get("breakeven_buffer_pct", 0.0005)
        self.timeout_seconds: int       = config.get("trade_timeout_seconds", 300)
        self.trade_size_pct: float      = config.get("trade_size_pct", 0.30)
        self.poll_interval: int         = config.get("poll_interval", 10)

        self.balance: float             = config.get("initial_balance", 5000.0)
        self.positions: dict            = {}

    # ── Indicator helpers ──────────────────────────────────────────────────────

    def _ema(self, series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    def _rsi(self, series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, float("inf"))
        return 100 - (100 / (1 + rs))

    def _macd_hist(self, series: pd.Series) -> pd.Series:
        ema_fast = series.ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = series.ewm(span=self.macd_slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        return macd_line - signal_line

    async def _fetch_df(self, symbol: str, timeframe: str) -> pd.DataFrame:
        ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=self.candles)
        return pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])

    # ── Signal logic ───────────────────────────────────────────────────────────

    def _get_signal(self, df_15m: pd.DataFrame, df_5m: pd.DataFrame,
                    df_1m: pd.DataFrame) -> tuple[str, str]:
        # 15m trend: price > EMA-50
        if len(df_15m) < self.ema_trend + 2:
            return "HOLD", "not enough 15m candles"
        ema50 = self._ema(df_15m["close"], self.ema_trend)
        if df_15m["close"].iloc[-2] <= ema50.iloc[-2]:
            return "HOLD", "BEAR trend on 15m"

        # 5m momentum: RSI 52-70 AND MACD hist > 0
        if len(df_5m) < self.macd_slow + 2:
            return "HOLD", "not enough 5m candles"
        rsi_5m = self._rsi(df_5m["close"], self.rsi_period).iloc[-2]
        hist_5m = self._macd_hist(df_5m["close"]).iloc[-2]
        if not (self.rsi_mid_low <= rsi_5m <= self.rsi_mid_high and hist_5m > 0):
            return "HOLD", f"5m RSI={rsi_5m:.1f} MACD_h={hist_5m:.4f}"

        # 1m entry: RSI crosses 50 + above EMA-20 + volume spike
        if len(df_1m) < self.ema_entry + 3:
            return "HOLD", "not enough 1m candles"
        rsi_1m = self._rsi(df_1m["close"], self.rsi_period)
        ema20 = self._ema(df_1m["close"], self.ema_entry)
        rsi_cross = rsi_1m.iloc[-3] < 50 <= rsi_1m.iloc[-2]
        above_ema = df_1m["close"].iloc[-2] > ema20.iloc[-2]
        vol_avg = df_1m["volume"].iloc[-22:-2].mean()
        vol_spike = vol_avg > 0 and df_1m["volume"].iloc[-2] >= vol_avg * self.vol_mult
        if not (rsi_cross and above_ema and vol_spike):
            return "HOLD", f"1m cross={rsi_cross} ema={above_ema} vol={vol_spike}"

        return "BUY", "ALL conditions met"

    # ── Main loop ──────────────────────────────────────────────────────────────

    async def run(self) -> None:
        await self.log(self.bot_id,
            f"[MTF] Started | Pairs: {', '.join(self.symbols)} | "
            f"TF: {self.tf_slow}/{self.tf_mid}/{self.tf_fast} | "
            f"TP: {self.take_profit_pct*100:.2f}% SL: {self.stop_loss_pct*100:.2f}%")

        while True:
            now = time.time()

            # ── Exit checks ────────────────────────────────────────────────────
            for symbol in list(self.positions.keys()):
                pos = self.positions[symbol]
                try:
                    ticker = await self.exchange.fetch_ticker(symbol)
                    price = float(ticker["last"])
                    entry = pos["entry_price"]
                    pnl_pct = (price - entry) / entry
                    elapsed = now - pos["entry_time_ts"]

                    # Move to breakeven
                    if not pos["breakeven_set"] and pnl_pct >= self.breakeven_trigger:
                        pos["stop_loss"] = entry * (1 + self.breakeven_buffer)
                        pos["breakeven_set"] = True
                        await self.log(self.bot_id,
                            f"[MTF] BE {symbol} — SL moved to ${pos['stop_loss']:,.4f}")

                    reason = None
                    if price <= pos["stop_loss"]:
                        reason = "STOP_LOSS"
                    elif pnl_pct >= self.take_profit_pct:
                        reason = "TAKE_PROFIT"
                    # Don't book a guaranteed loss: wait out the dead zone
                    # where the gain is real but too small to cover costs.
                    elif elapsed >= self.timeout_seconds and not costs.in_dead_zone(entry, price):
                        reason = "TIMEOUT"

                    if reason:
                        pnl = costs.net_pnl(entry, price, pos["size"])[0]
                        self.balance += costs.net_proceeds(entry, price, pos["size"])
                        del self.positions[symbol]
                        await self.log(self.bot_id,
                            f"[MTF] EXIT {symbol} @ ${price:,.4f} | {reason} | PnL: ${pnl:+.2f}")
                        await self.record_trade(self.bot_id, self.user_id, {
                            "symbol": symbol,
                            "entry_price": entry,
                            "exit_price": price,
                            "size": pos["size"],
                            "pnl_usdt": round(pnl, 4),
                            "pnl_pct": round(pnl_pct * 100, 4),
                            "reason": reason,
                            "entry_time": pos["entry_time"],
                        })
                except Exception as e:
                    await self.log(self.bot_id, f"[MTF] Exit error {symbol}: {e}")

            # ── Entry checks ───────────────────────────────────────────────────
            for symbol in self.symbols:
                if symbol in self.positions:
                    continue
                try:
                    df_15m = await self._fetch_df(symbol, self.tf_slow)
                    df_5m  = await self._fetch_df(symbol, self.tf_mid)
                    df_1m  = await self._fetch_df(symbol, self.tf_fast)
                    signal, reason = self._get_signal(df_15m, df_5m, df_1m)

                    ticker = await self.exchange.fetch_ticker(symbol)
                    price = float(ticker["last"])

                    await self.log(self.bot_id, f"[MTF] {symbol} ${price:,.4f} | {reason}")

                    if signal == "BUY" and self.balance > 10:
                        spend = self.balance * self.trade_size_pct
                        size = spend / price
                        self.balance -= spend
                        entry_time = datetime.now(UTC)
                        self.positions[symbol] = {
                            "size": size,
                            "entry_price": price,
                            "entry_time": entry_time,
                            "entry_time_ts": now,
                            "stop_loss": price * (1 - self.stop_loss_pct),
                            "breakeven_set": False,
                        }
                        await self.log(self.bot_id,
                            f"[MTF] BUY {symbol} @ ${price:,.4f} | "
                            f"Spent: ${spend:,.2f} | SL: ${self.positions[symbol]['stop_loss']:,.4f}")
                except Exception as e:
                    await self.log(self.bot_id, f"[MTF] Entry error {symbol}: {e}")

            await asyncio.sleep(self.poll_interval)
