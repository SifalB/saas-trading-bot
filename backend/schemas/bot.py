from datetime import datetime

from pydantic import BaseModel


class BotCreate(BaseModel):
    name: str
    type: str           # grid | scalp | corr | mtf
    config: dict = {}
    paper_mode: bool = True


class BotStats(BaseModel):
    bot_id: int
    name: str
    type: str
    status: str
    paper_mode: bool
    total_pnl: float
    win_rate: float
    total_trades: int
    best_trade: float
    worst_trade: float
    initial_balance: float
    current_balance: float


class StrategyStats(BaseModel):
    strategy: str          # grid | scalp | corr | mtf
    label: str
    total_pnl: float
    pnl_today: float
    win_rate: float
    total_trades: int
    trades_today: int
    best_trade: float
    worst_trade: float
    bot_count: int
    running: bool
    initial_balance: float
    current_balance: float
    return_pct: float = 0.0
    vs_benchmark: float = 0.0


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

MTF_DEFAULT_CONFIG = {
    "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"],
    "tf_slow": "15m",
    "tf_mid": "5m",
    "tf_fast": "1m",
    "candles": 100,
    "ema_trend_period": 50,
    "ema_entry_period": 20,
    "rsi_period": 14,
    "rsi_mid_low": 52,
    "rsi_mid_high": 70,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "volume_multiplier": 1.5,
    "stop_loss_pct": 0.0025,
    "take_profit_pct": 0.004,
    "breakeven_trigger_pct": 0.0015,
    "breakeven_buffer_pct": 0.0005,
    "trade_timeout_seconds": 300,
    "trade_size_pct": 0.30,
    "initial_balance": 5000.0,
    "poll_interval": 10,
}

BREAKOUT_DEFAULT_CONFIG = {
    "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"],
    "timeframe": "1h",
    "candles": 120,
    "entry_lookback": 20,
    "exit_lookback": 10,
    "atr_period": 14,
    "atr_trail_mult": 2.5,
    "stop_loss_pct": 0.02,
    "trade_size_pct": 0.25,
    "initial_balance": 5000.0,
    "poll_interval": 60,
}

DIP_DEFAULT_CONFIG = {
    "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"],
    "timeframe": "15m",
    "candles": 250,
    "trend_sma_period": 200,
    "rsi_period": 2,
    "rsi_oversold": 10,
    "bb_period": 20,
    "bb_std": 2.0,
    "stop_loss_pct": 0.015,
    "trade_timeout_seconds": 14400,
    "trade_size_pct": 0.25,
    "initial_balance": 5000.0,
    "poll_interval": 30,
}

VOLBREAK_DEFAULT_CONFIG = {
    "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"],
    "timeframe": "5m",
    "candles": 200,
    "atr_period": 14,
    "breakout_mult": 1.2,
    "lookback_bars": 12,
    "volume_multiplier": 1.3,
    "tp_atr_mult": 1.5,
    "sl_atr_mult": 1.0,
    "trade_timeout_seconds": 3600,
    "trade_size_pct": 0.25,
    "initial_balance": 5000.0,
    "poll_interval": 20,
}

ROTATION_DEFAULT_CONFIG = {
    "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"],
    "timeframe": "1h",
    "candles": 120,
    "momentum_lookback": 24,
    "min_momentum": 0.0,
    "rebalance_seconds": 3600,
    "switch_margin": 0.005,
    "stop_loss_pct": 0.05,
    "trade_size_pct": 0.95,
    "initial_balance": 5000.0,
    "poll_interval": 60,
}

HOLD_DEFAULT_CONFIG = {
    "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"],
    "mark_interval_seconds": 900,
    "initial_balance": 5000.0,
    "poll_interval": 60,
}

# Display names — single source of truth for the API and dashboard.
STRATEGY_LABELS = {
    "mtf": "Multi-Timeframe",
    "scalp": "Scalping (RSI+EMA)",
    "grid": "Grid",
    "corr": "Correlation",
    "breakout": "Donchian Breakout",
    "dip": "Dip Buyer (RSI-2)",
    "volbreak": "Volatility Breakout",
    "rotation": "Momentum Rotation",
    "hold": "Buy & Hold (benchmark)",
}

DEFAULT_CONFIGS = {
    "grid": GRID_DEFAULT_CONFIG,
    "scalp": SCALP_DEFAULT_CONFIG,
    "corr": CORR_DEFAULT_CONFIG,
    "mtf": MTF_DEFAULT_CONFIG,
    "breakout": BREAKOUT_DEFAULT_CONFIG,
    "dip": DIP_DEFAULT_CONFIG,
    "volbreak": VOLBREAK_DEFAULT_CONFIG,
    "rotation": ROTATION_DEFAULT_CONFIG,
    "hold": HOLD_DEFAULT_CONFIG,
}
