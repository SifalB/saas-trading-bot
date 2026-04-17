from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
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
    q = select(Trade).where(Trade.user_id == current_user.id)
    if bot_id:
        q = q.where(Trade.bot_id == bot_id)
    if symbol:
        q = q.where(Trade.symbol == symbol)
    q = q.order_by(Trade.exit_time.desc()).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()
