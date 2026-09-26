"""
src/__init__.py - Python Package Initialization
"""
from core import GameConfig, CompoundTarget, VerificationResult, OptimizationResult
from verifier import verify_coverage, verify_all_results
from solver_cp_sat import CPSatCoveringSolver
from optimizer import optimize_wheel, run_chvatal_greedy_repair, generate_cyclic_seed_tickets

__all__ = [
    "GameConfig",
    "CompoundTarget",
    "VerificationResult",
    "OptimizationResult",
    "verify_coverage",
    "verify_all_results",
    "CPSatCoveringSolver",
    "optimize_wheel",
    "run_chvatal_greedy_repair",
    "generate_cyclic_seed_tickets",
]
