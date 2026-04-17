from datetime import datetime

from pydantic import BaseModel


class TradeResponse(BaseModel):
    id: int
    bot_id: int
    symbol: str
    entry_price: float
    exit_price: float
    size: float
    pnl_usdt: float
    pnl_pct: float
    reason: str
    entry_time: datetime
    exit_time: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_pnl: float
    total_trades: int
    win_rate: float
    best_trade: float
    worst_trade: float
    active_bots: int
    trades_today: int
