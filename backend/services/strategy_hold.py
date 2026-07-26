"""
Buy & Hold Benchmark ("do nothing" control)
--------------------------------------------
Buys an equal-weight basket once, then simply holds it forever.

This is not a strategy to compete with — it is the control every other bot
must beat to justify existing. If an active strategy cannot outperform
buying the basket and sitting on your hands, the trading is destroying value.

Because the dashboard aggregates *closed* trades, the held position is
marked to market on an interval: each MARK row books the P&L accrued since
the previous mark, so the running total always equals the true buy & hold
return. MARK rows are exempt from round-trip fees in bot_runner (no trade
actually happened); the one-time entry cost is charged on the first mark.
"""

import asyncio
from datetime import datetime, UTC
from typing import Callable

from . import costs


class HoldStrategy:
    def __init__(self, bot_id: int, user_id: int, config: dict,
                 exchange, log_fn: Callable, trade_fn: Callable):
        self.bot_id = bot_id
        self.user_id = user_id
        self.exchange = exchange
        self.log = log_fn
        self.record_trade = trade_fn

        self.symbols: list[str] = config.get("symbols", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"])
        self.mark_interval: int = config.get("mark_interval_seconds", 900)  # 15m
        self.poll_interval: int = config.get("poll_interval", 60)

        self.balance: float = config.get("initial_balance", 5000.0)
        self.holdings: dict[str, dict] = {}   # symbol -> {size, entry_price, last_mark, entry_time}
        self._entry_cost_charged = False

    async def _buy_basket(self) -> None:
        per_symbol = self.balance / len(self.symbols)
        for symbol in self.symbols:
            try:
                ticker = await self.exchange.fetch_ticker(symbol)
                price = float(ticker["last"])
                size = per_symbol / price
                self.holdings[symbol] = {
                    "size": size,
                    "entry_price": price,
                    "last_mark": price,
                    "entry_time": datetime.now(UTC),
                }
                await self.log(self.bot_id,
                    f"[HOLD] BUY {symbol} @ ${price:,.4f} | ${per_symbol:,.2f} allocated")
            except Exception as e:  # noqa: BLE001
                await self.log(self.bot_id, f"[HOLD] Could not buy {symbol}: {e}")

    async def run(self) -> None:
        await self.log(self.bot_id,
            f"[HOLD] Benchmark started | equal-weight {', '.join(self.symbols)} | "
            f"marked to market every {self.mark_interval // 60}m")

        loop = asyncio.get_running_loop()
        last_mark = loop.time()

        while True:
            try:
                if not self.holdings:
                    await self._buy_basket()
                    last_mark = loop.time()

                elif loop.time() - last_mark >= self.mark_interval:
                    last_mark = loop.time()
                    total = 0.0
                    for symbol, h in self.holdings.items():
                        try:
                            ticker = await self.exchange.fetch_ticker(symbol)
                            price = float(ticker["last"])
                            delta = h["size"] * (price - h["last_mark"])

                            # Charge the real one-time cost of entering the basket
                            # on the first mark so the benchmark isn't flattered.
                            if not self._entry_cost_charged:
                                delta -= h["size"] * h["entry_price"] * (
                                    costs.settings.TRADING_FEE_RATE + costs.settings.SLIPPAGE_RATE
                                )

                            await self.record_trade(self.bot_id, self.user_id, {
                                "symbol": symbol,
                                "entry_price": h["last_mark"],
                                "exit_price": price,
                                "size": h["size"],
                                "pnl_usdt": round(delta, 6),
                                "pnl_pct": round((price - h["last_mark"]) / h["last_mark"] * 100, 4),
                                "reason": "MARK",
                                "entry_time": h["entry_time"],
                            })
                            h["last_mark"] = price
                            total += h["size"] * price
                        except Exception as e:  # noqa: BLE001
                            await self.log(self.bot_id, f"[HOLD] Mark error {symbol}: {e}")

                    self._entry_cost_charged = True
                    await self.log(self.bot_id, f"[HOLD] Basket marked to market | value ${total:,.2f}")
            except Exception as e:  # noqa: BLE001
                await self.log(self.bot_id, f"[HOLD] Error: {e}")

            await asyncio.sleep(self.poll_interval)
