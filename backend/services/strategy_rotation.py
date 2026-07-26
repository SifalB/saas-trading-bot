"""
Async Momentum Rotation Strategy
---------------------------------
Ranks the universe by recent momentum (return over a lookback window) and
holds only the strongest coin. Rotates when leadership changes; goes flat
when no coin has positive momentum (risk-off).

Personality: slow, few trades, portfolio-style rather than signal scalping —
a very different profile from every other bot here.
"""

import asyncio
from datetime import datetime, UTC
from typing import Callable

import pandas as pd


class RotationStrategy:
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

        self.momentum_lookback: int = config.get("momentum_lookback", 24)  # bars
        self.min_momentum: float    = config.get("min_momentum", 0.0)      # require > 0 to hold
        self.rebalance_seconds: int = config.get("rebalance_seconds", 3600)
        self.switch_margin: float   = config.get("switch_margin", 0.005)   # 0.5% edge to rotate
        self.stop_loss_pct: float   = config.get("stop_loss_pct", 0.05)
        self.trade_size_pct: float  = config.get("trade_size_pct", 0.95)   # concentrated by design
        self.poll_interval: int     = config.get("poll_interval", 60)

        self.balance: float = config.get("initial_balance", 5000.0)
        self.holding: dict | None = None   # {"symbol", "size", "entry_price", "entry_time", "stop_loss"}

    async def _momentum(self, symbol: str) -> float | None:
        ohlcv = await self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=self.candles)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        if len(df) < self.momentum_lookback + 2:
            return None
        past = float(df["close"].iloc[-(self.momentum_lookback + 1)])
        last = float(df["close"].iloc[-2])
        if past <= 0:
            return None
        return (last - past) / past

    async def _sell(self, price: float, reason: str) -> None:
        pos = self.holding
        self.holding = None
        proceeds = pos["size"] * price
        pnl = proceeds - pos["size"] * pos["entry_price"]
        self.balance += proceeds
        await self.log(self.bot_id,
            f"[ROTATION] SELL {pos['symbol']} @ ${price:,.4f} | {reason} | PnL: ${pnl:+.2f}")
        await self.record_trade(self.bot_id, self.user_id, {
            "symbol": pos["symbol"],
            "entry_price": pos["entry_price"],
            "exit_price": price,
            "size": pos["size"],
            "pnl_usdt": round(pnl, 4),
            "pnl_pct": round((price - pos["entry_price"]) / pos["entry_price"] * 100, 4),
            "reason": reason,
            "entry_time": pos["entry_time"],
        })

    async def _buy(self, symbol: str, price: float, mom: float) -> None:
        spend = self.balance * self.trade_size_pct
        size = spend / price
        self.balance -= spend
        self.holding = {
            "symbol": symbol,
            "size": size,
            "entry_price": price,
            "entry_time": datetime.now(UTC),
            "stop_loss": price * (1 - self.stop_loss_pct),
        }
        await self.log(self.bot_id,
            f"[ROTATION] BUY {symbol} @ ${price:,.4f} | momentum {mom*100:+.2f}% | spent ${spend:,.2f}")

    async def run(self) -> None:
        await self.log(self.bot_id,
            f"[ROTATION] Started | Universe: {', '.join(self.symbols)} | "
            f"hold strongest over {self.momentum_lookback}x{self.timeframe}, "
            f"rebalance every {self.rebalance_seconds//60}m")

        last_rebalance = 0.0
        while True:
            try:
                loop = asyncio.get_running_loop()
                now = loop.time()

                # Hard stop on the current holding is checked every poll
                if self.holding:
                    ticker = await self.exchange.fetch_ticker(self.holding["symbol"])
                    price = float(ticker["last"])
                    if price <= self.holding["stop_loss"]:
                        await self._sell(price, "STOP_LOSS")
                        last_rebalance = now  # wait a cycle before re-entering

                if now - last_rebalance >= self.rebalance_seconds:
                    last_rebalance = now
                    scores: dict[str, float] = {}
                    for symbol in self.symbols:
                        try:
                            m = await self._momentum(symbol)
                            if m is not None:
                                scores[symbol] = m
                        except Exception as e:  # noqa: BLE001
                            await self.log(self.bot_id, f"[ROTATION] Momentum error {symbol}: {e}")

                    if scores:
                        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
                        best, best_mom = ranked[0]
                        summary = " | ".join(f"{s.split('/')[0]} {m*100:+.2f}%" for s, m in ranked)
                        await self.log(self.bot_id, f"[ROTATION] Ranking: {summary}")

                        if best_mom <= self.min_momentum:
                            if self.holding:
                                t = await self.exchange.fetch_ticker(self.holding["symbol"])
                                await self._sell(float(t["last"]), "RISK_OFF")
                            else:
                                await self.log(self.bot_id, "[ROTATION] Flat — no positive momentum")
                        elif self.holding is None:
                            t = await self.exchange.fetch_ticker(best)
                            await self._buy(best, float(t["last"]), best_mom)
                        elif best != self.holding["symbol"]:
                            held_mom = scores.get(self.holding["symbol"], -1.0)
                            if best_mom - held_mom > self.switch_margin:
                                t_old = await self.exchange.fetch_ticker(self.holding["symbol"])
                                await self._sell(float(t_old["last"]), "ROTATE")
                                t_new = await self.exchange.fetch_ticker(best)
                                await self._buy(best, float(t_new["last"]), best_mom)
            except Exception as e:  # noqa: BLE001
                await self.log(self.bot_id, f"[ROTATION] Error: {e}")

            await asyncio.sleep(self.poll_interval)
