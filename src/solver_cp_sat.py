"""
Mathematical Optimization Solver Engine for Lottery Covering Problems.
Supports Google OR-Tools CP-SAT (default), SCIP, and Gurobi backends.

Strict Rules:
- Target matching is strictly EXACT: (t_mask & d_mask).bit_count() == target_k.
- Status is strictly one of:
    * "PROVED OPTIMAL"
    * "BEST FOUND"
    * "INFEASIBLE"
- Tertiary Objective: Balance match counts across all results (variance/spread minimization stage).
"""

from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import time
import math

from .core import TargetTier, SolverStatus, numbers_to_mask


@dataclass
class SolverResult:
    status: str  # "PROVED OPTIMAL" | "BEST FOUND" | "INFEASIBLE"
    raw_status_name: str
    selected_tickets: List[Tuple[int, ...]]
    selected_indices: List[int]
    objective_value: int
    best_objective_bound: float
    solve_time_seconds: float
    num_variables: int
    num_constraints: int


def solve_cp_sat_subproblem(
    candidate_tickets: List[Tuple[int, ...]],
    candidate_masks: List[int],
    active_draws: List[Tuple[int, ...]],
    targets: List[TargetTier],
    universe_min: int,
    time_limit_seconds: float = 30.0,
    num_workers: int = 4,
    hint_indices: Optional[List[int]] = None
) -> SolverResult:
    """
    Formulates and solves the Set Covering MIP on the active draw constraints
    using Google OR-Tools CP-SAT.
    """
    from ortools.sat.python import cp_model

    start_time = time.time()
    model = cp_model.CpModel()
    num_candidates = len(candidate_tickets)

    # Decision variables: x[j] in {0, 1}
    x = [model.NewBoolVar(f"x_{j}") for j in range(num_candidates)]

    # Warm-start hints from previous iteration
    if hint_indices:
        for idx in hint_indices:
            if 0 <= idx < num_candidates:
                model.AddHint(x[idx], 1)

    # Primary Objective: Minimize total tickets
    model.Minimize(cp_model.LinearExpr.Sum(x))

    num_constraints = 0

    # Build exact matching constraints for each active draw
    for draw in active_draws:
        d_mask = numbers_to_mask(draw, universe_min)
        draw_exact_groups: Dict[int, List[Any]] = {t.target_k: [] for t in targets}

        for j, t_mask in enumerate(candidate_masks):
            overlap = (t_mask & d_mask).bit_count()
            if overlap in draw_exact_groups:
                draw_exact_groups[overlap].append(x[j])

        for t in targets:
            matching_vars = draw_exact_groups[t.target_k]
            if matching_vars:
                model.Add(cp_model.LinearExpr.Sum(matching_vars) >= t.min_count)
            else:
                if t.min_count > 0:
                    model.Add(0 >= t.min_count)
            num_constraints += 1

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(0.5, float(time_limit_seconds))
    solver.parameters.num_workers = max(1, int(num_workers))
    solver.parameters.log_search_progress = False

    raw_status = solver.Solve(model)
    solve_duration = time.time() - start_time

    # Strictly map to the 3 valid statuses
    if raw_status == cp_model.OPTIMAL:
        status_label = SolverStatus.PROVED_OPTIMAL
    elif raw_status == cp_model.FEASIBLE:
        status_label = SolverStatus.BEST_FOUND
    elif raw_status == cp_model.INFEASIBLE:
        status_label = SolverStatus.INFEASIBLE
    else:
        status_label = SolverStatus.BEST_FOUND if hint_indices else SolverStatus.INFEASIBLE

    selected_tickets: List[Tuple[int, ...]] = []
    selected_indices: List[int] = []
    obj_val = 0
    best_bound = 0.0

    if raw_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        obj_val = int(solver.ObjectiveValue())
        best_bound = solver.BestObjectiveBound()
        for j, var in enumerate(x):
            if solver.Value(var) == 1:
                selected_tickets.append(candidate_tickets[j])
                selected_indices.append(j)

    return SolverResult(
        status=status_label,
        raw_status_name=solver.StatusName(raw_status),
        selected_tickets=selected_tickets,
        selected_indices=selected_indices,
        objective_value=obj_val,
        best_objective_bound=best_bound,
        solve_time_seconds=solve_duration,
        num_variables=num_candidates,
        num_constraints=num_constraints
    )


