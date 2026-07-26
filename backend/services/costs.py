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


# A winning trade must be worth at least this multiple of a losing one,
# measured AFTER costs. At 1.0 the strategy breaks even on a 50% hit rate.
MIN_REWARD_RISK: float = 1.0


def viable_tp(take_profit_pct: float, stop_loss_pct: float,
              min_rr: float = MIN_REWARD_RISK) -> float:
    """Smallest take-profit whose NET win is worth its NET loss.

    Costs hit twice: they shrink every win and deepen every loss. A 0.45% TP
    against a 0.25% SL looks like 1.8:1, but after a 0.30% round trip it is
    +0.15% vs -0.55% — needing a 79% hit rate just to break even. This
    returns the target that restores a sane payoff.
    """
    required = min_rr * (stop_loss_pct + ROUND_TRIP_PCT) + ROUND_TRIP_PCT
    return max(take_profit_pct, required, min_profit_pct())


def breakeven_win_rate(take_profit_pct: float, stop_loss_pct: float) -> float:
    """Hit rate needed to break even after costs, as a fraction."""
    net_win = take_profit_pct - ROUND_TRIP_PCT
    net_loss = stop_loss_pct + ROUND_TRIP_PCT
    if net_win + net_loss <= 0:
        return 1.0
    return net_loss / (net_win + net_loss)


def is_viable(take_profit_pct: float, stop_loss_pct: float) -> bool:
    """False when a trade cannot pay for itself — the bot should not enter."""
    return (take_profit_pct - ROUND_TRIP_PCT) > 0 and \
        breakeven_win_rate(take_profit_pct, stop_loss_pct) <= 0.65


def clears_costs(entry_price: float, exit_price: float) -> bool:
    """True when this round trip beats its own costs by the required margin."""
    if entry_price <= 0:
        return False
    return (exit_price - entry_price) / entry_price >= min_profit_pct()


def in_dead_zone(entry_price: float, price: float) -> bool:
    """True when a position is in profit but not by enough to cover costs.

    Selling here books a guaranteed loss, so time-based exits wait instead.
    Stop losses must still fire — this only ever defers a *profitable-looking*
    exit, never a losing one.
    """
    if entry_price <= 0:
        return False
    gain = (price - entry_price) / entry_price
    return 0 < gain < min_profit_pct()


def trade_costs(entry_price: float, exit_price: float, size: float) -> float:
    """Total fees + slippage in USDT for a round trip of `size` units."""
    notional = size * entry_price + size * exit_price
    return notional * (settings.TRADING_FEE_RATE + settings.SLIPPAGE_RATE)


def net_proceeds(entry_price: float, exit_price: float, size: float) -> float:
    """Cash actually returned to the wallet when closing a position.

    Strategies must credit this, not the gross `size * price`. Crediting gross
    makes a bot believe it holds more cash than it does — the error compounds
    with every trade and silently inflates position sizes.
    """
    return size * exit_price - trade_costs(entry_price, exit_price, size)


def net_pnl(entry_price: float, exit_price: float, size: float) -> tuple[float, float]:
    """Return (net_pnl_usdt, costs_usdt) for a round trip."""
    gross = size * (exit_price - entry_price)
    costs = trade_costs(entry_price, exit_price, size)
    return gross - costs, costs
