"""
core.py - Core Domain Models, Configurations, and Combinatorial Helpers
Universal Lottery & Covering Design Engine
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Set, Dict, Optional, Iterable

@dataclass(frozen=True)
class CompoundTarget:
    """
    Compound target requirement: e.g. target_k = 5, min_count = 1 (at least 1 ticket matches >= 5).
    """
    target_k: int
    min_count: int = 1

    def __post_init__(self):
        if self.target_k < 1:
            raise ValueError("target_k must be >= 1")
        if self.min_count < 1:
            raise ValueError("min_count must be >= 1")

@dataclass
class GameConfig:
    """
    Universal Combinatorial Lottery System Configuration: (v, k, t, m)
    """
    universe_size: int = 27         # v: Pool size (e.g. 1 to 27)
    ticket_size: int = 6           # k: Number of spots per ticket (e.g. 6)
    draw_size: int = 6             # m: Number of winning balls drawn (e.g. 6)
    target_k: int = 5              # t: Guaranteed match threshold (e.g. 5)
    min_count: int = 1             # Frequency: At least min_count tickets must hit >= target_k
    targets: List[CompoundTarget] = field(default_factory=list)
    start_number: int = 1          # 1-indexed (1..27) or 0-indexed (0..9 for digit games)
    allow_repeats: bool = False
    order_matters: bool = False

    def __post_init__(self):
        if not self.targets:
            self.targets = [CompoundTarget(target_k=self.target_k, min_count=self.min_count)]

    @property
    def total_combinations(self) -> int:
        """Total number of possible lottery draws: C(v, m)"""
        if self.allow_repeats and self.order_matters:
            return self.universe_size ** self.draw_size
        return math.comb(self.universe_size, self.draw_size)

    @property
    def candidate_universe_size(self) -> int:
        """Total number of possible tickets: C(v, k)"""
        return math.comb(self.universe_size, self.ticket_size)

    @property
    def single_ticket_coverage_capacity(self) -> int:
        """
        Number of winning draws covered with >= target_k matches by a single ticket.
        For m = k = 6, t = 5 on v = 27:
        1 ticket covers itself (1) + C(6, 5) * C(21, 1) = 1 + 6 * 21 = 127 draws.
        """
        if self.ticket_size == self.draw_size:
            cap = 0
            for i in range(self.target_k, self.ticket_size + 1):
                cap += math.comb(self.ticket_size, i) * math.comb(self.universe_size - self.ticket_size, self.draw_size - i)
            return cap
        return 1

    @property
    def schonheim_lower_bound(self) -> int:
        """
        Theoretical Schönheim / Sphere-Packing Lower Bound:
        ceil( C(v, m) / Single_Ticket_Capacity )
        """
        cap = self.single_ticket_coverage_capacity
        if cap <= 0:
            return 1
        return math.ceil(self.total_combinations / cap)

@dataclass
class VerificationResult:
    """
    Exhaustive 100% Audit Result across all C(v, m) draws without sampling.
    """
    total_checked: int              # e.g. 296,010
    pass_count: int                 # Count of draws with >= min_count tickets matching >= target_k
    fail_count: int                 # Count of draws with 0 tickets matching >= target_k
    pass_rate: float                # (pass_count / total_checked) * 100
    fail_rate: float                # (fail_count / total_checked) * 100
    is_100_percent_guaranteed: bool # True if and only if fail_count == 0
    status: str                     # "PASS" or "FAIL"
    solver_status: str              # "PROVED OPTIMAL", "BEST FOUND", or "INFEASIBLE"
    worst_case_match_count: int     # Minimum tickets matching >= target_k across all draws
    best_case_match_count: int      # Maximum tickets matching >= target_k across all draws
    draws_with_jackpot_6: int       # Draws with exact 6/6 match
    draws_with_match_5: int         # Draws with exact 5/6 match
    draws_with_match_4: int         # Draws with exact 4/6 match (Strictly separated!)
    draws_with_match_3_or_less: int # Draws with <= 3 match
    execution_time_seconds: float
    uncovered_draws_sample: List[Tuple[int, ...]] = field(default_factory=list)

@dataclass
class OptimizationResult:
    """
    Output of cutting-plane / IP optimization.
    """
    tickets: List[List[int]]
    ticket_count: int
    config: GameConfig
    verification: VerificationResult
    iterations: int
    solver_status: str              # "PROVED OPTIMAL", "BEST FOUND"

def ticket_to_mask(numbers: Iterable[int], offset: int = 1) -> int:
    """Convert ticket numbers to a compact 32/64-bit integer bitmask."""
    mask = 0
    for n in numbers:
        mask |= (1 << (n - offset))
    return mask

def mask_to_ticket(mask: int, offset: int = 1) -> List[int]:
    """Convert integer bitmask back to a sorted list of numbers."""
    res = []
    bit = 0
    while mask > 0:
        if mask & 1:
            res.append(bit + offset)
        mask >>= 1
        bit += 1
    return res
