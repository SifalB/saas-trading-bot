from datetime import datetime

from pydantic import BaseModel


class BotCreate(BaseModel):
    name: str
    type: str           # grid | scalp | corr
    config: dict = {}
    paper_mode: bool = True


class BotUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None
    paper_mode: bool | None = None


class BotResponse(BaseModel):
    id: int
    name: str
    type: str
    config: dict
    paper_mode: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Default configs per strategy type — sent to frontend for pre-filling forms
GRID_DEFAULT_CONFIG = {
    "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"],
    "levels": 7,
    "range_pct": 0.05,
    "investment": 5000.0,
    "poll_interval": 10,
}

SCALP_DEFAULT_CONFIG = {
    "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"],
    "timeframe": "1m",
    "rsi_period": 14,
    "rsi_buy": 50,
    "rsi_sell": 62,
    "ema_period": 20,
    "take_profit_pct": 0.005,
    "stop_loss_pct": 0.003,
    "trade_size_pct": 0.45,
    "initial_balance": 5000.0,
    "poll_interval": 10,
}

CORR_DEFAULT_CONFIG = {
    "trigger_symbol": "BTC/USDT",
    "alt_symbols": ["ETH/USDT", "BNB/USDT", "SOL/USDT"],
    "btc_move_threshold": 0.0035,
    "btc_window_seconds": 20,
    "take_profit_pct": 0.006,
    "stop_loss_pct": 0.003,
    "trade_timeout_seconds": 180,
    "trade_size_pct": 0.25,
    "initial_balance": 5000.0,
    "poll_interval": 5,
}

DEFAULT_CONFIGS = {
    "grid": GRID_DEFAULT_CONFIG,
    "scalp": SCALP_DEFAULT_CONFIG,
    "corr": CORR_DEFAULT_CONFIG,
}
