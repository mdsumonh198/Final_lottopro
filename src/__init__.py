"""
Universal Lottery / Combination Optimizer Package
"""

from .core import (
    TargetTier,
    GameConfig,
    OptimizationMode,
    SolverBackend,
    SolverStatus,
    TierVerificationSummary,
    VerificationResult,
    numbers_to_mask,
    mask_to_numbers,
    estimate_problem_complexity,
)
from .verifier import verify_tickets_exhaustive
from .solver_cp_sat import solve_subproblem, balance_match_counts, SolverResult
from .optimizer import (
    run_delayed_constraint_generation,
    optimize_with_constraint_generation,
    OptimizationOutput,
    IterationLog,
)

__all__ = [
    "TargetTier",
    "GameConfig",
    "OptimizationMode",
    "SolverBackend",
    "SolverStatus",
    "TierVerificationSummary",
    "VerificationResult",
    "numbers_to_mask",
    "mask_to_numbers",
    "estimate_problem_complexity",
    "verify_tickets_exhaustive",
    "solve_subproblem",
    "balance_match_counts",
    "SolverResult",
    "run_delayed_constraint_generation",
    "optimize_with_constraint_generation",
    "OptimizationOutput",
    "IterationLog",
]
