from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.bot import Bot
from backend.models.trade import Trade
from backend.models.user import User
from backend.schemas.trade import TradeResponse
from .deps import get_current_user

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/", response_model=list[TradeResponse])
async def get_trades(
    bot_id: int | None = Query(None),
    symbol: str | None = Query(None),
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Trade, Bot.type, Bot.name)
        .join(Bot, Trade.bot_id == Bot.id)
        .where(Trade.user_id == current_user.id)
    )
    if bot_id:
        q = q.where(Trade.bot_id == bot_id)
    if symbol:
        q = q.where(Trade.symbol == symbol)
    q = q.order_by(Trade.exit_time.desc()).limit(limit)
    result = await db.execute(q)

    return [
        TradeResponse(
            id=t.id, bot_id=t.bot_id, bot_type=bot_type, bot_name=bot_name,
            symbol=t.symbol, entry_price=t.entry_price, exit_price=t.exit_price,
            size=t.size, pnl_usdt=t.pnl_usdt, pnl_pct=t.pnl_pct,
            fees_usdt=t.fees_usdt, reason=t.reason,
            entry_time=t.entry_time, exit_time=t.exit_time,
        )
        for t, bot_type, bot_name in result.all()
    ]