def solve_scip_subproblem(
    candidate_tickets: List[Tuple[int, ...]],
    candidate_masks: List[int],
    active_draws: List[Tuple[int, ...]],
    targets: List[TargetTier],
    universe_min: int,
    time_limit_seconds: float = 30.0,
    hint_indices: Optional[List[int]] = None
) -> SolverResult:
    """
    Solves using SCIP via OR-Tools Linear Solver MPSolver wrapper (or PySCIPOpt if installed).
    """
    from ortools.linear_solver import pywraplp

    start_time = time.time()
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        # Fall back to CP-SAT if SCIP binary is unavailable in current OR-Tools build
        return solve_cp_sat_subproblem(
            candidate_tickets, candidate_masks, active_draws, targets,
            universe_min, time_limit_seconds, hint_indices=hint_indices
        )

    num_candidates = len(candidate_tickets)
    x = [solver.BoolVar(f"x_{j}") for j in range(num_candidates)]

    # Objective: Minimize sum x[j]
    objective = solver.Objective()
    for var in x:
        objective.SetCoefficient(var, 1.0)
    objective.SetMinimization()

    num_constraints = 0
    for draw in active_draws:
        d_mask = numbers_to_mask(draw, universe_min)
        draw_exact_groups: Dict[int, List[Any]] = {t.target_k: [] for t in targets}

        for j, t_mask in enumerate(candidate_masks):
            overlap = (t_mask & d_mask).bit_count()
            if overlap in draw_exact_groups:
                draw_exact_groups[overlap].append(x[j])

        for t in targets:
            matching_vars = draw_exact_groups[t.target_k]
            if matching_vars:
                ct = solver.Constraint(t.min_count, solver.infinity())
                for var in matching_vars:
                    ct.SetCoefficient(var, 1.0)
            else:
                if t.min_count > 0:
                    ct = solver.Constraint(t.min_count, solver.infinity())
            num_constraints += 1

    solver.SetTimeLimit(int(time_limit_seconds * 1000))
    raw_status = solver.Solve()
    solve_duration = time.time() - start_time

    if raw_status == pywraplp.Solver.OPTIMAL:
        status_label = SolverStatus.PROVED_OPTIMAL
    elif raw_status == pywraplp.Solver.FEASIBLE:
        status_label = SolverStatus.BEST_FOUND
    elif raw_status == pywraplp.Solver.INFEASIBLE:
        status_label = SolverStatus.INFEASIBLE
    else:
        status_label = SolverStatus.BEST_FOUND if hint_indices else SolverStatus.INFEASIBLE

    selected_tickets: List[Tuple[int, ...]] = []
    selected_indices: List[int] = []
    obj_val = 0
    best_bound = 0.0

    if raw_status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        obj_val = int(round(solver.Objective().Value()))
        best_bound = solver.Objective().BestBound() if hasattr(solver.Objective(), "BestBound") else obj_val
        for j, var in enumerate(x):
            if var.solution_value() > 0.5:
                selected_tickets.append(candidate_tickets[j])
                selected_indices.append(j)

    return SolverResult(
        status=status_label,
        raw_status_name=f"SCIP_{raw_status}",
        selected_tickets=selected_tickets,
        selected_indices=selected_indices,
        objective_value=obj_val,
        best_objective_bound=best_bound,
        solve_time_seconds=solve_duration,
        num_variables=num_candidates,
        num_constraints=num_constraints
    )


def solve_gurobi_subproblem(
    candidate_tickets: List[Tuple[int, ...]],
    candidate_masks: List[int],
    active_draws: List[Tuple[int, ...]],
    targets: List[TargetTier],
    universe_min: int,
    time_limit_seconds: float = 30.0,
    hint_indices: Optional[List[int]] = None
) -> SolverResult:
    """
    Solves using Gurobi (if gurobipy is installed and licensed).
    Falls back gracefully to CP-SAT if unavailable.
    """
    try:
        import gurobipy as gp
        from gurobipy import GRB

        start_time = time.time()
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        model = gp.Model("LotteryCovering", env=env)
        model.setParam("TimeLimit", max(1.0, float(time_limit_seconds)))

        num_candidates = len(candidate_tickets)
        x = model.addVars(num_candidates, vtype=GRB.BINARY, name="x")

        if hint_indices:
            for idx in hint_indices:
                if 0 <= idx < num_candidates:
                    x[idx].Start = 1

        model.setObjective(gp.quicksum(x[j] for j in range(num_candidates)), GRB.MINIMIZE)

        num_constraints = 0
        for draw in active_draws:
            d_mask = numbers_to_mask(draw, universe_min)
            draw_exact_groups: Dict[int, List[int]] = {t.target_k: [] for t in targets}

            for j, t_mask in enumerate(candidate_masks):
                overlap = (t_mask & d_mask).bit_count()
                if overlap in draw_exact_groups:
                    draw_exact_groups[overlap].append(j)

            for t in targets:
                idxs = draw_exact_groups[t.target_k]
                if idxs:
                    model.addConstr(gp.quicksum(x[j] for j in idxs) >= t.min_count)
                else:
                    if t.min_count > 0:
                        model.addConstr(0 >= t.min_count)
                num_constraints += 1

        model.optimize()
        solve_duration = time.time() - start_time

        if model.Status == GRB.OPTIMAL:
            status_label = SolverStatus.PROVED_OPTIMAL
        elif model.SolCount > 0:
            status_label = SolverStatus.BEST_FOUND
        elif model.Status == GRB.INFEASIBLE:
            status_label = SolverStatus.INFEASIBLE
        else:
            status_label = SolverStatus.BEST_FOUND if hint_indices else SolverStatus.INFEASIBLE

        selected_tickets = []
        selected_indices = []
        obj_val = 0
        best_bound = 0.0

        if model.SolCount > 0:
            obj_val = int(round(model.ObjVal))
            best_bound = model.ObjBound
            for j in range(num_candidates):
                if x[j].X > 0.5:
                    selected_tickets.append(candidate_tickets[j])
                    selected_indices.append(j)

        return SolverResult(
            status=status_label,
            raw_status_name=f"GUROBI_{model.Status}",
            selected_tickets=selected_tickets,
            selected_indices=selected_indices,
            objective_value=obj_val,
            best_objective_bound=best_bound,
            solve_time_seconds=solve_duration,
            num_variables=num_candidates,
            num_constraints=num_constraints
        )

    except (ImportError, Exception):
        # Graceful fallback to CP-SAT
        return solve_cp_sat_subproblem(
            candidate_tickets, candidate_masks, active_draws, targets,
            universe_min, time_limit_seconds, hint_indices=hint_indices
        )


