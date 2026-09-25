"""
Universal Exhaustive Combinatorial Verifier for Lottery Systems.

Strict Rules:
1. Target matching is STRICTLY EXACT: (t_mask & d_mask).bit_count() == target_k.
2. 100% Worst-Case Exhaustive Guarantee: evaluates ALL C(N, m) draws in the combinatorial space.
3. Zero sampling or probabilistic approximations.
4. Comprehensive auditing: reports min, max, avg, standard deviation for EVERY exact-match level,
   plus worst-case and best-case results, and PASS/FAIL per target tier.
"""

from typing import List, Tuple, Dict, Any, Optional
from itertools import combinations
import math

from .core import (
    TargetTier,
    MatchLevelStat,
    TierVerificationSummary,
    VerificationResult,
    numbers_to_mask,
)


def verify_tickets_exhaustive(
    tickets: List[Tuple[int, ...]],
    universe_min: int,
    universe_max: int,
    draw_size: int,
    targets: List[TargetTier],
    max_violations_to_collect: int = 2000
) -> VerificationResult:
    """
    Exhaustively audits the ticket set against EVERY possible combination of draw_size (m)
    from range(universe_min, universe_max + 1).

    Computes full statistics across ALL match levels (0 to min(ticket_size, draw_size))
    and verifies whether all target tiers PASS with 100% worst-case guarantee.
    """
    if not tickets:
        # Trivial failure
        universe = list(range(universe_min, universe_max + 1))
        v = len(universe)
        total_draws = math.comb(v, draw_size) if v >= draw_size else 0
        tier_summaries = {}
        for t in targets:
            tier_summaries[t.target_k] = TierVerificationSummary(
                target_k=t.target_k,
                min_count=t.min_count,
                worst_case_min=0,
                best_case_max=0,
                avg_matches=0.0,
                std_dev=0.0,
                passed=False,
                worst_case_draw=tuple(universe[:draw_size]) if v >= draw_size else (),
                best_case_draw=tuple(universe[:draw_size]) if v >= draw_size else (),
                distribution={0: total_draws}
            )
        return VerificationResult(
            is_valid=False,
            total_draws_evaluated=total_draws,
            tier_summaries=tier_summaries,
            all_levels_stats={},
            violations=[],
            worst_case_draws={},
            best_case_draws={},
            overall_variance=0.0
        )

    min_val = universe_min
    universe = list(range(universe_min, universe_max + 1))
    v = len(universe)
    total_draws = math.comb(v, draw_size)

    ticket_k = len(tickets[0])
    max_match_level = min(ticket_k, draw_size)

    # Precompute ticket masks for high-speed hardware bitwise operations
    ticket_masks = [numbers_to_mask(t, min_val) for t in tickets]
    num_tickets = len(tickets)

    # Set up structures for EVERY exact match level [0 ... max_match_level]
    all_levels = list(range(max_match_level + 1))
    lvl_min = {lvl: num_tickets + 1 for lvl in all_levels}
    lvl_max = {lvl: -1 for lvl in all_levels}
    lvl_sum = {lvl: 0 for lvl in all_levels}
    lvl_sum_sq = {lvl: 0 for lvl in all_levels}
    lvl_worst_draw = {lvl: None for lvl in all_levels}
    lvl_best_draw = {lvl: None for lvl in all_levels}

    # Target parameters
    unique_target_ks = sorted({t.target_k for t in targets})
    target_dict = {t.target_k: t.min_count for t in targets}

    # Tracking per target tier
    tier_dist_counts = {k: {} for k in unique_target_ks}
    violations: List[Tuple[int, ...]] = []

    # Iterate through all C(v, m) draws
    for draw in combinations(universe, draw_size):
        d_mask = numbers_to_mask(draw, min_val)

        # Count exact match frequencies for this draw across all tickets
        counts_for_draw = [0] * (max_match_level + 1)

        for t_mask in ticket_masks:
            overlap = (t_mask & d_mask).bit_count()
            if overlap <= max_match_level:
                counts_for_draw[overlap] += 1

        draw_has_violation = False

        # Update all levels stats
        for lvl in all_levels:
            c = counts_for_draw[lvl]
            lvl_sum[lvl] += c
            lvl_sum_sq[lvl] += c * c

            if c < lvl_min[lvl]:
                lvl_min[lvl] = c
                lvl_worst_draw[lvl] = draw
            if c > lvl_max[lvl]:
                lvl_max[lvl] = c
                lvl_best_draw[lvl] = draw

        # Check target tiers
        for k in unique_target_ks:
            cnt = counts_for_draw[k] if k <= max_match_level else 0
            if cnt in tier_dist_counts[k]:
                tier_dist_counts[k][cnt] += 1
            elif len(tier_dist_counts[k]) < 100:
                tier_dist_counts[k][cnt] = 1

            if cnt < target_dict[k]:
                draw_has_violation = True

        if draw_has_violation:
            if len(violations) < max_violations_to_collect:
                violations.append(draw)

    # Compile all levels stats
    all_levels_stats: Dict[int, MatchLevelStat] = {}
    for lvl in all_levels:
        min_c = lvl_min[lvl] if lvl_min[lvl] <= num_tickets else 0
        max_c = lvl_max[lvl] if lvl_max[lvl] >= 0 else 0
        avg_c = lvl_sum[lvl] / total_draws if total_draws > 0 else 0.0
        # Population variance: E[X^2] - (E[X])^2
        var_c = max(0.0, (lvl_sum_sq[lvl] / total_draws) - (avg_c ** 2)) if total_draws > 0 else 0.0
        std_c = math.sqrt(var_c)

        all_levels_stats[lvl] = MatchLevelStat(
            match_level=lvl,
            min_matches=min_c,
            max_matches=max_c,
            avg_matches=round(avg_c, 3),
            std_dev=round(std_c, 3),
            worst_case_draw=lvl_worst_draw[lvl] or tuple(universe[:draw_size]),
            best_case_draw=lvl_best_draw[lvl] or tuple(universe[:draw_size]),
        )

    # Compile tier summaries
    tier_summaries: Dict[int, TierVerificationSummary] = {}
    is_valid = True
    total_target_variance = 0.0

    for k in unique_target_ks:
        req_min = target_dict[k]
        lvl_stat = all_levels_stats.get(k)
        if lvl_stat:
            actual_min = lvl_stat.min_matches
            actual_max = lvl_stat.max_matches
            avg = lvl_stat.avg_matches
            std_dev = lvl_stat.std_dev
            worst_draw = lvl_stat.worst_case_draw
            best_draw = lvl_stat.best_case_draw
        else:
            actual_min = 0
            actual_max = 0
            avg = 0.0
            std_dev = 0.0
            worst_draw = tuple(universe[:draw_size])
            best_draw = tuple(universe[:draw_size])

        passed = actual_min >= req_min
        if not passed:
            is_valid = False

        total_target_variance += (std_dev ** 2)

        tier_summaries[k] = TierVerificationSummary(
            target_k=k,
            min_count=req_min,
            worst_case_min=actual_min,
            best_case_max=actual_max,
            avg_matches=avg,
            std_dev=std_dev,
            passed=passed,
            worst_case_draw=worst_draw,
            best_case_draw=best_draw,
            distribution=tier_dist_counts[k]
        )

    return VerificationResult(
        is_valid=is_valid,
        total_draws_evaluated=total_draws,
        tier_summaries=tier_summaries,
        all_levels_stats=all_levels_stats,
        violations=violations,
        worst_case_draws={k: tier_summaries[k].worst_case_draw for k in unique_target_ks},
        best_case_draws={k: tier_summaries[k].best_case_draw for k in unique_target_ks},
        overall_variance=round(total_target_variance, 4)
    )
