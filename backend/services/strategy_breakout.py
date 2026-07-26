"""
Async Donchian Breakout Strategy (trend-following)
--------------------------------------------------
Entry:  price breaks above the highest high of the last N closed 1h candles
        (classic "turtle" breakout). One position per symbol.
Exit:   trailing stop (ATR-scaled), hard stop, or break below the M-period low.

Personality: few trades, small losses, occasional big trending winners —
the philosophical opposite of the grid bot.
"""

import asyncio
import time
from datetime import datetime, UTC
from typing import Callable

from . import costs

import pandas as pd


class BreakoutStrategy:
    def __init__(self, bot_id: int, user_id: int, config: dict,
                 exchange, log_fn: Callable, trade_fn: Callable):
        self.bot_id = bot_id
        self.user_id = user_id
        self.exchange = exchange
        self.log = log_fn
        self.record_trade = trade_fn

        self.symbols: list[str] = config.get("symbols", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"])
        self.timeframe: str     = config.get("timeframe", "1h")
        self.candles: int       = config.get("candles", 120)

        self.entry_lookback: int = config.get("entry_lookback", 20)   # break of 20-bar high
        self.exit_lookback: int  = config.get("exit_lookback", 10)    # break of 10-bar low
        self.atr_period: int     = config.get("atr_period", 14)
        self.atr_trail_mult: float = config.get("atr_trail_mult", 2.5)
        self.stop_loss_pct: float  = config.get("stop_loss_pct", 0.02)   # 2% disaster stop
        self.trade_size_pct: float = config.get("trade_size_pct", 0.25)
        self.poll_interval: int    = config.get("poll_interval", 60)

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
        pnl = costs.net_pnl(pos["entry_price"], price, pos["size"])[0]
        self.balance += costs.net_proceeds(pos["entry_price"], price, pos["size"])
        await self.log(self.bot_id,
            f"[BREAKOUT] EXIT {symbol} @ ${price:,.4f} | {reason} | PnL: ${pnl:+.2f}")
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
            f"[BREAKOUT] Started | Pairs: {', '.join(self.symbols)} | "
            f"{self.timeframe} Donchian {self.entry_lookback}-high entry / "
            f"{self.exit_lookback}-low exit | ATR trail x{self.atr_trail_mult}")

        while True:
            for symbol in self.symbols:
                try:
                    df = await self._fetch_df(symbol)
                    if len(df) < max(self.entry_lookback, self.exit_lookback, self.atr_period) + 3:
                        continue
                    ticker = await self.exchange.fetch_ticker(symbol)
                    price = float(ticker["last"])
                    # Channels computed on CLOSED candles only (exclude the forming one)
                    entry_high = float(df["high"].iloc[-(self.entry_lookback + 1):-1].max())
                    exit_low   = float(df["low"].iloc[-(self.exit_lookback + 1):-1].min())
                    atr = self._atr(df)

                    pos = self.positions.get(symbol)
                    if pos:
                        # Ratchet the ATR trailing stop up as price advances
                        trail = price - atr * self.atr_trail_mult
                        if trail > pos["stop_loss"]:
                            pos["stop_loss"] = trail
                        if price <= pos["stop_loss"]:
                            # Risk control — always honoured, never deferred.
                            await self._close(symbol, price, "STOP_LOSS")
                        elif price < exit_low and not costs.in_dead_zone(pos["entry_price"], price):
                            # Trend-reversal exit, but not for a gain too small
                            # to cover the round trip.
                            await self._close(symbol, price, "CHANNEL_EXIT")
                    else:
                        # A trailing stop tighter than the round trip means the
                        # exit cannot clear its own costs — skip such setups.
                        trail_pct = (atr * self.atr_trail_mult) / price if price else 0
                        if trail_pct < costs.ROUND_TRIP_PCT:
                            await self.log(self.bot_id,
                                f"[BREAKOUT] {symbol} skipped — ATR trail {trail_pct*100:.3f}% "
                                f"below round-trip cost {costs.ROUND_TRIP_PCT*100:.2f}%")
                        elif price > entry_high and self.balance > 10:
                            spend = self.balance * self.trade_size_pct
                            size = spend / price
                            self.balance -= spend
                            self.positions[symbol] = {
                                "size": size,
                                "entry_price": price,
                                "entry_time": datetime.now(UTC),
                                "stop_loss": max(price * (1 - self.stop_loss_pct),
                                                 price - atr * self.atr_trail_mult),
                            }
                            await self.log(self.bot_id,
                                f"[BREAKOUT] BUY {symbol} @ ${price:,.4f} | broke {self.entry_lookback}-bar high "
                                f"${entry_high:,.4f} | SL ${self.positions[symbol]['stop_loss']:,.4f}")
                        else:
                            await self.log(self.bot_id,
                                f"[BREAKOUT] {symbol} ${price:,.4f} | high to beat ${entry_high:,.4f}")
                except Exception as e:  # noqa: BLE001 — keep scanning other symbols
                    await self.log(self.bot_id, f"[BREAKOUT] Error {symbol}: {e}")

            await asyncio.sleep(self.poll_interval)
