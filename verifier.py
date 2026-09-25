"""
Exhaustive Combinatorial Verifier Module (Root Dispatcher)
Exports all classes and functions from src.verifier and src.core.
"""

from src.core import (
    TargetTier,
    MatchLevelStat,
    TierVerificationSummary,
    VerificationResult,
    numbers_to_mask,
    mask_to_numbers,
)
from src.verifier import verify_tickets_exhaustive

__all__ = [
    "TargetTier",
    "MatchLevelStat",
    "TierVerificationSummary",
    "VerificationResult",
    "numbers_to_mask",
    "mask_to_numbers",
    "verify_tickets_exhaustive",
]
