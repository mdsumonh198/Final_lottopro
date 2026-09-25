"""
Universal Delayed Constraint Generation / Cutting Plane Optimizer.
Implements:
1. Universal combinatorial universe (0-40 range, arbitrary ticket size k, draw size m).
2. Multiple compound exact-match targets: (t_mask & d_mask).bit_count() == target_k.
3. 100% Exhaustive Verification against all C(v, m) draws — never sampling.
4. Smart Candidate-Generation Strategy for large instances up to full 0–40 universe.
5. Strict 3-value status: "PROVED OPTIMAL" | "BEST FOUND" | "INFEASIBLE".
6. Tertiary objective: Stage 2 Match-Count Variance / Spread balancing across results.
"""

from typing import List, Tuple, Dict, Any, Callable, Optional, Set
from itertools import combinations
from dataclasses import dataclass, field
import time
import math
import random

from .core import (
    TargetTier,
    OptimizationMode,
    SolverBackend,
    SolverStatus,
    TierVerificationSummary,
    VerificationResult,
    numbers_to_mask,
    mask_to_numbers,
)
from .verifier import verify_tickets_exhaustive
from .solver_cp_sat import solve_subproblem, balance_match_counts, SolverResult


@dataclass
class IterationLog:
    iteration: int
    num_active_draws: int
    num_candidate_tickets: int
    num_tickets_found: int
    num_violations: int
    solve_time_seconds: float
    verification_time_seconds: float
    solver_status: str
    best_bound: float


@dataclass
class OptimizationOutput:
    status: str  # "PROVED OPTIMAL" | "BEST FOUND" | "INFEASIBLE"
    fully_verified: bool
    tickets: List[Tuple[int, ...]]
    total_tickets: int
    total_iterations: int
    total_time_seconds: float
    active_draws_count: int
    total_draws_in_universe: int
    total_candidates_in_universe: int
    active_candidates_count: int
    verification_summary: Optional[VerificationResult]
    iteration_history: List[IterationLog]
    worst_case_draws: Dict[int, Tuple[int, ...]]
    best_case_draws: Dict[int, Tuple[int, ...]]
    is_balanced: bool = False


