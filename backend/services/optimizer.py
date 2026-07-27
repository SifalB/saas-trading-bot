"""
Parameter search for the trading strategies — with the discipline that makes
the answer trustworthy.

Tuning parameters on historical data and then judging them on that same data
always produces spectacular results and worthless strategies. It is exactly
the mistake of scoring a model on its training set: the search does not find
an edge, it memorises the noise of one particular month.

So the history is split:

    [------------- TRAIN (optimise here) -------------][--- TEST (never seen) ---]

Every candidate is scored on TRAIN, and only the winner is then run on TEST.
The TEST number is the honest one. When TRAIN looks brilliant and TEST does
not, the parameters are curve-fitted and are reported as such rather than
quietly presented as a discovery.
"""

from __future__ import annotations

import random
from typing import Any, Iterable

import pandas as pd

from backend.schemas.bot import DEFAULT_CONFIGS, STRATEGY_LABELS

# Parameter spaces. Values are deliberately coarse: a fine grid mostly buys
# more chances to fit noise, not better strategies.
SEARCH_SPACE: dict[str, dict[str, list]] = {
    "grid": {
        "levels": [4, 7, 10, 14],
        "range_pct": [0.02, 0.035, 0.05, 0.08],
    },
    "scalp": {
        "timeframe": ["1m", "5m", "15m"],
        "rsi_buy": [40, 50, 55],
        "rsi_sell": [62, 70, 78],
        "take_profit_pct": [0.006, 0.01, 0.02, 0.035],
        "stop_loss_pct": [0.004, 0.008, 0.015],
        "trade_size_pct": [0.2, 0.45],
    },
    "corr": {
        "btc_move_threshold": [0.002, 0.0035, 0.006, 0.01],
        "take_profit_pct": [0.008, 0.015, 0.03],
        "stop_loss_pct": [0.005, 0.01, 0.02],
        "trade_timeout_seconds": [300, 900, 3600],
    },
    "mtf": {
        "rsi_mid_low": [45, 52, 58],
        "rsi_mid_high": [65, 70, 80],
        "volume_multiplier": [1.0, 1.5, 2.5],
        "take_profit_pct": [0.008, 0.015, 0.03],
        "stop_loss_pct": [0.004, 0.008, 0.015],
        "trade_timeout_seconds": [300, 1800, 7200],
    },
    "breakout": {
        "timeframe": ["1h", "4h"],
        "entry_lookback": [10, 20, 40, 55],
        "exit_lookback": [5, 10, 20],
        "atr_trail_mult": [1.5, 2.5, 4.0],
        "stop_loss_pct": [0.02, 0.04, 0.08],
    },
    "dip": {
        "timeframe": ["15m", "1h"],
        "rsi_oversold": [5, 10, 20],
        "bb_std": [1.5, 2.0, 2.5],
        "trend_sma_period": [50, 100, 200],
        "stop_loss_pct": [0.015, 0.03, 0.06],
    },
    "volbreak": {
        "timeframe": ["5m", "15m", "1h"],
        "breakout_mult": [1.2, 2.0, 3.0],
        "lookback_bars": [12, 24, 48],
        "tp_atr_mult": [1.5, 3.0, 5.0],
        "sl_atr_mult": [1.0, 2.0],
    },
    "rotation": {
        "momentum_lookback": [12, 24, 72, 168],
        "switch_margin": [0.005, 0.02, 0.05],
        "min_momentum": [0.0, 0.01, 0.03],
        "stop_loss_pct": [0.05, 0.10],
    },
    # "hold" has nothing to tune — it is the benchmark, by definition fixed.
}


def sample_params(stype: str, trials: int, seed: int = 0) -> list[dict]:
    """Random search over the space.

    Random search beats an exhaustive grid here: it covers more distinct
    values per parameter for the same compute, and an exhaustive grid over
    six parameters is both slower and more prone to fitting noise.
    """
    space = SEARCH_SPACE.get(stype)
    if not space:
        return [{}]

    combos = 1
    for values in space.values():
        combos *= len(values)

    rng = random.Random(seed)
    if combos <= trials:  # small enough to enumerate exhaustively
        out: list[dict] = [{}]
        for key, values in space.items():
            out = [{**base, key: v} for base in out for v in values]
        return out

    seen: set[tuple] = set()
    picks: list[dict] = []
    while len(picks) < trials and len(seen) < combos:
        candidate = {k: rng.choice(v) for k, v in space.items()}
        key = tuple(sorted(candidate.items()))
        if key in seen:
            continue
        seen.add(key)
        picks.append(candidate)
    return picks


def split_data(data: dict[str, pd.DataFrame], train_frac: float = 0.6
               ) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    """Chronological split — never random.

    Shuffling would leak the future into the training set: a model that has
    seen tomorrow's candle can 'predict' today. Markets are a time series;
    the test set must come strictly after the training set.
    """
    train, test = {}, {}
    for symbol, df in data.items():
        cut = int(len(df) * train_frac)
        train[symbol] = df.iloc[:cut].reset_index(drop=True)
        test[symbol] = df.iloc[cut:].reset_index(drop=True)
    return train, test


def buy_hold_return(data: dict[str, pd.DataFrame]) -> float:
    """Equal-weight basket return over a window, as a percentage."""
    changes = [
        (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
        for df in data.values() if len(df) > 1
    ]
    return sum(changes) / len(changes) if changes else 0.0


def score(summary: dict) -> float:
    """Rank candidates by risk-adjusted return, not raw return.

    Return alone rewards a strategy that made one lucky trade or rode a 60%
    drawdown. Dividing by drawdown prefers results that were survivable, and
    requiring a few trades stops a single fluke from topping the table.
    """
    if summary["trades"] < 5:
        return -999.0
    dd = max(summary["max_drawdown_pct"], 1.0)
    return summary["return_pct"] / dd


def verdict(train_pct: float, test_pct: float, benchmark_test: float) -> str:
    """Plain-language read on whether a result is real or curve-fitted."""
    if test_pct > benchmark_test and test_pct > 0:
        return "BEATS BUY & HOLD out-of-sample"
    # Judged on the unseen half alone: how it did while being fitted is not
    # evidence either way. A strategy that made money on data the search never
    # saw is a real (if unremarkable) result and must not be filed as "no edge"
    # merely because the training window happened to be a bear market.
    if test_pct > 0:
        return "profitable out-of-sample, but loses to buy & hold"
    if train_pct > 0 and test_pct <= 0:
        return "OVERFIT - good in training, loses on unseen data"
    return "no edge"


def format_params(params: dict) -> str:
    if not params:
        return "(defaults)"
    return ", ".join(f"{k}={v}" for k, v in sorted(params.items()))


def merged_config(stype: str, params: dict) -> dict:
    return {**DEFAULT_CONFIGS[stype], **params}


def strategies_to_optimize() -> Iterable[str]:
    return [s for s in STRATEGY_LABELS if s in SEARCH_SPACE]
