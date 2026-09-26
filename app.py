"""
app.py - CLI Entry Point for Universal Lottery Covering & Optimization
"""

from __future__ import annotations
import argparse
import sys
import time
from core import GameConfig
from verifier import verify_coverage
from optimizer import optimize_wheel, generate_cyclic_seed_tickets

def main():
    parser = argparse.ArgumentParser(description="Universal Combinatorial Lottery Optimizer (C(v, k, t, m))")
    parser.add_argument("-v", "--universe", type=int, default=27, help="Universe size (default: 27)")
    parser.add_argument("-k", "--ticket-size", type=int, default=6, help="Ticket size (default: 6)")
    parser.add_argument("-m", "--draw-size", type=int, default=6, help="Draw size (default: 6)")
    parser.add_argument("-t", "--target", type=int, default=5, help="Guaranteed match threshold (default: 5)")
    parser.add_argument("-c", "--count", type=int, default=1, help="Minimum matching tickets (default: 1)")
    parser.add_argument("--audit-only", action="store_true", help="Audit the default 2,335 system tickets")
    parser.add_argument("--csv", type=str, default="tickets_output.csv", help="CSV export destination")
    args = parser.parse_args()

    config = GameConfig(
        universe_size=args.universe,
        ticket_size=args.ticket_size,
        draw_size=args.draw_size,
        target_k=args.target,
        min_count=args.count,
    )

    print("=" * 80)
    print(f"UNIVERSAL LOTTERY COVERING ENGINE: C({config.universe_size}, {config.ticket_size}, {config.target_k}, {config.draw_size})")
    print(f"Total Combinatorial Universe: {config.total_combinations:,} possible draws")
    print(f"Theoretical Schönheim Lower Bound: {config.schonheim_lower_bound:,} tickets")
    print("=" * 80)

    if args.audit_only:
        print("\n[AUDIT MODE] Auditing 2,335 system seed tickets against all 296,010 draws...")
        tickets = generate_cyclic_seed_tickets(v=args.universe, k=args.ticket_size)
        audit = verify_coverage(tickets, config=config, target_k=args.target, min_count=args.count)
    else:
        print("\n[OPTIMIZE MODE] Running cutting-plane optimization loop to ensure FAIL = 0...")
        result = optimize_wheel(config=config, target_k=args.target, min_count=args.count)
        tickets = result.tickets
        audit = result.verification

    print("\n" + "=" * 30 + " EXHAUSTIVE VERIFICATION AUDIT " + "=" * 30)
    print(f"Total Checked:        {audit.total_checked:,}")
    print(f"PASS Results (>= {args.target}): {audit.pass_count:,} ({audit.pass_rate}%)")
    print(f"FAIL Results:         {audit.fail_count:,} ({audit.fail_rate}%)")
    print(f"Exact 6/6 Jackpot:    {audit.draws_with_jackpot_6:,}")
    print(f"Exact 5/6 Matches:    {audit.draws_with_match_5:,}")
    print(f"Exact 4/6 Matches:    {audit.draws_with_match_4:,} (Strictly separated from 5)")
    print(f"<= 3 Matches:         {audit.draws_with_match_3_or_less:,}")
    print(f"Audit Status:         [{audit.status}]")
    print(f"Solver Status:        {audit.solver_status}")
    print(f"Execution Duration:   {audit.execution_time_seconds:.3f}s")
    print("-" * 75)

    if audit.fail_count == 0:
        print(f"✅ 100% ZERO-MISS MATHEMATICAL GUARANTEE PROVEN! (FAIL = 0)")
    else:
        print(f"⚠️  FAIL > 0 ({audit.fail_count:,} uncovered draws). Tickets do not provide 100% guarantee.")

    # Export to CSV
    with open(args.csv, "w") as f:
        f.write("PriorityRank,TicketID,Numbers\n")
        for i, t in enumerate(tickets):
            formatted = " ".join(f"{n:02d}" for n in sorted(t))
            f.write(f"{i+1},TK-{i+1:04d},\"{formatted}\"\n")
    print(f"Saved {len(tickets):,} tickets to '{args.csv}'.")
    print("=" * 80)

if __name__ == "__main__":
    main()
