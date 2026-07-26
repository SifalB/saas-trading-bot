"""
Periodically records each running bot's account value.

Without this the dashboard can only draw a curve by inventing one from total
P&L — which is exactly what it used to do. Real snapshots give a genuine
equity history, and with it a genuine maximum drawdown.
"""

import asyncio
import contextlib
from datetime import datetime, UTC

from sqlalchemy import select

from backend.core.database import AsyncSessionLocal
from backend.models.bot import Bot
from backend.models.equity import EquitySnapshot
from backend.services import portfolio as portfolio_svc
from backend.workers import task_manager

INTERVAL_SECONDS = 300  # 5 minutes

_task: asyncio.Task | None = None


async def _record_once() -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Bot))
        bots = result.scalars().all()

        recorded = 0
        now = datetime.now(UTC)
        for bot in bots:
            strategy = task_manager.get_strategy(bot.id)
            if strategy is None or not task_manager.is_running(bot.id):
                continue
            snap = portfolio_svc.snapshot(strategy)
            db.add(EquitySnapshot(
                bot_id=bot.id,
                user_id=bot.user_id,
                cash=round(snap["cash"], 6),
                deployed=round(snap["deployed"], 6),
                equity=round(snap["cash"] + snap["deployed"], 6),
                recorded_at=now,
            ))
            recorded += 1
        if recorded:
            await db.commit()
        return recorded


async def _loop() -> None:
    while True:
        try:
            await _record_once()
        except Exception as e:  # noqa: BLE001 — never let recording kill the app
            print(f"[equity] snapshot failed: {e}")
        await asyncio.sleep(INTERVAL_SECONDS)


def start() -> None:
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_loop())


async def stop() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _task
    _task = None
