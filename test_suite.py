import time
from src.core import TargetTier, OptimizationMode, SolverStatus
from src.optimizer import run_delayed_constraint_generation
from src.verifier import verify_tickets_exhaustive

def test_targets():
    print("Testing targets: exact-5 >= 1, exact-4 >= 10, exact-3 >= 25 on 1-25...")
    targets = [
        TargetTier(target_k=5, min_count=1),
        TargetTier(target_k=4, min_count=10),
        TargetTier(target_k=3, min_count=25),
    ]

    # Let's test with a small game or verify
    start = time.time()
    output = run_delayed_constraint_generation(
        universe_min=1,
        universe_max=12,
        ticket_size=6,
        draw_size=6,
        targets=[TargetTier(target_k=5, min_count=1)],
        mode=OptimizationMode.EXHAUSTIVE.value,
        backend="ortools",
        max_iterations=10,
        cuts_per_iteration=30,
        solver_time_limit_per_iter=10.0,
        balance_variance=True
    )
    print(f"1-12 finished in {time.time() - start:.2f}s:")
    print("Status:", output.status)
    print("Tickets:", output.total_tickets)
    print("Fully verified:", output.fully_verified)
    assert output.status in SolverStatus.VALID_SET

if __name__ == "__main__":
    test_targets()
