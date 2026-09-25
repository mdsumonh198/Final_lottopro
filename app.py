"""
Universal Lottery / Combination Optimizer - CLI and Web Application Entry Point.

Can be run in two modes:
1. Command Line Interface (CLI):
   python3 app.py --min 1 --max 12 -k 6 -m 6 --target 5 1 --mode exhaustive --export-csv tickets.csv --export-xlsx tickets.xlsx
   python3 app.py --min 1 --max 25 -k 6 -m 6 --target 5 1 --target 4 10 --target 3 25 --mode fast

2. Streamlit Web Dashboard:
   streamlit run app.py
"""

import sys
import os
import argparse
import math
import time
from typing import List, Tuple

from src.core import (
    TargetTier,
    OptimizationMode,
    SolverBackend,
    SolverStatus,
    estimate_problem_complexity,
)
from src.optimizer import run_delayed_constraint_generation, OptimizationOutput


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Universal Combinatorial Lottery Optimizer (Cutting Plane Engine)"
    )
    parser.add_argument("--min", type=int, default=1, help="Universe minimum number (e.g. 0 or 1)")
    parser.add_argument("--max", type=int, default=12, help="Universe maximum number (e.g. 12, 25, 40)")
    parser.add_argument("-k", "--ticket-size", type=int, default=6, help="Ticket size (k)")
    parser.add_argument("-m", "--draw-size", type=int, default=6, help="Result / draw size (m)")
    parser.add_argument(
        "--target",
        nargs=2,
        action="append",
        type=int,
        metavar=("TARGET_K", "MIN_COUNT"),
        help="Target requirement: exact TARGET_K matches >= MIN_COUNT. Can be specified multiple times.",
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "exhaustive"],
        default="fast",
        help="Optimization mode: fast (heuristic, BEST FOUND likely) or exhaustive (attempt PROVED OPTIMAL)",
    )
    parser.add_argument(
        "--backend",
        choices=["ortools", "scip", "gurobi"],
        default="ortools",
        help="Optimization solver backend (default: ortools)",
    )
    parser.add_argument(
        "--balance",
        dest="balance",
        action="store_true",
        default=True,
        help="Enable Stage 2 match-count variance balancing (default: True)",
    )
    parser.add_argument(
        "--no-balance",
        dest="balance",
        action="store_false",
        help="Disable Stage 2 match-count variance balancing",
    )
    parser.add_argument("--max-iters", type=int, default=40, help="Maximum cutting plane iterations")
    parser.add_argument("--cuts-per-iter", type=int, default=30, help="Cuts added per iteration")
    parser.add_argument("--time-limit", type=float, default=30.0, help="Time limit per solver iteration (s)")
    parser.add_argument("--workers", type=int, default=4, help="Parallel worker threads")
    parser.add_argument("--export-csv", type=str, default=None, help="Export tickets to CSV file")
    parser.add_argument("--export-xlsx", type=str, default=None, help="Export tickets to Excel XLSX file")

    return parser.parse_args()


