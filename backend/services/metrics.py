"""
Risk and performance metrics, shared by the live dashboard and the backtester.

Win rate and total P&L are the two most misleading numbers in trading. A bot
can win 95% of the time and still lose money (tiny wins, huge losses), or
double your account while suffering a drawdown you would never have sat
through. These are the numbers that actually separate an edge from luck.
"""

from math import sqrt
from typing import Iterable, Sequence


def profit_factor(pnls: Sequence[float]) -> float:
    """Gross profit / gross loss. Below 1.0 loses money. Above ~1.3 is decent."""
    gains = sum(p for p in pnls if p > 0)
    losses = abs(sum(p for p in pnls if p < 0))
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return gains / losses


def expectancy(pnls: Sequence[float]) -> float:
    """Average P&L per trade — what you expect to make each time you trade."""
    return sum(pnls) / len(pnls) if pnls else 0.0


def avg_win_loss(pnls: Sequence[float]) -> tuple[float, float]:
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    return (
        sum(wins) / len(wins) if wins else 0.0,
        sum(losses) / len(losses) if losses else 0.0,
    )


def max_drawdown(equity: Sequence[float]) -> tuple[float, float]:
    """Deepest peak-to-trough fall in an equity curve.

    Returns (absolute, fraction). This is the number that decides whether a
    strategy is survivable: a curve that ends up 5% after being down 40% is
    not something a human actually holds through.
    """
    if not equity:
        return 0.0, 0.0
    peak = equity[0]
    worst_abs = 0.0
    worst_pct = 0.0
    for value in equity:
        peak = max(peak, value)
        drop = peak - value
        if drop > worst_abs:
            worst_abs = drop
            worst_pct = drop / peak if peak else 0.0
    return worst_abs, worst_pct


def sharpe(returns: Sequence[float], periods_per_year: int = 365) -> float:
    """Return per unit of volatility, annualised. Rough guide: >1 is good.

    Computed on per-period returns (e.g. daily), not per trade.
    """
    n = len(returns)
    if n < 2:
        return 0.0
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    sd = sqrt(var)
    if sd == 0:
        return 0.0
    return (mean / sd) * sqrt(periods_per_year)


def equity_curve(pnls: Iterable[float], starting: float = 5000.0) -> list[float]:
    """Running account value from a sequence of trade P&Ls."""
    curve = [starting]
    for pnl in pnls:
        curve.append(curve[-1] + pnl)
    return curve


def summarize(pnls: Sequence[float], starting: float = 5000.0) -> dict:
    """Full performance picture for one strategy."""
    curve = equity_curve(pnls, starting)
    dd_abs, dd_pct = max_drawdown(curve)
    wins = [p for p in pnls if p > 0]
    avg_w, avg_l = avg_win_loss(pnls)
    total = sum(pnls)

    return {
        "trades": len(pnls),
        "total_pnl": round(total, 4),
        "return_pct": round(total / starting * 100, 3) if starting else 0.0,
        "win_rate": round(len(wins) / len(pnls) * 100, 1) if pnls else 0.0,
        "profit_factor": round(profit_factor(pnls), 3),
        "expectancy": round(expectancy(pnls), 4),
        "avg_win": round(avg_w, 4),
        "avg_loss": round(avg_l, 4),
        "max_drawdown": round(dd_abs, 4),
        "max_drawdown_pct": round(dd_pct * 100, 2),
        "final_equity": round(curve[-1], 2),
    }
