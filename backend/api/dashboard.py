from datetime import datetime, UTC

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.bot import Bot
from backend.models.trade import Trade
from backend.models.user import User
from backend.schemas.bot import BotStats, StrategyStats, STRATEGY_LABELS
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


@router.get("/portfolio")
async def portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Live money view: what's free to trade vs committed, plus realized P&L."""
    from backend.services import portfolio as portfolio_svc

    bots_result = await db.execute(select(Bot).where(Bot.user_id == current_user.id))
    all_bots = bots_result.scalars().all()

    trades_result = await db.execute(select(Trade).where(Trade.user_id == current_user.id))
    all_trades = trades_result.scalars().all()

    realized_pnl = sum(t.pnl_usdt for t in all_trades)
    total_fees = sum(t.fees_usdt or 0.0 for t in all_trades)

    cash = deployed = 0.0
    open_positions = 0
    starting_capital = 0.0
    running = 0

    for bot in all_bots:
        starting_capital += float(
            bot.config.get("initial_balance", bot.config.get("investment", 5000.0))
        )
        strategy = task_manager.get_strategy(bot.id)
        if strategy is not None and task_manager.is_running(bot.id):
            running += 1
            snap = portfolio_svc.snapshot(strategy)
            cash += snap["cash"]
            deployed += snap["deployed"]
            open_positions += snap["open_positions"]

    return {
        "starting_capital": round(starting_capital, 2),
        "realized_pnl": round(realized_pnl, 2),
        "total_fees": round(total_fees, 2),
        "available_cash": round(cash, 2),
        "deployed": round(deployed, 2),
        "equity": round(cash + deployed, 2),
        "open_positions": open_positions,
        "running_bots": running,
    }


@router.get("/strategies", response_model=list[StrategyStats])
async def strategies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bots_result = await db.execute(select(Bot).where(Bot.user_id == current_user.id))
    all_bots = bots_result.scalars().all()

    trades_result = await db.execute(select(Trade).where(Trade.user_id == current_user.id))
    all_trades = trades_result.scalars().all()

    today = datetime.now(UTC).date()
    out = []
    for stype, label in STRATEGY_LABELS.items():
        sbots = [b for b in all_bots if b.type == stype]
        bot_ids = {b.id for b in sbots}
        strades = [t for t in all_trades if t.bot_id in bot_ids]
        today_trades = [t for t in strades if t.exit_time and t.exit_time.date() == today]

        total_pnl = sum(t.pnl_usdt for t in strades)
        pnl_today = sum(t.pnl_usdt for t in today_trades)
        wins = sum(1 for t in strades if t.pnl_usdt > 0)
        win_rate = round(wins / len(strades) * 100, 1) if strades else 0.0
        best = max((t.pnl_usdt for t in strades), default=0.0)
        worst = min((t.pnl_usdt for t in strades), default=0.0)
        initial = sum(float(b.config.get("initial_balance", 5000.0)) for b in sbots)
        running = any(task_manager.is_running(b.id) for b in sbots)

        out.append(StrategyStats(
            strategy=stype,
            label=label,
            total_pnl=round(total_pnl, 4),
            pnl_today=round(pnl_today, 4),
            win_rate=win_rate,
            total_trades=len(strades),
            trades_today=len(today_trades),
            best_trade=round(best, 4),
            worst_trade=round(worst, 4),
            bot_count=len(sbots),
            running=running,
            initial_balance=round(initial, 4),
            current_balance=round(initial + total_pnl, 4),
        ))

    # Best performer first; ties keep the STRATEGY_LABELS order.
    return sorted(out, key=lambda x: x.total_pnl, reverse=True)


@router.get("/compare", response_model=list[BotStats])
async def compare_bots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bots_result = await db.execute(select(Bot).where(Bot.user_id == current_user.id))
    all_bots = bots_result.scalars().all()

    trades_result = await db.execute(select(Trade).where(Trade.user_id == current_user.id))
    all_trades = trades_result.scalars().all()

    stats = []
    for bot in all_bots:
        bot_trades = [t for t in all_trades if t.bot_id == bot.id]
        total_pnl = sum(t.pnl_usdt for t in bot_trades)
        wins = sum(1 for t in bot_trades if t.pnl_usdt > 0)
        win_rate = round(wins / len(bot_trades) * 100, 1) if bot_trades else 0.0
        best = max((t.pnl_usdt for t in bot_trades), default=0.0)
        worst = min((t.pnl_usdt for t in bot_trades), default=0.0)
        initial_balance = float(bot.config.get("initial_balance", 5000.0))
        status = "running" if task_manager.is_running(bot.id) else bot.status

        stats.append(BotStats(
            bot_id=bot.id,
            name=bot.name,
            type=bot.type,
            status=status,
            paper_mode=bot.paper_mode,
            total_pnl=round(total_pnl, 4),
            win_rate=win_rate,
            total_trades=len(bot_trades),
            best_trade=round(best, 4),
            worst_trade=round(worst, 4),
            initial_balance=initial_balance,
            current_balance=round(initial_balance + total_pnl, 4),
        ))

    return sorted(stats, key=lambda x: x.total_pnl, reverse=True)
