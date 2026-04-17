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
from .strategy_grid import GridStrategy
from .strategy_scalp import ScalpStrategy
from .strategy_corr import CorrStrategy


async def _save_log(bot_id: int, message: str) -> None:
    await task_manager.push_log(bot_id, message)
    async with AsyncSessionLocal() as db:
        db.add(BotLog(bot_id=bot_id, message=message))
        await db.commit()


async def _save_trade(bot_id: int, user_id: int, trade: dict) -> None:
    async with AsyncSessionLocal() as db:
        db.add(Trade(
            bot_id=bot_id,
            user_id=user_id,
            symbol=trade["symbol"],
            entry_price=trade["entry_price"],
            exit_price=trade["exit_price"],
            size=trade["size"],
            pnl_usdt=trade["pnl_usdt"],
            pnl_pct=trade["pnl_pct"],
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
