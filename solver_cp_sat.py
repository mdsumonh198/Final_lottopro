"""
Solver Engine Module (Root Dispatcher)
Exports CP-SAT, SCIP, and Gurobi solvers and variance balancing from src.solver_cp_sat.
"""

from src.solver_cp_sat import (
    SolverResult,
    solve_cp_sat_subproblem,
    solve_scip_subproblem,
    solve_gurobi_subproblem,
    solve_subproblem,
    balance_match_counts,
)

__all__ = [
    "SolverResult",
    "solve_cp_sat_subproblem",
    "solve_scip_subproblem",
    "solve_gurobi_subproblem",
    "solve_subproblem",
    "balance_match_counts",
]
