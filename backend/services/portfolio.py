"""
Live portfolio snapshot for a running strategy.

Closed trades are in the database, but a bot's *current* cash and open
positions only exist in memory while it runs. This reads that live state so
the dashboard can show money available to trade versus money already
committed — the figures that move every time a bot buys or sells.

Strategies store positions in four different shapes; all are handled here so
no strategy needs to know the dashboard exists.
"""

from typing import Any


def _positions(strategy: Any) -> list[tuple[str, float, float]]:
    """Return [(symbol, size, entry_price)] across every position shape."""
    out: list[tuple[str, float, float]] = []

    # Most strategies: {symbol: {size, entry_price}}
    for symbol, pos in (getattr(strategy, "positions", None) or {}).items():
        if isinstance(pos, dict) and "size" in pos:
            out.append((symbol, float(pos["size"]), float(pos["entry_price"])))

    # Rotation: a single concentrated holding
    holding = getattr(strategy, "holding", None)
    if isinstance(holding, dict) and "size" in holding:
        out.append((holding["symbol"], float(holding["size"]), float(holding["entry_price"])))

    # Buy & hold: {symbol: {size, entry_price}} basket
    for symbol, pos in (getattr(strategy, "holdings", None) or {}).items():
        if isinstance(pos, dict) and "size" in pos:
            out.append((symbol, float(pos["size"]), float(pos["entry_price"])))

    # Grid: one open buy per filled level, nested per symbol
    for symbol, grid in (getattr(strategy, "grids", None) or {}).items():
        for level in (grid.get("open_buys") or {}).values():
            out.append((symbol, float(level["size"]), float(level["entry_price"])))

    return out


def snapshot(strategy: Any) -> dict:
    """Cash free to trade, capital committed to positions, and position count."""
    positions = _positions(strategy)
    return {
        "cash": float(getattr(strategy, "balance", 0.0) or 0.0),
        "deployed": sum(size * entry for _, size, entry in positions),
        "open_positions": len(positions),
    }