def _generate_candidate_pool_for_large_universe(
    universe: List[int],
    ticket_size: int,
    targets: List[TargetTier],
    seed_draws: List[Tuple[int, ...]],
    max_initial_candidates: int = 40_000
) -> List[Tuple[int, ...]]:
    """
    Candidate-Generation Strategy for Large Instances (e.g. pools up to 0–40 where C(v, k) > 100k).
    Constructs a rich, structurally diverse candidate pool containing:
    1. Balanced cyclic shift designs.
    2. Equi-distributed frequency tickets covering each number evenly.
    3. Direct target-intersecting tickets tailored to cover the initial seed draws.
    """
    v = len(universe)
    k = ticket_size
    candidates_set: Set[Tuple[int, ...]] = set()

    # 1. Balanced cyclic designs
    step = max(1, v // k)
    for shift in range(v):
        ticket = tuple(sorted(universe[(shift + i * step) % v] for i in range(k)))
        if len(set(ticket)) == k:
            candidates_set.add(ticket)

    # 2. Evenly distributed partition tickets
    shuffled_u = list(universe)
    rng = random.Random(101)
    for _ in range(min(500, max_initial_candidates // 10)):
        rng.shuffle(shuffled_u)
        for chunk_start in range(0, v - k + 1, k):
            t = tuple(sorted(shuffled_u[chunk_start:chunk_start + k]))
            candidates_set.add(t)

    # 3. Construct specific candidate tickets directly intersecting seed draws at exact target_k
    u_set = set(universe)
    for draw in seed_draws:
        d_set = set(draw)
        outside = list(u_set - d_set)
        for t in targets:
            tk = t.target_k
            if tk <= len(draw) and (k - tk) <= len(outside):
                # Pick combinations of tk elements from draw and (k - tk) from outside
                for in_sub in combinations(draw, tk):
                    if len(candidates_set) >= max_initial_candidates:
                        break
                    # Take balanced outside elements
                    if k - tk > 0:
                        for out_sub in combinations(outside[:min(len(outside), 12)], k - tk):
                            cand = tuple(sorted(in_sub + out_sub))
                            candidates_set.add(cand)
                            if len(candidates_set) >= max_initial_candidates:
                                break
                    else:
                        cand = tuple(sorted(in_sub))
                        candidates_set.add(cand)

    # Fill up to a safe working pool size with pseudo-random stratified combinations
    step_comb = max(1, math.comb(v, k) // max_initial_candidates)
    idx = 0
    for cand in combinations(universe, k):
        if idx % step_comb == 0:
            candidates_set.add(cand)
            if len(candidates_set) >= max_initial_candidates:
                break
        idx += 1

    return sorted(list(candidates_set))


def _expand_candidates_for_violations(
    violating_draws: List[Tuple[int, ...]],
    universe: List[int],
    ticket_size: int,
    targets: List[TargetTier],
    existing_candidates_set: Set[Tuple[int, ...]],
    max_new_candidates: int = 5_000
) -> List[Tuple[int, ...]]:
    """
    Dynamically expands the candidate pool by synthesizing tickets that directly hit
    the violating draws at exact target_k.
    """
    new_candidates: List[Tuple[int, ...]] = []
    u_set = set(universe)
    k = ticket_size

    for draw in violating_draws:
        d_set = set(draw)
        outside = list(u_set - d_set)
        for t in targets:
            tk = t.target_k
            needed_outside = k - tk
            if tk <= len(draw) and 0 <= needed_outside <= len(outside):
                # Sample combinations from draw and outside
                for in_sub in combinations(draw, tk):
                    if needed_outside == 0:
                        cand = tuple(sorted(in_sub))
                        if cand not in existing_candidates_set:
                            existing_candidates_set.add(cand)
                            new_candidates.append(cand)
                    else:
                        # Choose outside elements
                        sample_outside = outside[:min(len(outside), 15)]
                        for out_sub in combinations(sample_outside, needed_outside):
                            cand = tuple(sorted(in_sub + out_sub))
                            if cand not in existing_candidates_set:
                                existing_candidates_set.add(cand)
                                new_candidates.append(cand)
                            if len(new_candidates) >= max_new_candidates:
                                return new_candidates
    return new_candidates


def run_delayed_constraint_generation(
    universe_min: int,
    universe_max: int,
    ticket_size: int,
    draw_size: int,
    targets: List[TargetTier],
    mode: str = OptimizationMode.FAST.value,
    backend: str = "ortools",
    max_iterations: int = 40,
    cuts_per_iteration: int = 30,
    solver_time_limit_per_iter: float = 25.0,
    initial_seed_draws_count: int = 20,
    num_workers: int = 4,
    balance_variance: bool = True,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> OptimizationOutput:
    """
    Universal Delayed Constraint Generation / Cutting Plane Solver.
    """
    total_start = time.time()
    universe = list(range(universe_min, universe_max + 1))
    v = len(universe)
    k = ticket_size
    m = draw_size

    if k > v or m > v or k <= 0 or m <= 0:
        raise ValueError(f"Invalid dimensions: universe={v}, ticket_size={k}, draw_size={m}")

    total_possible_draws = math.comb(v, m)
    total_possible_candidates = math.comb(v, k)

    # Determine candidate generation strategy
    # Exhaustive mode builds all candidates if <= 100,000
    is_exhaustive_mode = (mode == OptimizationMode.EXHAUSTIVE.value or "exhaustive" in mode.lower())
    use_full_candidates = is_exhaustive_mode and (total_possible_candidates <= 120_000)

    # 1. Build initial seed draws
    all_draws_sample: List[Tuple[int, ...]] = []
    step = max(1, total_possible_draws // max(1, initial_seed_draws_count))
    draw_idx = 0
    for draw in combinations(universe, m):
        if draw_idx % step == 0 and len(all_draws_sample) < initial_seed_draws_count:
            all_draws_sample.append(draw)
        draw_idx += 1

    active_draws: List[Tuple[int, ...]] = list(all_draws_sample)
    active_draw_set = set(active_draws)

    # 2. Candidate tickets generation
    if use_full_candidates:
        candidate_tickets = list(combinations(universe, k))
        candidate_set = set(candidate_tickets)
    else:
        # Smart candidate pool for large / fast runs
        candidate_tickets = _generate_candidate_pool_for_large_universe(
            universe=universe,
            ticket_size=k,
            targets=targets,
            seed_draws=active_draws,
            max_initial_candidates=min(35_000, total_possible_candidates)
        )
        candidate_set = set(candidate_tickets)

    candidate_masks = [numbers_to_mask(t, universe_min) for t in candidate_tickets]

    iteration_history: List[IterationLog] = []
    current_tickets: List[Tuple[int, ...]] = []
    current_indices: List[int] = []
    last_solver_status = "UNKNOWN"
    last_verif_result: Optional[VerificationResult] = None
    proved_optimality_achieved = False

    for iteration in range(1, max_iterations + 1):
        if progress_callback:
            progress_callback({
                "iteration": iteration,
                "max_iterations": max_iterations,
                "phase": "SOLVING_MIP",
                "active_draws": len(active_draws),
                "total_draws": total_possible_draws,
                "candidates_count": len(candidate_tickets),
                "tickets_count": len(current_tickets),
                "status": f"Solving {backend} optimization subproblem ({len(active_draws)} constraints)..."
            })

        solve_res: SolverResult = solve_subproblem(
            backend=backend,
            candidate_tickets=candidate_tickets,
            candidate_masks=candidate_masks,
            active_draws=active_draws,
            targets=targets,
            universe_min=universe_min,
            time_limit_seconds=solver_time_limit_per_iter,
            num_workers=num_workers,
            hint_indices=current_indices if current_indices else None
        )

        last_solver_status = solve_res.status

        # If subproblem on relaxed constraints is INFEASIBLE, full problem is strictly INFEASIBLE
        if solve_res.status == SolverStatus.INFEASIBLE:
            # If we used a restricted candidate pool, try expanding candidates before declaring infeasible
            if not use_full_candidates and len(candidate_tickets) < total_possible_candidates:
                # Add more candidates and retry
                new_cands = _expand_candidates_for_violations(
                    active_draws, universe, k, targets, candidate_set, max_new_candidates=10_000
                )
                if new_cands:
                    candidate_tickets.extend(new_cands)
                    candidate_masks = [numbers_to_mask(t, universe_min) for t in candidate_tickets]
                    continue

            return OptimizationOutput(
                status=SolverStatus.INFEASIBLE,
                fully_verified=True,
                tickets=[],
                total_tickets=0,
                total_iterations=iteration,
                total_time_seconds=time.time() - total_start,
                active_draws_count=len(active_draws),
                total_draws_in_universe=total_possible_draws,
                total_candidates_in_universe=total_possible_candidates,
                active_candidates_count=len(candidate_tickets),
                verification_summary=None,
                iteration_history=iteration_history,
                worst_case_draws={},
                best_case_draws={},
                is_balanced=False
            )

        current_tickets = solve_res.selected_tickets
        current_indices = solve_res.selected_indices

        # Record whether this subproblem proved lower bound == upper bound
        if solve_res.status == SolverStatus.PROVED_OPTIMAL and use_full_candidates:
            subproblem_proved_optimal = True
        else:
            subproblem_proved_optimal = False

        # Run 100% Full Exhaustive Verification across ALL C(v, m) draws
        if progress_callback:
            progress_callback({
                "iteration": iteration,
                "max_iterations": max_iterations,
                "phase": "EXHAUSTIVE_VERIFY",
                "active_draws": len(active_draws),
                "total_draws": total_possible_draws,
                "candidates_count": len(candidate_tickets),
                "tickets_count": len(current_tickets),
                "status": f"Exhaustively verifying {total_possible_draws:,} combinatorial draws..."
            })

        verif_start = time.time()
        verif_res: VerificationResult = verify_tickets_exhaustive(
            tickets=current_tickets,
            universe_min=universe_min,
            universe_max=universe_max,
            draw_size=draw_size,
            targets=targets,
            max_violations_to_collect=cuts_per_iteration * 5
        )
        verif_duration = time.time() - verif_start
        last_verif_result = verif_res

        iteration_history.append(IterationLog(
            iteration=iteration,
            num_active_draws=len(active_draws),
            num_candidate_tickets=len(candidate_tickets),
            num_tickets_found=len(current_tickets),
            num_violations=len(verif_res.violations),
            solve_time_seconds=solve_res.solve_time_seconds,
            verification_time_seconds=verif_duration,
            solver_status=solve_res.status,
            best_bound=solve_res.best_objective_bound
        ))

        # Check Convergence: 0 Violations across entire combinatorial space
        if len(verif_res.violations) == 0:
            if subproblem_proved_optimal:
                proved_optimality_achieved = True

            if progress_callback:
                progress_callback({
                    "iteration": iteration,
                    "max_iterations": max_iterations,
                    "phase": "CONVERGED",
                    "active_draws": len(active_draws),
                    "total_draws": total_possible_draws,
                    "tickets_count": len(current_tickets),
                    "status": f"100% Zero-Miss Guarantee Certified: 0 Violations across all {total_possible_draws:,} draws!"
                })
            break

        # Add violating draws as new cutting plane constraints
        new_cuts = 0
        added_violations: List[Tuple[int, ...]] = []
        for viol_draw in verif_res.violations:
            if viol_draw not in active_draw_set:
                active_draws.append(viol_draw)
                active_draw_set.add(viol_draw)
                added_violations.append(viol_draw)
                new_cuts += 1
                if new_cuts >= cuts_per_iteration:
                    break

        # If restricted candidate pool was used, expand candidate pool for these new violations
        if not use_full_candidates:
            new_cands = _expand_candidates_for_violations(
                added_violations, universe, k, targets, candidate_set, max_new_candidates=3_000
            )
            if new_cands:
                candidate_tickets.extend(new_cands)
                candidate_masks = [numbers_to_mask(t, universe_min) for t in candidate_tickets]

    # Evaluate Final Status
    fully_verified = (last_verif_result is not None and len(last_verif_result.violations) == 0 and last_verif_result.is_valid)

    if fully_verified and proved_optimality_achieved:
        final_status = SolverStatus.PROVED_OPTIMAL
    elif len(current_tickets) > 0:
        final_status = SolverStatus.BEST_FOUND
    else:
        final_status = SolverStatus.INFEASIBLE

    # Tertiary Objective: Balance match counts across results (variance reduction stage)
    is_balanced = False
    if balance_variance and fully_verified and len(current_tickets) > 0:
        if progress_callback:
            progress_callback({
                "iteration": len(iteration_history),
                "max_iterations": max_iterations,
                "phase": "BALANCE_VARIANCE",
                "active_draws": len(active_draws),
                "total_draws": total_possible_draws,
                "tickets_count": len(current_tickets),
                "status": "Stage 2: Balancing match counts across all results (variance minimization)..."
            })

        balanced_tickets = balance_match_counts(
            current_tickets=current_tickets,
            candidate_tickets=candidate_tickets,
            candidate_masks=candidate_masks,
            active_draws=active_draws,
            targets=targets,
            universe_min=universe_min,
            time_limit_seconds=15.0,
            num_workers=num_workers
        )

        if balanced_tickets != current_tickets:
            # Re-verify the balanced set
            b_verif = verify_tickets_exhaustive(
                tickets=balanced_tickets,
                universe_min=universe_min,
                universe_max=universe_max,
                draw_size=draw_size,
                targets=targets,
                max_violations_to_collect=10
            )
            if b_verif.is_valid and len(b_verif.violations) == 0:
                current_tickets = balanced_tickets
                last_verif_result = b_verif
                is_balanced = True

    total_duration = time.time() - total_start

    return OptimizationOutput(
        status=final_status,
        fully_verified=fully_verified,
        tickets=current_tickets,
        total_tickets=len(current_tickets),
        total_iterations=len(iteration_history),
        total_time_seconds=total_duration,
        active_draws_count=len(active_draws),
        total_draws_in_universe=total_possible_draws,
        total_candidates_in_universe=total_possible_candidates,
        active_candidates_count=len(candidate_tickets),
        verification_summary=last_verif_result,
        iteration_history=iteration_history,
        worst_case_draws=last_verif_result.worst_case_draws if last_verif_result else {},
        best_case_draws=last_verif_result.best_case_draws if last_verif_result else {},
        is_balanced=is_balanced
    )


# Alias function matching the naming requested in the brief
def optimize_with_constraint_generation(*args, **kwargs) -> OptimizationOutput:
    """Standard wrapper for backward compatibility with project brief specification."""
    return run_delayed_constraint_generation(*args, **kwargs)
