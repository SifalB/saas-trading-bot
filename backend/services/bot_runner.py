"""
Bridges the FastAPI layer with the strategy engines.
Responsible for building the coroutine that runs a bot,
saving trades to DB, and pushing logs to the WebSocket queue.
"""

import asyncio
from datetime import datetime, UTC

import ccxt.async_support as ccxt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import AsyncSessionLocal
from backend.core.security import decrypt
from backend.models.bot import Bot, BotLog
from backend.models.trade import Trade
from backend.models.user import User
from backend.workers import task_manager
from . import costs
from .strategy_grid import GridStrategy
from .strategy_scalp import ScalpStrategy
from .strategy_corr import CorrStrategy
from .strategy_mtf import MtfStrategy
from .strategy_breakout import BreakoutStrategy
from .strategy_dip import DipStrategy
from .strategy_volbreak import VolBreakStrategy
from .strategy_rotation import RotationStrategy
from .strategy_hold import HoldStrategy


async def _save_log(bot_id: int, message: str) -> None:
    await task_manager.push_log(bot_id, message)
    async with AsyncSessionLocal() as db:
        db.add(BotLog(bot_id=bot_id, message=message))
        await db.commit()


async def _save_trade(bot_id: int, user_id: int, trade: dict) -> None:
    """Persist a trade with exchange fees and slippage deducted.

    Applied here, centrally, so every strategy is scored on what a real
    account would actually keep — a gain smaller than its own round-trip
    cost lands in the database as a loss, and is never counted as a win.
    """
    entry_price = trade["entry_price"]
    exit_price = trade["exit_price"]
    size = trade["size"]

    # MARK rows are mark-to-market snapshots of a held position, not round
    # trips, so they must not be charged entry/exit costs.
    if trade["reason"] == "MARK":
        net, fees = trade["pnl_usdt"], 0.0
    else:
        net, fees = costs.net_pnl(entry_price, exit_price, size)

    cost_basis = size * entry_price
    async with AsyncSessionLocal() as db:
        db.add(Trade(
            bot_id=bot_id,
            user_id=user_id,
            symbol=trade["symbol"],
            entry_price=entry_price,
            exit_price=exit_price,
            size=size,
            pnl_usdt=round(net, 6),
            pnl_pct=round(net / cost_basis * 100, 4) if cost_basis else 0.0,
            fees_usdt=round(fees, 6),
            reason=trade["reason"],
            entry_time=trade["entry_time"],
            exit_time=trade.get("exit_time", datetime.now(UTC)),
        ))
        await db.commit()


async def _set_status(bot_id: int, status: str) -> None:
    async with AsyncSessionLocal() as db:
        bot = await db.get(Bot, bot_id)
        if bot:
            bot.status = status
            await db.commit()


def _build_exchange(api_key: str | None, secret: str | None, paper_mode: bool) -> ccxt.binance:
    if paper_mode or not api_key:
        return ccxt.binance({"options": {"defaultType": "spot"}})
    return ccxt.binance({
        "apiKey": decrypt(api_key),
        "secret": decrypt(secret),
        "options": {"defaultType": "spot"},
    })


STRATEGY_MAP = {
    "grid": GridStrategy,
    "scalp": ScalpStrategy,
    "corr": CorrStrategy,
    "mtf": MtfStrategy,
    "breakout": BreakoutStrategy,
    "dip": DipStrategy,
    "volbreak": VolBreakStrategy,
    "rotation": RotationStrategy,
    "hold": HoldStrategy,
}


async def run_bot(bot_id: int) -> None:
    async with AsyncSessionLocal() as db:
        bot: Bot = await db.get(Bot, bot_id)
        user: User = await db.get(User, bot.user_id)

    exchange = _build_exchange(user.binance_api_key, user.binance_secret, bot.paper_mode)
    strategy_cls = STRATEGY_MAP.get(bot.type)

    if not strategy_cls:
        await _save_log(bot_id, f"Unknown strategy type: {bot.type}")
        await _set_status(bot_id, "error")
        return

    await _set_status(bot_id, "running")
    await _save_log(bot_id, f"Bot {bot.name} ({bot.type}) started — paper={bot.paper_mode}")

    strategy = strategy_cls(
        bot_id=bot_id,
        user_id=bot.user_id,
        config=bot.config,
        exchange=exchange,
        log_fn=_save_log,
        trade_fn=_save_trade,
    )

    try:
        await strategy.run()
    except asyncio.CancelledError:
        await _save_log(bot_id, "Bot stopped by user.")
    except Exception as e:
        await _save_log(bot_id, f"ERROR: {e}")
        await _set_status(bot_id, "error")
        return
    finally:
        await exchange.close()

    await _set_status(bot_id, "stopped")