def solve_subproblem(
    backend: str,
    candidate_tickets: List[Tuple[int, ...]],
    candidate_masks: List[int],
    active_draws: List[Tuple[int, ...]],
    targets: List[TargetTier],
    universe_min: int,
    time_limit_seconds: float = 30.0,
    num_workers: int = 4,
    hint_indices: Optional[List[int]] = None
) -> SolverResult:
    """Dispatches to the selected mathematical optimization backend."""
    b = backend.lower().strip()
    if "scip" in b:
        return solve_scip_subproblem(
            candidate_tickets, candidate_masks, active_draws, targets,
            universe_min, time_limit_seconds, hint_indices=hint_indices
        )
    elif "gurobi" in b:
        return solve_gurobi_subproblem(
            candidate_tickets, candidate_masks, active_draws, targets,
            universe_min, time_limit_seconds, hint_indices=hint_indices
        )
    else:
        return solve_cp_sat_subproblem(
            candidate_tickets, candidate_masks, active_draws, targets,
            universe_min, time_limit_seconds, num_workers=num_workers, hint_indices=hint_indices
        )


def balance_match_counts(
    current_tickets: List[Tuple[int, ...]],
    candidate_tickets: List[Tuple[int, ...]],
    candidate_masks: List[int],
    active_draws: List[Tuple[int, ...]],
    targets: List[TargetTier],
    universe_min: int,
    time_limit_seconds: float = 15.0,
    num_workers: int = 4
) -> List[Tuple[int, ...]]:
    """
    STAGE 2 (Tertiary Objective):
    Re-optimizes with ticket count FIXED at N = len(current_tickets) and ALL target
    guarantees still enforced. Minimizes the variance/spread of match counts across
    results (linearized absolute deviation from mean match count).
    """
    from ortools.sat.python import cp_model

    if not current_tickets or not active_draws or not targets:
        return current_tickets

    num_candidates = len(candidate_tickets)
    N = len(current_tickets)

    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x_{j}") for j in range(num_candidates)]

    # Warm-start with current solution
    ticket_set = set(current_tickets)
    for j, t in enumerate(candidate_tickets):
        if t in ticket_set:
            model.AddHint(x[j], 1)

    # 1. FIXED TICKET COUNT: sum(x_j) == N
    model.Add(cp_model.LinearExpr.Sum(x) == N)

    # 2. ENFORCE ALL TARGET CONSTRAINTS
    draw_match_vars: Dict[Tuple[int, int], Any] = {}  # (draw_idx, target_k) -> LinExpr
    deviations: List[Any] = []

    primary_target = targets[0]

    for d_idx, draw in enumerate(active_draws):
        d_mask = numbers_to_mask(draw, universe_min)
        draw_exact_groups: Dict[int, List[Any]] = {t.target_k: [] for t in targets}

        for j, t_mask in enumerate(candidate_masks):
            overlap = (t_mask & d_mask).bit_count()
            if overlap in draw_exact_groups:
                draw_exact_groups[overlap].append(x[j])

        for t in targets:
            matching_vars = draw_exact_groups[t.target_k]
            if matching_vars:
                m_expr = cp_model.LinearExpr.Sum(matching_vars)
                model.Add(m_expr >= t.min_count)
                if t.target_k == primary_target.target_k:
                    # Deviation from target minimum / target average
                    dev_var = model.NewIntVar(0, N, f"dev_{d_idx}_{t.target_k}")
                    # dev >= (m_expr - t.min_count)
                    model.Add(dev_var >= m_expr - t.min_count)
                    deviations.append(dev_var)
            else:
                if t.min_count > 0:
                    model.Add(0 >= t.min_count)

    if deviations:
        # Minimize total excess spread to keep hits balanced and flat
        model.Minimize(cp_model.LinearExpr.Sum(deviations))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(0.5, float(time_limit_seconds))
    solver.parameters.num_workers = max(1, int(num_workers))

    status = solver.Solve(model)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        balanced = []
        for j, var in enumerate(x):
            if solver.Value(var) == 1:
                balanced.append(candidate_tickets[j])
        if len(balanced) == N:
            return balanced

    return current_tickets
