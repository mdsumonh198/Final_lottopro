"""
optimizer.py - Production Combinatorial Optimizer & Chvátal Greedy Set Cover Engine
Iteratively generates minimal tickets ensuring 100% worst-case guarantee (FAIL = 0).
"""

from __future__ import annotations
import math
import time
import os
import json
import itertools
from typing import List, Tuple, Set, Dict, Optional, Callable
from core import GameConfig, OptimizationResult, VerificationResult, ticket_to_mask, mask_to_ticket
from verifier import verify_coverage, verify_all_results

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

def run_chvatal_greedy_repair(
    seed_tickets: List[List[int]],
    config: Optional[GameConfig] = None,
    progress_callback: Optional[Callable[[int, int, int], None]] = None,
) -> List[List[int]]:
    """
    Chvátal's Greedy Set Cover loop starting from the current seeds:
    1. Identifies the exact uncovered draws as a bitmask set.
    2. Iteratively evaluates candidate tickets that cover the maximum remaining uncovered draws.
    3. Greedily appends the best tickets to the wheel until the uncovered set is STRICTLY EMPTY (len(uncovered) == 0).
    4. Prunes redundant tickets that do not violate coverage.
    """
    if config is None:
        config = GameConfig(universe_size=27, ticket_size=6, draw_size=6, target_k=5, min_count=1)

    v = config.universe_size
    k = config.ticket_size
    offset = config.start_number
    target_k = config.target_k

    # Generate all draws
    draws = list(itertools.combinations(range(offset, offset + v), config.draw_size))
    draw_index = {d: i for i, d in enumerate(draws)}
    N = len(draws)

    tickets = [list(t) for t in seed_tickets]

    # Pre-index 5-subsets of initial seeds
    covered = bytearray(N)
    covered_5 = set()
    for t in tickets:
        for s5 in itertools.combinations(sorted(t), 5):
            covered_5.add(s5)

    covered_count = 0
    uncovered_indices = []
    for i, d in enumerate(draws):
        if any(s5 in covered_5 for s5 in itertools.combinations(d, 5)):
            covered[i] = 1
            covered_count += 1
        else:
            uncovered_indices.append(i)

    def get_covered_draws(cand: Iterable[int]) -> List[int]:
        cand_list = list(cand)
        cand_set = set(cand_list)
        cand_others = [x for x in range(offset, offset + v) if x not in cand_set]
        res = [draw_index[tuple(sorted(cand_list))]]
        for i in range(k):
            base = cand_list[:i] + cand_list[i+1:]
            for o in cand_others:
                res.append(draw_index[tuple(sorted(base + [o]))])
        return res

    # Chvatal Greedy Loop
    step = 0
    while uncovered_indices:
        while uncovered_indices and covered[uncovered_indices[-1]]:
            uncovered_indices.pop()
        if not uncovered_indices:
            break

        target_idx = uncovered_indices[-1]
        target_draw = draws[target_idx]

        target_set = set(target_draw)
        others = [x for x in range(offset, offset + v) if x not in target_set]

        # Candidates: target_draw itself + 1-element variations
        candidates = [target_draw]
        for i in range(k):
            base = list(target_draw[:i] + target_draw[i+1:])
            for o in others[:6]:
                candidates.append(tuple(sorted(base + [o])))

        best_cand = target_draw
        best_gain = 0
        best_cov_draws: List[int] = []

        for cand in candidates:
            cov_draws = get_covered_draws(cand)
            gain = sum(1 for d_idx in cov_draws if not covered[d_idx])
            if gain > best_gain:
                best_gain = gain
                best_cand = cand
                best_cov_draws = cov_draws

        tickets.append(list(best_cand))
        for d_idx in best_cov_draws:
            if not covered[d_idx]:
                covered[d_idx] = 1
                covered_count += 1

        step += 1
        if progress_callback and step % 500 == 0:
            progress_callback(step, len(tickets), N - covered_count)

    # Step 4: Redundancy Pruning Pass
    coverage_counts = [0] * N
    ticket_to_draws = []
    for t in tickets:
        cov = get_covered_draws(t)
        ticket_to_draws.append(cov)
        for d_idx in cov:
            coverage_counts[d_idx] += 1

    pruned_tickets: List[List[int]] = []
    for t_idx, t in enumerate(tickets):
        cov = ticket_to_draws[t_idx]
        can_prune = all(coverage_counts[d_idx] > 1 for d_idx in cov)
        if can_prune:
            for d_idx in cov:
                coverage_counts[d_idx] -= 1
        else:
            pruned_tickets.append(t)

    return sorted(pruned_tickets, key=lambda t: (t[0], t[1], t[2], t[3], t[4], t[5]))

def optimize_wheel(
    config: Optional[GameConfig] = None,
    target_k: int = 5,
    min_count: int = 1,
    max_iterations: int = 50,
    time_limit_seconds: float = 300.0,
    progress_callback: Optional[Callable[[int, int, int], None]] = None,
) -> OptimizationResult:
    """
    Main entry point: Generates minimal tickets ensuring 100% guarantee (FAIL = 0).
    """
    if config is None:
        config = GameConfig(universe_size=27, ticket_size=6, draw_size=6, target_k=target_k, min_count=min_count)
    else:
        target_k = config.target_k
        min_count = config.min_count

    v = config.universe_size
    k = config.ticket_size

    # Load verified zero-gap tickets if available on disk
    zero_fail_file = "tickets_chvatal_minimal.json"
    if v == 27 and k == 6 and target_k == 5 and os.path.exists(zero_fail_file):
        try:
            with open(zero_fail_file) as f:
                tickets = json.load(f)
        except Exception:
            tickets = []
    else:
        tickets = []

    if not tickets:
        # Load seeds from 2335 or generate cyclic seeds
        seeds_file = "tickets_2335.json"
        if os.path.exists(seeds_file):
            with open(seeds_file) as f:
                seeds = json.load(f)
        else:
            seeds = generate_cyclic_seed_tickets(v=v, k=k)

        tickets = run_chvatal_greedy_repair(seeds, config=config, progress_callback=progress_callback)
        try:
            with open(zero_fail_file, "w") as f:
                json.dump(tickets, f)
        except Exception:
            pass

    # Exhaustive verification of all 296,010 draws
    final_audit = verify_all_results(tickets, config=config, target_k=target_k, min_count=min_count)

    return OptimizationResult(
        tickets=tickets,
        ticket_count=len(tickets),
        config=config,
        verification=final_audit,
        iterations=1,
        solver_status=final_audit.solver_status,
    )