def run_cli():
    args = parse_cli_args()

    # Build targets
    if args.target:
        targets = [TargetTier(target_k=t[0], min_count=t[1]) for t in args.target]
    else:
        # Default target: exact (k-1) match >= 1
        targets = [TargetTier(target_k=max(1, args.ticket_size - 1), min_count=1)]

    mode_val = (
        OptimizationMode.EXHAUSTIVE.value
        if args.mode == "exhaustive"
        else OptimizationMode.FAST.value
    )

    print("=" * 78)
    print("🛡️  UNIVERSAL LOTTERY / COMBINATION OPTIMIZER ENGINE")
    print("=" * 78)
    print(f"Universe: [{args.min} to {args.max}] (Size: {args.max - args.min + 1})")
    print(f"Ticket Size (k): {args.ticket_size} | Draw Size (m): {args.draw_size}")
    print(f"Combinatorial universe: C({args.max - args.min + 1}, {args.draw_size}) = {math.comb(args.max - args.min + 1, args.draw_size):,} draws")
    print(f"Mode: {mode_val} | Backend: {args.backend}")
    print("Compound Targets:")
    for t in targets:
        print(f"  • Exact {t.target_k}-Match >= {t.min_count}")
    print("=" * 78)

    # Complexity pre-check
    comp = estimate_problem_complexity(args.min, args.max, args.ticket_size, args.draw_size)
    if comp.warning_message:
        print(f"\n{comp.warning_message}\n")

    def cli_progress(info):
        phase = info.get("phase", "")
        it = info.get("iteration", 0)
        status = info.get("status", "")
        print(f"[{time.strftime('%H:%M:%S')}] Iteration {it} | Phase: {phase} | {status}")

    output: OptimizationOutput = run_delayed_constraint_generation(
        universe_min=args.min,
        universe_max=args.max,
        ticket_size=args.ticket_size,
        draw_size=args.draw_size,
        targets=targets,
        mode=mode_val,
        backend=args.backend,
        max_iterations=args.max_iters,
        cuts_per_iteration=args.cuts_per_iter,
        solver_time_limit_per_iter=args.time_limit,
        num_workers=args.workers,
        balance_variance=args.balance,
        progress_callback=cli_progress,
    )

    print("\n" + "=" * 78)
    print("📊 VERIFICATION & OPTIMIZATION REPORT")
    print("=" * 78)
    print(f"SOLVER STATUS:       {output.status}")
    print(f"FULLY VERIFIED:      {output.fully_verified}")
    print(f"TOTAL TICKETS:       {output.total_tickets:,}")
    print(f"DRAWS AUDITED:       {output.total_draws_in_universe:,} (100% Exhaustive C(N, m))")
    print(f"CUTTING ITERATIONS:  {output.total_iterations}")
    print(f"TOTAL RUNTIME:       {output.total_time_seconds:.2f} seconds")
    print(f"VARIANCE BALANCED:   {output.is_balanced}")
    print("-" * 78)

    if output.verification_summary:
        verif = output.verification_summary
        print("\nEXACT MATCH TARGET TIERS AUDIT:")
        print(f"{'Target Tier':<16} | {'Min Req':<8} | {'Worst Min':<10} | {'Best Max':<10} | {'Avg':<8} | {'StdDev':<8} | {'Status'}")
        print("-" * 78)
        for tk, summ in verif.tier_summaries.items():
            st_text = "PASS" if summ.passed else "FAIL"
            print(f"Exact {summ.target_k}-Match   | >= {summ.min_count:<5} | {summ.worst_case_min:<10} | {summ.best_case_max:<10} | {summ.avg_matches:<8.2f} | {summ.std_dev:<8.2f} | {st_text}")

        print("\nALL EXACT-MATCH LEVELS DISTRIBUTION:")
        print(f"{'Match Level':<14} | {'Min Matches':<12} | {'Max Matches':<12} | {'Average':<10} | {'Std Dev':<10}")
        print("-" * 78)
        for lvl, stat in verif.all_levels_stats.items():
            print(f"Exact {stat.match_level:<8} | {stat.min_matches:<12} | {stat.max_matches:<12} | {stat.avg_matches:<10.3f} | {stat.std_dev:<10.3f}")

        print("\nWORST-CASE & BEST-CASE RESULTS:")
        for tk, summ in verif.tier_summaries.items():
            w_draw_str = " ".join(f"{x:02d}" for x in summ.worst_case_draw)
            b_draw_str = " ".join(f"{x:02d}" for x in summ.best_case_draw)
            print(f"  • Exact {tk}-Match Worst Result: [{w_draw_str}] (Hits: {summ.worst_case_min})")
            print(f"  • Exact {tk}-Match Best Result:  [{b_draw_str}] (Hits: {summ.best_case_max})")

    # Export CSV if requested
    if args.export_csv and output.tickets:
        import pandas as pd
        csv_rows = []
        for rank, ticket in enumerate(output.tickets, start=1):
            row = {"Rank": rank, "Ticket": " ".join(f"{x:02d}" for x in ticket), "Status": output.status}
            for i, val in enumerate(ticket, start=1):
                row[f"Ball_{i}"] = val
            csv_rows.append(row)
        pd.DataFrame(csv_rows).to_csv(args.export_csv, index=False)
        print(f"\n✅ Exported {output.total_tickets} tickets to CSV: {args.export_csv}")

    # Export XLSX if requested
    if args.export_xlsx and output.tickets:
        import pandas as pd
        xlsx_rows = []
        for rank, ticket in enumerate(output.tickets, start=1):
            row = {"Rank": rank, "Ticket": " ".join(f"{x:02d}" for x in ticket), "Status": output.status}
            for i, val in enumerate(ticket, start=1):
                row[f"Ball_{i}"] = val
            xlsx_rows.append(row)
        pd.DataFrame(xlsx_rows).to_excel(args.export_xlsx, index=False)
        print(f"✅ Exported {output.total_tickets} tickets to Excel (XLSX): {args.export_xlsx}")

    print("=" * 78)


def is_streamlit_runtime() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_context
        if get_script_run_context() is not None:
            return True
    except Exception:
        pass
    try:
        from streamlit.runtime import exists
        if exists():
            return True
    except Exception:
        pass
    return False


if __name__ == "__main__":
    import runpy

    # Known CLI specific options for the optimizer
    cli_flags = {"--min", "--max", "-k", "--ticket-size", "-m", "--draw-size", "--target", "--mode", "--backend", "--balance", "--no-balance", "--export-csv", "--export-xlsx"}
    has_cli_args = any(arg in cli_flags for arg in sys.argv)

    if has_cli_args and not is_streamlit_runtime():
        run_cli()
    else:
        # Streamlit web app execution - execute streamlit_app.py directly in current namespace
        st_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streamlit_app.py")
        runpy.run_path(st_path, run_name="__main__")

