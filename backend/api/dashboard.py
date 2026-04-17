from datetime import datetime, UTC

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.bot import Bot
from backend.models.trade import Trade
from backend.models.user import User
from backend.schemas.trade import DashboardStats
from backend.workers import task_manager
from .deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Trade).where(Trade.user_id == current_user.id))
    all_trades = result.scalars().all()

    today = datetime.now(UTC).date()
    trades_today = sum(1 for t in all_trades if t.exit_time.date() == today)
    wins = sum(1 for t in all_trades if t.pnl_usdt > 0)
    total_pnl = sum(t.pnl_usdt for t in all_trades)
    best = max((t.pnl_usdt for t in all_trades), default=0.0)
    worst = min((t.pnl_usdt for t in all_trades), default=0.0)

    bots_result = await db.execute(select(Bot).where(Bot.user_id == current_user.id))
    all_bots = bots_result.scalars().all()
    active_bots = sum(1 for b in all_bots if task_manager.is_running(b.id))

    return DashboardStats(
        total_pnl=round(total_pnl, 4),
        total_trades=len(all_trades),
        win_rate=round(wins / len(all_trades) * 100, 1) if all_trades else 0.0,
        best_trade=round(best, 4),
        worst_trade=round(worst, 4),
        active_bots=active_bots,
        trades_today=trades_today,
    )
