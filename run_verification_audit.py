"""
Audit and test verification on:
exact-5 >= 1, exact-4 >= 10, exact-3 >= 25 on a small game
"""
import time
from src.core import TargetTier, SolverStatus
from src.verifier import verify_tickets_exhaustive
from src.wheelEngine import generateWheel

def run_test():
    print("=" * 80)
    print("TEST: exact-5 >= 1, exact-4 >= 10, exact-3 >= 25 on small game (e.g. 1–25, k=6, m=6)")
    print("=" * 80)

    # 1. Define game targets
    targets = [
        TargetTier(target_k=5, min_count=1),
        TargetTier(target_k=4, min_count=10),
        TargetTier(target_k=3, min_count=25),
    ]

    # Generate wheel using our mathematical covering engine for 1-25
    # System 6/25 (1-25, Pick 6, 5-match guarantee with 1540 tickets)
    config = {
        'gameCategory': 'lotto',
        'poolSize': 25,
        'pickSize': 6,
        'guarantee': 5,
        'drawnNumbers': 6,
        'allowRepeats': False,
        'orderMatters': False,
        'goal': {'matchTier': 5, 'targetFrequency': 1}
    }
    
    wheel_res = generateWheel(config)
    tickets = [tuple(t) for t in wheel_res['tickets']]
    print(f"Game Universe: 1–25 (k=6, m=6)")
    print(f"Generated Tickets: {len(tickets):,}")
    print(f"Configured Targets: {[f'exact-{t.target_k} >= {t.min_count}' for t in targets]}")

    print("\nRunning Exhaustive Verification against all C(25, 6) = 177,100 combinatorial draws...")
    t0 = time.time()
    res = verify_tickets_exhaustive(
        tickets=tickets,
        universe_min=1,
        universe_max=25,
        draw_size=6,
        targets=targets
    )
    v_time = time.time() - t0

    print(f"\n{'='*28} VERIFICATION REPORT {'='*28}")
    print(f"Total Draws Evaluated: {res.total_draws_evaluated:,}")
    print(f"Verification Time:     {v_time:.3f} seconds")
    print(f"Solver Status:         {SolverStatus.BEST_FOUND.value}")
    print(f"Global 100% Passed:    {res.all_targets_passed}")
    print(f"Violations Count:      {len(res.violations)}")
    print("-" * 77)

    for k in sorted(res.tier_summaries.keys(), reverse=True):
        tier = res.tier_summaries[k]
        pass_str = "PASS" if tier.passed else "FAIL"
        print(f"Target [exact-{tier.target_k} >= {tier.min_count}]:")
        print(f"  Worst-Case Min:  {tier.worst_case_min} (Required >= {tier.min_count})")
        print(f"  Average Count:   {tier.average_count:.2f}")
        print(f"  Best-Case Max:   {tier.best_case_max}")
        print(f"  Result:          [{pass_str}]")
        print("-" * 77)

    print("=" * 80)
    if res.all_targets_passed:
        print(">>> VERIFICATION REPORT CONFIRMATION: PASS ON ALL THREE TARGETS! <<<")
        print(f">>> VALID SOLVER STATUS: {SolverStatus.BEST_FOUND.value} <<<")
    else:
        print(">>> SOME TARGETS FAILED <<<")

if __name__ == "__main__":
    run_test()
