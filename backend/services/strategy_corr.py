"""
Async Correlation Strategy — adapted from crypto-trading-bot/corr_bot.py
"""

import asyncio
from collections import deque
from datetime import datetime, UTC
from typing import Callable


class CorrStrategy:
    def __init__(self, bot_id: int, user_id: int, config: dict,
                 exchange, log_fn: Callable, trade_fn: Callable):
        self.bot_id = bot_id
        self.user_id = user_id
        self.cfg = config
        self.exchange = exchange
        self.log = log_fn
        self.record_trade = trade_fn

        self.trigger: str = config.get("trigger_symbol", "BTC/USDT")
        self.alts: list[str] = config.get("alt_symbols", ["ETH/USDT", "BNB/USDT", "SOL/USDT"])
        self.threshold: float = config.get("btc_move_threshold", 0.0035)
        self.window: int = config.get("btc_window_seconds", 20)
        self.take_profit: float = config.get("take_profit_pct", 0.006)
        self.stop_loss: float = config.get("stop_loss_pct", 0.003)
        self.timeout: int = config.get("trade_timeout_seconds", 180)
        self.trade_size_pct: float = config.get("trade_size_pct", 0.25)
        self.poll_interval: int = config.get("poll_interval", 5)

        self.balance: float = config.get("initial_balance", 5000.0)
        self.positions: dict[str, dict] = {}
        self.btc_history: deque = deque()

    async def run(self) -> None:
        await self.log(self.bot_id,
            f"[CORR] Started | Trigger: {self.trigger} >{self.threshold*100:.2f}% in {self.window}s")

        while True:
            now = asyncio.get_event_loop().time()
            try:
                # Update BTC history
                ticker = await self.exchange.fetch_ticker(self.trigger)
                btc_price = ticker["last"]
                self.btc_history.append((now, btc_price))
                while self.btc_history and self.btc_history[0][0] < now - self.window:
                    self.btc_history.popleft()

                # Check exits
                for symbol in list(self.positions.keys()):
                    pos = self.positions[symbol]
                    t = await self.exchange.fetch_ticker(symbol)
                    price = t["last"]
                    entry = pos["entry_price"]
                    pnl_pct = (price - entry) / entry
                    elapsed = now - pos["entry_time"]

                    reason = None
                    if pnl_pct >= self.take_profit:
                        reason = "TAKE_PROFIT"
                    elif pnl_pct <= -self.stop_loss:
                        reason = "STOP_LOSS"
                    elif elapsed >= self.timeout:
                        reason = "TIMEOUT"

                    if reason:
                        proceeds = pos["size"] * price
                        self.balance += proceeds
                        pnl = proceeds - pos["size"] * entry
                        del self.positions[symbol]
                        await self.log(self.bot_id,
                            f"[CORR] SELL {symbol} @ ${price:,.4f} | {reason} | PnL: ${pnl:+.2f}")
                        await self.record_trade(self.bot_id, self.user_id, {
                            "symbol": symbol, "entry_price": entry, "exit_price": price,
                            "size": pos["size"], "pnl_usdt": round(pnl, 4),
                            "pnl_pct": round(pnl_pct * 100, 4), "reason": reason,
                            "entry_time": pos["entry_time_dt"],
                        })

                # Detect BTC move and enter
                if len(self.btc_history) >= 2:
                    oldest = self.btc_history[0][1]
                    move = (btc_price - oldest) / oldest

                    if move >= self.threshold:
                        for symbol in self.alts:
                            if symbol not in self.positions and self.balance > 10:
                                t = await self.exchange.fetch_ticker(symbol)
                                alt_price = t["last"]
                                spend = self.balance * self.trade_size_pct
                                size = spend / alt_price
                                self.balance -= spend
                                self.positions[symbol] = {
                                    "size": size,
                                    "entry_price": alt_price,
                                    "entry_time": now,
                                    "entry_time_dt": datetime.now(UTC),
                                }
                                await self.log(self.bot_id,
                                    f"[CORR] BUY  {symbol} @ ${alt_price:,.4f} "
                                    f"| BTC +{move*100:.3f}% | Spent: ${spend:,.2f}")

            except Exception as e:
                await self.log(self.bot_id, f"[CORR] Error: {e}")

            await asyncio.sleep(self.poll_interval)
