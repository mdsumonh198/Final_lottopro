"""
Core data types, mathematical definitions, bitmask helpers, and complexity estimators
for the Universal Lottery / Combination Optimizer.
"""

from typing import List, Tuple, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import math


class SolverStatus:
    PROVED_OPTIMAL = "PROVED OPTIMAL"
    BEST_FOUND = "BEST FOUND"
    INFEASIBLE = "INFEASIBLE"

    VALID_SET = {PROVED_OPTIMAL, BEST_FOUND, INFEASIBLE}

    @classmethod
    def validate(cls, status: str) -> str:
        if status in cls.VALID_SET:
            return status
        raise ValueError(
            f"Invalid solver status '{status}'. Must be strictly one of: {cls.VALID_SET}"
        )


class OptimizationMode(str, Enum):
    FAST = "Fast (heuristic, BEST FOUND likely)"
    EXHAUSTIVE = "Exhaustive (attempt PROVED OPTIMAL)"


class SolverBackend(str, Enum):
    ORTOOLS = "OR-Tools CP-SAT"
    SCIP = "SCIP"
    GUROBI = "Gurobi"


@dataclass(frozen=True)
class TargetTier:
    """
    Represents an exact-match compound requirement:
    Exactly target_k matches at least min_count times across every possible draw.
    Strictly exact matching: (mask & rmask).bit_count() == target_k.
    """
    target_k: int
    min_count: int

    def __post_init__(self):
        if self.target_k < 0:
            raise ValueError(f"target_k cannot be negative: {self.target_k}")
        if self.min_count < 1:
            raise ValueError(f"min_count must be at least 1: {self.min_count}")


@dataclass
class MatchLevelStat:
    """Statistics for an exact match count level (e.g. exact 0, 1, 2, ..., k)."""
    match_level: int
    min_matches: int
    max_matches: int
    avg_matches: float
    std_dev: float
    worst_case_draw: Tuple[int, ...]
    best_case_draw: Tuple[int, ...]


@dataclass
class TierVerificationSummary:
    """Full audit summary for a specific target tier."""
    target_k: int
    min_count: int
    worst_case_min: int
    best_case_max: int
    avg_matches: float
    std_dev: float
    passed: bool
    worst_case_draw: Tuple[int, ...]
    best_case_draw: Tuple[int, ...]
    distribution: Dict[int, int] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Complete verification report against 100% of all possible results."""
    is_valid: bool
    total_draws_evaluated: int
    tier_summaries: Dict[int, TierVerificationSummary]
    all_levels_stats: Dict[int, MatchLevelStat]
    violations: List[Tuple[int, ...]]
    worst_case_draws: Dict[int, Tuple[int, ...]]
    best_case_draws: Dict[int, Tuple[int, ...]]
    overall_variance: float = 0.0


@dataclass
class GameConfig:
    universe_min: int
    universe_max: int
    ticket_size: int
    draw_size: int
    targets: List[TargetTier]

    @property
    def universe_size(self) -> int:
        return self.universe_max - self.universe_min + 1

    @property
    def total_candidate_tickets(self) -> int:
        return math.comb(self.universe_size, self.ticket_size)

    @property
    def total_possible_draws(self) -> int:
        return math.comb(self.universe_size, self.draw_size)


def numbers_to_mask(numbers: Tuple[int, ...], min_val: int = 0) -> int:
    """Converts a tuple of integers to a compact bitmask."""
    mask = 0
    for num in numbers:
        mask |= (1 << (num - min_val))
    return mask


def mask_to_numbers(mask: int, min_val: int = 0) -> Tuple[int, ...]:
    """Converts a bitmask back to a sorted tuple of integers."""
    nums = []
    bit = 0
    temp = mask
    while temp > 0:
        if temp & 1:
            nums.append(bit + min_val)
        temp >>= 1
        bit += 1
    return tuple(nums)


@dataclass
class ComplexityEstimate:
    universe_size: int
    ticket_size: int
    draw_size: int
    total_candidates: int
    total_draws: int
    is_large: bool
    is_extreme: bool
    recommended_mode: str
    suggested_safe_max: int
    warning_message: Optional[str] = None


def estimate_problem_complexity(
    universe_min: int,
    universe_max: int,
    ticket_size: int,
    draw_size: int,
    time_limit_seconds: float = 60.0
) -> ComplexityEstimate:
    """
    Evaluates combinatorial magnitude and pre-checks computational viability.
    Suggests the largest safe pool solvable within the given time limit.
    """
    v = universe_max - universe_min + 1
    k = ticket_size
    m = draw_size

    total_candidates = math.comb(v, k) if v >= k else 0
    total_draws = math.comb(v, m) if v >= m else 0

    # Complexity thresholds:
    # Small: total_candidates <= 10,000 and total_draws <= 50,000 (Instant exact proof)
    # Medium: total_candidates <= 100,000 and total_draws <= 300,000 (Solvable within seconds)
    # Large: total_candidates > 100,000 or total_draws > 300,000 (Requires smart candidate generation or cutting planes)
    # Extreme: total_candidates > 1,500,000 or total_draws > 2,000,000 (Requires Fast mode / iterative expansion)
    is_large = (total_candidates > 80_000) or (total_draws > 200_000)
    is_extreme = (total_candidates > 1_000_000) or (total_draws > 1_500_000)

    # Calculate safe suggested universe_max for typical interactive response under time_limit
    safe_max = universe_max
    for candidate_v in range(v, max(k, m) + 1, -1):
        c_cand = math.comb(candidate_v, k)
        c_draw = math.comb(candidate_v, m)
        if c_cand <= 50_000 and c_draw <= 150_000:
            safe_max = universe_min + candidate_v - 1
            break
    else:
        safe_max = universe_min + max(k, m) + 2

    warning = None
    if is_extreme:
        warning = (
            f"⚠️ Combinatorial Universe is VERY LARGE: C({v}, {k}) = {total_candidates:,} candidates and "
            f"C({v}, {m}) = {total_draws:,} exhaustive draw outcomes. "
            f"Exhaustive branch-and-bound will exceed memory/time if all combinations are built in RAM. "
            f"The system will automatically apply smart candidate sampling & iterative constraint generation. "
            f"Recommended safe range for under {int(time_limit_seconds)}s: Universe {universe_min} to {safe_max}."
        )
    elif is_large:
        warning = (
            f"ℹ️ Moderately Large Instance: C({v}, {k}) = {total_candidates:,} tickets, "
            f"C({v}, {m}) = {total_draws:,} draws. "
            f"Iterative delayed constraint generation is recommended. "
            f"Suggested range for fastest proved-optimal turnaround: Universe {universe_min} to {safe_max}."
        )

    rec_mode = "Fast (heuristic, BEST FOUND likely)" if is_large else "Exhaustive (attempt PROVED OPTIMAL)"

    return ComplexityEstimate(
        universe_size=v,
        ticket_size=k,
        draw_size=m,
        total_candidates=total_candidates,
        total_draws=total_draws,
        is_large=is_large,
        is_extreme=is_extreme,
        recommended_mode=rec_mode,
        suggested_safe_max=safe_max,
        warning_message=warning
    )
