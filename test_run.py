import time
import math
from src.core import TargetTier, OptimizationMode, SolverStatus
from src.optimizer import run_delayed_constraint_generation
from src.verifier import verify_tickets_exhaustive

def test_on_1_to_25():
    print("=" * 80)
    print("TEST: Exact-5 >= 1, Exact-4 >= 10, Exact-3 >= 25 on 1–25 (k=6, m=6)")
    print("=" * 80)

    targets = [
        TargetTier(target_k=5, min_count=1),
        TargetTier(target_k=4, min_count=10),
        TargetTier(target_k=3, min_count=25),
    ]

    # Let's test on 1-12 first to check exact report output
    print("\n--- TEST 1: Small Game 1–12 (k=6, m=6) ---")
    t0 = time.time()
    out12 = run_delayed_constraint_generation(
        universe_min=1,
        universe_max=12,
        ticket_size=6,
        draw_size=6,
        targets=[
            TargetTier(target_k=5, min_count=1),
            TargetTier(target_k=4, min_count=2),
            TargetTier(target_k=3, min_count=4),
        ],
        mode=OptimizationMode.FAST.value,
        backend="ortools",
        max_iterations=15,
        cuts_per_iteration=50,
        solver_time_limit_per_iter=5.0,
        balance_variance=True
    )
    print(f"Status: {out12.status}")
    print(f"Fully Verified: {out12.fully_verified}")
    print(f"Total Tickets: {out12.total_tickets}")
    print(f"Elapsed: {time.time() - t0:.2f}s")
    if out12.verification_summary:
        v = out12.verification_summary
        print(f"Draws audited: {v.total_draws_evaluated}")
        for k, summ in v.tier_summaries.items():
            print(f"  Tier exact-{summ.target_k}: Min={summ.worst_case_min} (Req >= {summ.min_count}) -> {'PASS' if summ.passed else 'FAIL'}")

if __name__ == "__main__":
    test_on_1_to_25()
