"""
Trading cost model — shared by every strategy.

Two jobs:

1. `net_pnl()` subtracts exchange fees and slippage from every simulated fill,
   so a trade that "wins" by less than it costs to make is correctly recorded
   as a LOSS. This is applied centrally in bot_runner._save_trade, so no
   strategy can bypass it.

2. `min_profit_pct()` / `enforce_tp()` stop strategies from *aiming* at
   profits smaller than the round trip costs in the first place. A take-profit
   below the break-even threshold is not a strategy, it's a fee donation.
"""

from backend.core.config import settings

# Cost of one full round trip (buy + sell) as a fraction of notional.
ROUND_TRIP_PCT: float = 2 * (settings.TRADING_FEE_RATE + settings.SLIPPAGE_RATE)

# Require a target to clear costs by this multiple before a trade is worth
# taking — a target exactly equal to costs nets zero.
MIN_PROFIT_MARGIN: float = 1.5


def min_profit_pct() -> float:
    """Smallest gain (as a fraction) worth targeting after costs."""
    return ROUND_TRIP_PCT * MIN_PROFIT_MARGIN


def enforce_tp(take_profit_pct: float) -> float:
    """Raise a take-profit target to the minimum that survives costs."""
    return max(take_profit_pct, min_profit_pct())


def clears_costs(entry_price: float, exit_price: float) -> bool:
    """True when this round trip beats its own costs by the required margin."""
    if entry_price <= 0:
        return False
    return (exit_price - entry_price) / entry_price >= min_profit_pct()


def trade_costs(entry_price: float, exit_price: float, size: float) -> float:
    """Total fees + slippage in USDT for a round trip of `size` units."""
    notional = size * entry_price + size * exit_price
    return notional * (settings.TRADING_FEE_RATE + settings.SLIPPAGE_RATE)


def net_pnl(entry_price: float, exit_price: float, size: float) -> tuple[float, float]:
    """Return (net_pnl_usdt, costs_usdt) for a round trip."""
    gross = size * (exit_price - entry_price)
    costs = trade_costs(entry_price, exit_price, size)
    return gross - costs, costs
