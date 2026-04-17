"""
Async Grid Strategy — adapted from crypto-trading-bot/grid_trader.py
"""

import asyncio
from datetime import datetime, UTC
from typing import Callable


class GridStrategy:
    def __init__(self, bot_id: int, user_id: int, config: dict,
                 exchange, log_fn: Callable, trade_fn: Callable):
        self.bot_id = bot_id
        self.user_id = user_id
        self.cfg = config
        self.exchange = exchange
        self.log = log_fn
        self.record_trade = trade_fn

        self.symbols: list[str] = config.get("symbols", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"])
        self.levels: int = config.get("levels", 7)
        self.range_pct: float = config.get("range_pct", 0.05)
        self.investment: float = config.get("investment", 5000.0)
        self.poll_interval: int = config.get("poll_interval", 10)

        self.grids: dict[str, dict] = {}  # symbol -> grid state

    def _build_grid(self, symbol: str, price: float) -> dict:
        step = (price * self.range_pct * 2) / (self.levels * 2)
        grid_prices = [round(price + step * i, 6) for i in range(-self.levels, self.levels + 1)]
        inv_per_grid = (self.investment / len(self.symbols)) / (self.levels * 2)
        return {
            "prices": grid_prices,
            "inv_per_grid": inv_per_grid,
            "open_buys": {},
            "total_pnl": 0.0,
        }

    def _is_outside(self, grid: dict, price: float) -> bool:
        return price < grid["prices"][0] or price >= grid["prices"][-1]

    async def _reset_grid(self, symbol: str, price: float) -> None:
        grid = self.grids[symbol]
        forced_pnl = 0.0
        for i, buy in list(grid["open_buys"].items()):
            cost = buy["size"] * buy["entry_price"]
            proceeds = buy["size"] * price
            pnl = proceeds - cost
            forced_pnl += pnl
            grid["total_pnl"] += pnl
            await self.record_trade(self.bot_id, self.user_id, {
                "symbol": symbol, "entry_price": buy["entry_price"],
                "exit_price": price, "size": buy["size"],
                "pnl_usdt": round(pnl, 6), "pnl_pct": round(pnl / cost * 100, 4),
                "reason": "GRID_RESET", "entry_time": buy["entry_time"],
            })
        grid["open_buys"].clear()
        self.grids[symbol] = self._build_grid(symbol, price)
        await self.log(self.bot_id,
            f"[GRID] RESET {symbol} @ ${price:,.4f} | Forced PnL: ${forced_pnl:+.4f}")

    async def _check(self, symbol: str, price: float) -> None:
        grid = self.grids[symbol]
        for i, level_price in enumerate(grid["prices"][:-1]):
            next_price = grid["prices"][i + 1]

            if level_price <= price < next_price and i not in grid["open_buys"]:
                size = grid["inv_per_grid"] / price
                grid["open_buys"][i] = {"size": size, "entry_price": price, "entry_time": datetime.now(UTC)}
                await self.log(self.bot_id, f"[GRID] BUY  {symbol} level {i} @ ${price:,.4f}")

            elif price >= next_price and i in grid["open_buys"]:
                buy = grid["open_buys"].pop(i)
                cost = buy["size"] * buy["entry_price"]
                proceeds = buy["size"] * price
                pnl = proceeds - cost
                grid["total_pnl"] += pnl
                await self.log(self.bot_id,
                    f"[GRID] SELL {symbol} level {i} @ ${price:,.4f} | PnL: ${pnl:+.4f}")
                await self.record_trade(self.bot_id, self.user_id, {
                    "symbol": symbol, "entry_price": buy["entry_price"],
                    "exit_price": price, "size": buy["size"],
                    "pnl_usdt": round(pnl, 6), "pnl_pct": round(pnl / cost * 100, 4),
                    "reason": "GRID_SELL", "entry_time": buy["entry_time"],
                })

    async def run(self) -> None:
        # Initialize grids
        for symbol in self.symbols:
            ticker = await self.exchange.fetch_ticker(symbol)
            price = ticker["last"]
            self.grids[symbol] = self._build_grid(symbol, price)
            await self.log(self.bot_id,
                f"[GRID] {symbol} initialized @ ${price:,.4f} | "
                f"Range: ${self.grids[symbol]['prices'][0]:,.4f} — ${self.grids[symbol]['prices'][-1]:,.4f}")

        while True:
            for symbol in self.symbols:
                ticker = await self.exchange.fetch_ticker(symbol)
                price = ticker["last"]

                if self._is_outside(self.grids[symbol], price):
                    await self._reset_grid(symbol, price)

                await self._check(symbol, price)

            await asyncio.sleep(self.poll_interval)
