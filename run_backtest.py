"""
Replay every strategy over historical Binance data and rank the results.

    python run_backtest.py            # last 30 days
    python run_backtest.py --days 90  # last 90 days

Data is cached in backtest_data/ so repeat runs are instant.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from backend.services import backtest  # noqa: E402


def _row(r: dict) -> str:
    pf = "inf" if r["profit_factor"] == float("inf") else f"{r['profit_factor']:.2f}"
    return (
        f"{r['label']:<24} {r['return_pct']:>+8.2f}% {r['total_pnl']:>+10.2f} "
        f"{r['trades']:>7} {r['win_rate']:>7.1f}% {pf:>7} "
        f"{r['max_drawdown_pct']:>9.1f}% {r['fees_paid']:>9.2f}"
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest all strategies")
    parser.add_argument("--days", type=int, default=30, help="days of history (default 30)")
    parser.add_argument("--balance", type=float, default=5000.0, help="starting balance per strategy")
    args = parser.parse_args()

    results = await backtest.run_all(days=args.days, starting_balance=args.balance)

    header = (
        f"\n{'STRATEGY':<24} {'RETURN':>9} {'P&L':>10} {'TRADES':>7} "
        f"{'WIN%':>8} {'PF':>7} {'MAX DD':>10} {'FEES':>9}"
    )
    print(header)
    print("-" * len(header))

    benchmark = next((r for r in results if r["strategy"] == "hold"), None)
    for r in results:
        print(_row(r))

    if benchmark:
        print("\nVersus buy & hold (the only comparison that matters):")
        bench = benchmark["return_pct"]
        print(f"  Buy & Hold returned {bench:+.2f}%")
        beat = [r for r in results
                if r["strategy"] != "hold" and r["return_pct"] > bench]
        if beat:
            for r in beat:
                print(f"  BEAT IT: {r['label']} {r['return_pct']:+.2f}% "
                      f"({r['return_pct'] - bench:+.2f}%)")
        else:
            print("  Nothing beat it. Over this period, trading destroyed value.")

    print("\nReminder: one historical period is not proof. Re-run across "
          "different windows (--days 90, 180) before trusting any of it.")


if __name__ == "__main__":
    asyncio.run(main())
