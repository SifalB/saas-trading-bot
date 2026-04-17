"""
Async Scalping Strategy — RSI + EMA, adapted from crypto-trading-bot/strategy.py
"""

import asyncio
from datetime import datetime, UTC
from typing import Callable

import pandas as pd
import ta


class ScalpStrategy:
    def __init__(self, bot_id: int, user_id: int, config: dict,
                 exchange, log_fn: Callable, trade_fn: Callable):
        self.bot_id = bot_id
        self.user_id = user_id
        self.cfg = config
        self.exchange = exchange
        self.log = log_fn
        self.record_trade = trade_fn

        self.symbols: list[str] = config.get("symbols", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"])
        self.timeframe: str = config.get("timeframe", "1m")
        self.rsi_period: int = config.get("rsi_period", 14)
        self.rsi_buy: float = config.get("rsi_buy", 50)
        self.rsi_sell: float = config.get("rsi_sell", 62)
        self.ema_period: int = config.get("ema_period", 20)
        self.take_profit: float = config.get("take_profit_pct", 0.005)
        self.stop_loss: float = config.get("stop_loss_pct", 0.003)
        self.trade_size_pct: float = config.get("trade_size_pct", 0.45)
        self.poll_interval: int = config.get("poll_interval", 10)

        self.balance: float = config.get("initial_balance", 5000.0)
        self.positions: dict[str, dict] = {}

    async def _fetch_df(self, symbol: str) -> pd.DataFrame:
        ohlcv = await self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=self.rsi_period).rsi()
        df["ema"] = ta.trend.EMAIndicator(df["close"], window=self.ema_period).ema_indicator()
        return df

    def _signal(self, df: pd.DataFrame) -> str:
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]
        rsi_crossed_up = prev2["rsi"] < self.rsi_buy <= prev["rsi"]
        above_ema = prev["close"] > prev["ema"]
        if rsi_crossed_up and above_ema:
            return "BUY"
        if prev["rsi"] >= self.rsi_sell:
            return "SELL"
        return "HOLD"

    async def run(self) -> None:
        await self.log(self.bot_id, f"[SCALP] Started | Pairs: {', '.join(self.symbols)}")

        while True:
            for symbol in self.symbols:
                try:
                    df = await self._fetch_df(symbol)
                    ticker = await self.exchange.fetch_ticker(symbol)
                    price = ticker["last"]

                    # Check TP / SL
                    if symbol in self.positions:
                        entry = self.positions[symbol]["entry_price"]
                        pnl_pct = (price - entry) / entry
                        reason = None
                        if pnl_pct >= self.take_profit:
                            reason = "TAKE_PROFIT"
                        elif pnl_pct <= -self.stop_loss:
                            reason = "STOP_LOSS"
                        if reason:
                            pos = self.positions.pop(symbol)
                            proceeds = pos["size"] * price
                            self.balance += proceeds
                            pnl = proceeds - pos["size"] * entry
                            await self.log(self.bot_id,
                                f"[SCALP] SELL {symbol} @ ${price:,.4f} | {reason} | PnL: ${pnl:+.2f}")
                            await self.record_trade(self.bot_id, self.user_id, {
                                "symbol": symbol, "entry_price": entry, "exit_price": price,
                                "size": pos["size"], "pnl_usdt": round(pnl, 4),
                                "pnl_pct": round(pnl_pct * 100, 4), "reason": reason,
                                "entry_time": pos["entry_time"],
                            })
                            continue

                    signal = self._signal(df)
                    if signal == "BUY" and symbol not in self.positions and self.balance > 10:
                        spend = self.balance * self.trade_size_pct
                        size = spend / price
                        self.balance -= spend
                        self.positions[symbol] = {"size": size, "entry_price": price, "entry_time": datetime.now(UTC)}
                        await self.log(self.bot_id,
                            f"[SCALP] BUY  {symbol} @ ${price:,.4f} | Spent: ${spend:,.2f}")

                    elif signal == "SELL" and symbol in self.positions:
                        pos = self.positions.pop(symbol)
                        entry = pos["entry_price"]
                        proceeds = pos["size"] * price
                        self.balance += proceeds
                        pnl = proceeds - pos["size"] * entry
                        pnl_pct = pnl / (pos["size"] * entry)
                        await self.log(self.bot_id,
                            f"[SCALP] SELL {symbol} @ ${price:,.4f} | SIGNAL | PnL: ${pnl:+.2f}")
                        await self.record_trade(self.bot_id, self.user_id, {
                            "symbol": symbol, "entry_price": entry, "exit_price": price,
                            "size": pos["size"], "pnl_usdt": round(pnl, 4),
                            "pnl_pct": round(pnl_pct * 100, 4), "reason": "SIGNAL",
                            "entry_time": pos["entry_time"],
                        })

                except Exception as e:
                    await self.log(self.bot_id, f"[SCALP] Error on {symbol}: {e}")

            await asyncio.sleep(self.poll_interval)
