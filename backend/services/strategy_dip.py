"""
Async Mean-Reversion Dip Buyer (RSI-2 / Bollinger)
---------------------------------------------------
Entry:  long-term uptrend (close > SMA-200 on the trading timeframe)
        AND RSI(2) < oversold threshold
        AND price below the lower Bollinger band
Exit:   price reverts to the SMA-20 mid band (take profit), hard stop, or timeout.

Personality: high win rate, small-to-moderate wins, occasional larger loss.
Complements the breakout bot, which is the inverse profile.
"""

import asyncio
import time
from datetime import datetime, UTC
from typing import Callable

from . import costs

import pandas as pd


class DipStrategy:
    def __init__(self, bot_id: int, user_id: int, config: dict,
                 exchange, log_fn: Callable, trade_fn: Callable):
        self.bot_id = bot_id
        self.user_id = user_id
        self.exchange = exchange
        self.log = log_fn
        self.record_trade = trade_fn

        self.symbols: list[str] = config.get("symbols", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"])
        self.timeframe: str     = config.get("timeframe", "15m")
        self.candles: int       = config.get("candles", 250)

        self.trend_sma: int       = config.get("trend_sma_period", 200)
        self.rsi_period: int      = config.get("rsi_period", 2)
        self.rsi_oversold: float  = config.get("rsi_oversold", 10)
        self.bb_period: int       = config.get("bb_period", 20)
        self.bb_std: float        = config.get("bb_std", 2.0)

        self.stop_loss_pct: float  = config.get("stop_loss_pct", 0.015)
        self.timeout_seconds: int  = config.get("trade_timeout_seconds", 14400)  # 4h
        self.trade_size_pct: float = config.get("trade_size_pct", 0.25)
        self.poll_interval: int    = config.get("poll_interval", 30)

        self.balance: float = config.get("initial_balance", 5000.0)
        self.positions: dict = {}

    def _rsi(self, series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, float("inf"))
        return 100 - (100 / (1 + rs))

    async def _fetch_df(self, symbol: str) -> pd.DataFrame:
        ohlcv = await self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=self.candles)
        return pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])

    async def _close(self, symbol: str, price: float, reason: str) -> None:
        pos = self.positions.pop(symbol)
        pnl = costs.net_pnl(pos["entry_price"], price, pos["size"])[0]
        self.balance += costs.net_proceeds(pos["entry_price"], price, pos["size"])
        await self.log(self.bot_id,
            f"[DIP] EXIT {symbol} @ ${price:,.4f} | {reason} | PnL: ${pnl:+.2f}")
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
            f"[DIP] Started | Pairs: {', '.join(self.symbols)} | {self.timeframe} | "
            f"buy RSI({self.rsi_period})<{self.rsi_oversold} below lower BB, above SMA-{self.trend_sma}")

        while True:
            now = time.time()
            for symbol in self.symbols:
                try:
                    df = await self._fetch_df(symbol)
                    if len(df) < self.trend_sma + 3:
                        await self.log(self.bot_id, f"[DIP] {symbol}: warming up ({len(df)} candles)")
                        continue

                    close = df["close"]
                    sma_trend = close.rolling(self.trend_sma).mean().iloc[-2]
                    mid = close.rolling(self.bb_period).mean()
                    std = close.rolling(self.bb_period).std()
                    lower_band = (mid - self.bb_std * std).iloc[-2]
                    mid_band = float(mid.iloc[-2])
                    rsi = float(self._rsi(close, self.rsi_period).iloc[-2])
                    prev_close = float(close.iloc[-2])

                    ticker = await self.exchange.fetch_ticker(symbol)
                    price = float(ticker["last"])

                    pos = self.positions.get(symbol)
                    if pos:
                        if price <= pos["stop_loss"]:
                            await self._close(symbol, price, "STOP_LOSS")
                        elif price >= pos["target"]:
                            await self._close(symbol, price, "TAKE_PROFIT")
                        elif (now - pos["entry_time_ts"] >= self.timeout_seconds
                              and not costs.in_dead_zone(pos["entry_price"], price)):
                            await self._close(symbol, price, "TIMEOUT")
                    else:
                        uptrend = prev_close > sma_trend
                        oversold = rsi < self.rsi_oversold
                        below_band = prev_close < lower_band
                        if uptrend and oversold and below_band and self.balance > 10:
                            spend = self.balance * self.trade_size_pct
                            size = spend / price
                            self.balance -= spend
                            self.positions[symbol] = {
                                "size": size,
                                "entry_price": price,
                                "entry_time": datetime.now(UTC),
                                "entry_time_ts": now,
                                "stop_loss": price * (1 - self.stop_loss_pct),
                                # Revert to the mean, but never aim below break-even.
                                "target": max(mid_band, price * (1 + costs.min_profit_pct())),
                            }
                            await self.log(self.bot_id,
                                f"[DIP] BUY {symbol} @ ${price:,.4f} | RSI={rsi:.1f} "
                                f"| target ${self.positions[symbol]['target']:,.4f}")
                        else:
                            await self.log(self.bot_id,
                                f"[DIP] {symbol} ${price:,.4f} | RSI={rsi:.1f} "
                                f"uptrend={uptrend} belowBB={below_band}")
                except Exception as e:  # noqa: BLE001
                    await self.log(self.bot_id, f"[DIP] Error {symbol}: {e}")

            await asyncio.sleep(self.poll_interval)
