"""
Async Volatility Breakout Strategy (ATR range expansion)
---------------------------------------------------------
Entry:  price moves more than k x ATR above the session open (Larry Williams
        style range expansion) with above-average volume.
Exit:   ATR-scaled take profit / stop, or session timeout.

Personality: catches explosive expansion moves — exactly the regime the grid
bot hates. Trades rarely but decisively.
"""

import asyncio
import time
from datetime import datetime, UTC
from typing import Callable

from . import costs

import pandas as pd


class VolBreakStrategy:
    def __init__(self, bot_id: int, user_id: int, config: dict,
                 exchange, log_fn: Callable, trade_fn: Callable):
        self.bot_id = bot_id
        self.user_id = user_id
        self.exchange = exchange
        self.log = log_fn
        self.record_trade = trade_fn

        self.symbols: list[str] = config.get("symbols", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"])
        self.timeframe: str     = config.get("timeframe", "5m")
        self.candles: int       = config.get("candles", 200)

        self.atr_period: int       = config.get("atr_period", 14)
        self.breakout_mult: float  = config.get("breakout_mult", 1.2)   # k x ATR above open
        self.lookback_bars: int    = config.get("lookback_bars", 12)    # "session" window
        self.vol_mult: float       = config.get("volume_multiplier", 1.3)

        self.tp_atr_mult: float    = config.get("tp_atr_mult", 1.5)
        self.sl_atr_mult: float    = config.get("sl_atr_mult", 1.0)
        self.timeout_seconds: int  = config.get("trade_timeout_seconds", 3600)
        self.trade_size_pct: float = config.get("trade_size_pct", 0.25)
        self.poll_interval: int    = config.get("poll_interval", 20)

        self.balance: float = config.get("initial_balance", 5000.0)
        self.positions: dict = {}

    async def _fetch_df(self, symbol: str) -> pd.DataFrame:
        ohlcv = await self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=self.candles)
        return pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])

    def _atr(self, df: pd.DataFrame) -> float:
        high, low, close = df["high"], df["low"], df["close"]
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)
        return float(tr.ewm(com=self.atr_period - 1, adjust=False).mean().iloc[-2])

    async def _close(self, symbol: str, price: float, reason: str) -> None:
        pos = self.positions.pop(symbol)
        proceeds = pos["size"] * price
        pnl = proceeds - pos["size"] * pos["entry_price"]
        self.balance += proceeds
        await self.log(self.bot_id,
            f"[VOLBREAK] EXIT {symbol} @ ${price:,.4f} | {reason} | PnL: ${pnl:+.2f}")
        await self.record_trade(self.bot_id, self.user_id, {
            "symbol": symbol,
            "entry_price": pos["entry_price"],
            "exit_price": price,
            "size": pos["size"],
            "pnl_usdt": round(pnl, 4),
            "pnl_pct": round((price - pos["entry_price"]) / pos["entry_price"] * 100, 4),
            "reason": reason,
            "entry_time": pos["entry_time"],
        })

    async def run(self) -> None:
        await self.log(self.bot_id,
            f"[VOLBREAK] Started | Pairs: {', '.join(self.symbols)} | {self.timeframe} | "
            f"entry > open + {self.breakout_mult}xATR over {self.lookback_bars} bars")

        while True:
            now = time.time()
            for symbol in self.symbols:
                try:
                    df = await self._fetch_df(symbol)
                    if len(df) < max(self.atr_period, self.lookback_bars) + 3:
                        continue

                    atr = self._atr(df)
                    session_open = float(df["open"].iloc[-(self.lookback_bars + 1)])
                    trigger = session_open + self.breakout_mult * atr
                    vol_avg = float(df["volume"].iloc[-(self.lookback_bars + 1):-1].mean())
                    last_vol = float(df["volume"].iloc[-2])

                    ticker = await self.exchange.fetch_ticker(symbol)
                    price = float(ticker["last"])

                    pos = self.positions.get(symbol)
                    if pos:
                        if price <= pos["stop_loss"]:
                            await self._close(symbol, price, "STOP_LOSS")
                        elif price >= pos["target"]:
                            await self._close(symbol, price, "TAKE_PROFIT")
                        elif now - pos["entry_time_ts"] >= self.timeout_seconds:
                            await self._close(symbol, price, "TIMEOUT")
                    else:
                        vol_ok = vol_avg > 0 and last_vol >= vol_avg * self.vol_mult
                        if price > trigger and vol_ok and atr > 0 and self.balance > 10:
                            spend = self.balance * self.trade_size_pct
                            size = spend / price
                            self.balance -= spend
                            self.positions[symbol] = {
                                "size": size,
                                "entry_price": price,
                                "entry_time": datetime.now(UTC),
                                "entry_time_ts": now,
                                "stop_loss": price - atr * self.sl_atr_mult,
                                "target": max(price + atr * self.tp_atr_mult,
                                              price * (1 + costs.min_profit_pct())),
                            }
                            await self.log(self.bot_id,
                                f"[VOLBREAK] BUY {symbol} @ ${price:,.4f} | trigger ${trigger:,.4f} "
                                f"ATR ${atr:,.4f} | TP ${self.positions[symbol]['target']:,.4f}")
                        else:
                            await self.log(self.bot_id,
                                f"[VOLBREAK] {symbol} ${price:,.4f} | trigger ${trigger:,.4f} volOK={vol_ok}")
                except Exception as e:  # noqa: BLE001
                    await self.log(self.bot_id, f"[VOLBREAK] Error {symbol}: {e}")

            await asyncio.sleep(self.poll_interval)
