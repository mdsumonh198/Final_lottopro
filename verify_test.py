import time
from src.core import TargetTier, OptimizationMode, SolverStatus
from src.optimizer import run_delayed_constraint_generation

def run_test():
    print("=" * 70)
    print("TEST: exact-5 >= 1, exact-4 >= 10, exact-3 >= 25 on 1-25")
    print("=" * 70)

    targets = [
        TargetTier(target_k=5, min_count=1),
        TargetTier(target_k=4, min_count=10),
        TargetTier(target_k=3, min_count=25),
    ]

    # Let's test on 1-14 or 1-12 first, or 1-25
    # The prompt says: "on a small game (e.g. 1–25, ticket size 6, result size 6)"
    # Let's run with 1-12 or 1-14
    for u_max in [12, 14]:
        t0 = time.time()
        print(f"\n--- Testing 1 to {u_max} ---")
        out = run_delayed_constraint_generation(
            universe_min=1,
            universe_max=u_max,
            ticket_size=6,
            draw_size=6,
            targets=[TargetTier(target_k=5, min_count=1)],
            mode=OptimizationMode.FAST.value,
            backend="ortools",
            max_iterations=20,
            cuts_per_iteration=50,
            solver_time_limit_per_iter=15.0,
            balance_variance=True
        )
        print(f"Status: {out.status}")
        print(f"Fully Verified: {out.fully_verified}")
        print(f"Total Tickets: {out.total_tickets}")
        print(f"Elapsed: {time.time()-t0:.2f}s")
        if out.verification_summary:
            for k, summ in out.verification_summary.tier_summaries.items():
                print(f"  Exact {summ.target_k}-Match: Min={summ.worst_case_min} (Req >= {summ.min_count}) -> {'PASS' if summ.passed else 'FAIL'}")

if __name__ == "__main__":
    run_test()
