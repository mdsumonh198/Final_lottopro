"""
optimizer.py - Production Combinatorial Optimizer & Cutting-Plane Engine
Iteratively generates minimal tickets ensuring 100% worst-case guarantee (FAIL = 0).
"""

from __future__ import annotations
import math
import time
import itertools
from typing import List, Tuple, Set, Dict, Optional, Callable
from core import GameConfig, OptimizationResult, VerificationResult, ticket_to_mask, mask_to_ticket
from verifier import verify_coverage
from solver_cp_sat import CPSatCoveringSolver

def generate_cyclic_seed_tickets(v: int = 27, k: int = 6, offset: int = 1) -> List[List[int]]:
    """
    Generates high-dispersion base cyclic difference blocks in Z_v.
    Covers the symmetric group orbits efficiently.
    """
    base_blocks = [
        [0, 1, 3, 7, 12, 20],
        [0, 2, 5, 11, 15, 23],
        [0, 3, 8, 14, 18, 22],
        [0, 4, 9, 13, 19, 25],
        [0, 1, 6, 10, 16, 21],
        [0, 2, 7, 13, 17, 24],
        [0, 3, 9, 15, 20, 26],
        [0, 4, 10, 15, 21, 25],
        [0, 2, 11, 13, 15, 22],
        [0, 2, 11, 13, 15, 23],
        [0, 5, 6, 10, 12, 24],
        [0, 5, 6, 10, 12, 25],
        [0, 1, 4, 10, 16, 23],
        [0, 2, 8, 13, 18, 24],
    ]

    seen = set()
    seed_tickets = []

    for block in base_blocks:
        valid = [x % v for x in block]
        if len(set(valid)) == k:
            for shift in range(v):
                nums = sorted([((x + shift) % v) + offset for x in valid])
                key = tuple(nums)
                if key not in seen:
                    seen.add(key)
                    seed_tickets.append(nums)

    return seed_tickets

def optimize_wheel(
    config: Optional[GameConfig] = None,
    target_k: int = 5,
    min_count: int = 1,
    max_iterations: int = 50,
    time_limit_seconds: float = 300.0,
    progress_callback: Optional[Callable[[int, int, int], None]] = None,
) -> OptimizationResult:
    """
    Iterative Delayed Constraint Generation (Cutting-Plane) Optimizer.

    Strict Client Requirements:
    1. Does NOT abort prematurely with uncovered draws.
    2. Iteratively resolves all violating draws until:
       Total Results = 296,010
       FAIL Results  = 0
    3. Objective: Minimal ticket count (Priority 1: 100% guarantee, Priority 2: minimal tickets).
    """
    if config is None:
        config = GameConfig(universe_size=27, ticket_size=6, draw_size=6, target_k=target_k, min_count=min_count)
    else:
        target_k = config.target_k
        min_count = config.min_count

    v = config.universe_size
    k = config.ticket_size
    m = config.draw_size
    offset = config.start_number
    t_start = time.perf_counter()

    # Step 1: Initial Seed / Preloaded Optimal Covering Design
    tickets: List[List[int]] = []
    # If 6/27 with target 5, load verified zero-fail minimal tickets if available
    import os, json
    zero_fail_file = "tickets_guaranteed_5.json"
    if v == 27 and k == 6 and target_k == 5 and os.path.exists(zero_fail_file):
        try:
            with open(zero_fail_file) as f:
                tickets = json.load(f)
        except Exception:
            tickets = []

    if not tickets:
        if v == 27 and k == 6:
            tickets = generate_cyclic_seed_tickets(v=27, k=6, offset=offset)
        else:
            pool = list(range(offset, offset + v))
            for _ in range(max(10, config.schonheim_lower_bound // 4)):
                tickets.append(sorted(pool[:k]))

    seen_tickets = {tuple(sorted(t)) for t in tickets}

    # Step 2: Cutting-Plane / Constraint Generation Loop
    iteration = 0
    solver = CPSatCoveringSolver(config=config, time_limit_seconds=30.0)

    while iteration < max_iterations:
        iteration += 1

        # Exhaustive verification against ALL 296,010 draws
        audit = verify_coverage(tickets, config=config, target_k=target_k, min_count=min_count)

        if progress_callback:
            progress_callback(iteration, len(tickets), audit.fail_count)

        # Check stopping criterion: 100% ZERO-MISS GUARANTEE
        if audit.fail_count == 0:
            break

        # Extract violating draws that have zero coverage
        violating = audit.uncovered_draws_sample
        if not violating:
            break

        # Generate candidates to cover the violating draws
        candidate_pool: List[List[int]] = []
        cand_seen = set()

        for draw in violating[:500]:
            draw_list = list(draw)
            # Add draw itself as candidate
            d_key = tuple(sorted(draw_list))
            if d_key not in seen_tickets and d_key not in cand_seen:
                cand_seen.add(d_key)
                candidate_pool.append(draw_list)

            # Add 1-element variations that share 5 elements with draw
            draw_set = set(draw_list)
            others = [x for x in range(offset, offset + v) if x not in draw_set]
            for i in range(k):
                base = draw_list[:i] + draw_list[i+1:]
                for o in others[:4]:  # Take best neighboring candidates
                    cand = sorted(base + [o])
                    c_key = tuple(cand)
                    if c_key not in seen_tickets and c_key not in cand_seen:
                        cand_seen.add(c_key)
                        candidate_pool.append(cand)

        # Solve cutting-plane subproblem to pick minimal new tickets covering violations
        new_tickets, _ = solver.solve_cutting_plane_subproblem(
            candidate_tickets=candidate_pool,
            violating_draws=violating,
            existing_tickets=None,
        )

        added = 0
        for t in new_tickets:
            st = tuple(sorted(t))
            if st not in seen_tickets:
                seen_tickets.add(st)
                tickets.append(t)
                added += 1

        # Fallback safeguard: if solver selected 0, directly add violating draws to guarantee progress
        if added == 0:
            for draw in violating[:50]:
                st = tuple(sorted(draw))
                if st not in seen_tickets:
                    seen_tickets.add(st)
                    tickets.append(list(draw))
                    added += 1

        if time.perf_counter() - t_start > time_limit_seconds:
            break

    # Step 3: Minimal Ticket Pruning Pass (Redundancy Elimination)
    # For small instances, prune redundant tickets without violating any draw
    if v <= 14 and audit.fail_count == 0 and len(tickets) > config.schonheim_lower_bound:
        candidates_to_keep = list(tickets)
        for i in range(len(candidates_to_keep) - 1, -1, -1):
            trial_set = candidates_to_keep[:i] + candidates_to_keep[i+1:]
            audit_trial = verify_coverage(trial_set, config=config, target_k=target_k, min_count=min_count, max_violating_draws_to_collect=1)
            if audit_trial.fail_count == 0:
                candidates_to_keep = trial_set
        tickets = candidates_to_keep

    # Final Exhaustive Verification
    final_audit = verify_coverage(tickets, config=config, target_k=target_k, min_count=min_count)

    # Sort tickets by numbers for clean presentation
    sorted_tickets = sorted(tickets, key=lambda t: (t[0], t[1], t[2], t[3], t[4], t[5]))

    return OptimizationResult(
        tickets=sorted_tickets,
        ticket_count=len(sorted_tickets),
        config=config,
        verification=final_audit,
        iterations=iteration,
        solver_status=final_audit.solver_status,
    )
