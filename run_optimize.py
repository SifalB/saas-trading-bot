"""
Search for better strategy parameters — honestly.

    python run_optimize.py --days 90 --trials 24
    python run_optimize.py --days 90 --only mtf,dip

History is split chronologically. Parameters are tuned on the TRAIN half and
then judged on a TEST half the search never saw. The TEST column is the only
one that means anything: a result that shines in TRAIN and dies in TEST is
curve-fitted, and is labelled that way rather than sold as a discovery.
"""

import argparse
import asyncio
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from backend.services import backtest, optimizer  # noqa: E402

_DATA = {}


def _init_worker(days: int, symbols: list[str], train_frac: float) -> None:
    """Each process loads the cached candles once, not once per trial."""
    import pandas as pd

    global _DATA
    data = {}
    for symbol in symbols:
        cache = backtest.CACHE_DIR / f"{symbol.replace('/', '')}_{days}d_1m.pkl"
        data[symbol] = pd.read_pickle(cache)
    train, test = optimizer.split_data(data, train_frac)
    _DATA = {"train": train, "test": test}


def _evaluate(job: tuple) -> dict:
    stype, params, half = job
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    summary = asyncio.run(backtest.run_strategy(stype, _DATA[half], params=params))
    summary["half"] = half
    return summary


async def main() -> None:
    parser = argparse.ArgumentParser(description="Optimise strategy parameters")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--trials", type=int, default=20, help="parameter sets per strategy")
    parser.add_argument("--train-frac", type=float, default=0.6)
    parser.add_argument("--only", type=str, default="", help="comma-separated strategies")
    parser.add_argument("--workers", type=int, default=0, help="0 = cpu_count-1")
    args = parser.parse_args()

    import os

    symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT"]
    print(f"Loading {args.days}d of history...")
    data = await backtest.fetch_history(symbols, args.days)

    train, test = optimizer.split_data(data, args.train_frac)
    bh_train = optimizer.buy_hold_return(train)
    bh_test = optimizer.buy_hold_return(test)

    t0 = next(iter(train.values()))
    t1 = next(iter(test.values()))
    print(f"\nTRAIN {t0['dt'].iloc[0]:%Y-%m-%d} to {t0['dt'].iloc[-1]:%Y-%m-%d} "
          f"| buy & hold {bh_train:+.2f}%")
    print(f"TEST  {t1['dt'].iloc[0]:%Y-%m-%d} to {t1['dt'].iloc[-1]:%Y-%m-%d} "
          f"| buy & hold {bh_test:+.2f}%   <- the honest benchmark")

    wanted = [s.strip() for s in args.only.split(",") if s.strip()] or \
        list(optimizer.strategies_to_optimize())

    jobs = []
    for stype in wanted:
        for params in optimizer.sample_params(stype, args.trials):
            jobs.append((stype, params, "train"))

    workers = args.workers or max(1, (os.cpu_count() or 2) - 1)
    print(f"\nSearching {len(jobs)} parameter sets across {len(wanted)} strategies "
          f"on {workers} workers...")

    results: dict[str, list[dict]] = {s: [] for s in wanted}
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker,
                             initargs=(args.days, symbols, args.train_frac)) as pool:
        for i, summary in enumerate(pool.map(_evaluate, jobs), 1):
            results[summary["strategy"]].append(summary)
            print(f"\r  {i}/{len(jobs)} evaluated", end="", flush=True)

        # Re-run each winner on data the search never touched.
        print("\n\nValidating winners on unseen data...")
        finals = []
        best_jobs = []
        for stype, runs in results.items():
            usable = [r for r in runs if r["trades"] >= 5]
            if not usable:
                finals.append({"strategy": stype, "best": None})
                continue
            best = max(usable, key=optimizer.score)
            best_jobs.append((stype, best["params"], "test"))
            finals.append({"strategy": stype, "best": best})

        tested = {}
        if best_jobs:
            for summary in pool.map(_evaluate, best_jobs):
                tested[summary["strategy"]] = summary

    header = (f"\n{'STRATEGY':<14} {'TRAIN':>9} {'TEST':>9} {'TRADES':>7} "
              f"{'PF':>6} {'MAXDD':>7}  VERDICT")
    print(header)
    print("-" * 96)

    rows = []
    for entry in finals:
        stype = entry["strategy"]
        best = entry["best"]
        if not best or stype not in tested:
            print(f"{stype:<14} {'-':>9} {'-':>9} {'-':>7} {'-':>6} {'-':>7}  "
                  f"no parameter set produced enough trades")
            continue
        t = tested[stype]
        v = optimizer.verdict(best["return_pct"], t["return_pct"], bh_test)
        pf = "inf" if t["profit_factor"] == float("inf") else f"{t['profit_factor']:.2f}"
        print(f"{stype:<14} {best['return_pct']:>+8.2f}% {t['return_pct']:>+8.2f}% "
              f"{t['trades']:>7} {pf:>6} {t['max_drawdown_pct']:>6.1f}%  {v}")
        rows.append((stype, best, t, v))

    print(f"\n{'BUY & HOLD':<14} {bh_train:>+8.2f}% {bh_test:>+8.2f}%       -      -       -  benchmark")

    winners = [r for r in rows if r[2]["return_pct"] > bh_test and r[2]["return_pct"] > 0]
    print("\n" + "=" * 96)
    if winners:
        print("Beat buy & hold on data the optimiser never saw:")
        for stype, best, t, _ in winners:
            print(f"\n  {stype}  test {t['return_pct']:+.2f}% vs benchmark {bh_test:+.2f}%")
            print(f"    {optimizer.format_params(best['params'])}")
        print("\nBefore trusting these, re-run with a different --days window. "
              "Surviving one split is encouraging, not proof.")
    else:
        print("Nothing beat buy & hold out-of-sample.")
        print("Tuning harder will not fix this — a search that only ever wins on the")
        print("data it was fitted to is finding noise, not an edge.")


if __name__ == "__main__":
    asyncio.run(main())
