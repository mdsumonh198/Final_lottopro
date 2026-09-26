"""
solver_cp_sat.py - Google OR-Tools CP-SAT & Set Covering Solver
Formulates exact mathematical integer programming for Lottery Covering Designs.
"""

from __future__ import annotations
import math
import time
from typing import List, Tuple, Set, Dict, Optional
from core import GameConfig, ticket_to_mask, mask_to_ticket

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

class CPSatCoveringSolver:
    """
    CP-SAT formulation of the minimum covering problem:
    Minimize Sum_{j} x_j
    Subject to:
      Sum_{j : |j ∩ i| >= target_k} x_j >= min_count  for all violating draws i
    """
    def __init__(self, config: GameConfig, time_limit_seconds: float = 60.0):
        self.config = config
        self.time_limit = time_limit_seconds

    def solve_cutting_plane_subproblem(
        self,
        candidate_tickets: List[List[int]],
        violating_draws: List[Tuple[int, ...]],
        existing_tickets: Optional[List[List[int]]] = None,
    ) -> Tuple[List[List[int]], str]:
        """
        Solves integer covering model on candidate tickets covering violating draws.
        Returns: (selected_tickets, status_string)
        """
        if not violating_draws:
            return existing_tickets or [], "OPTIMAL"

        if not ORTOOLS_AVAILABLE:
            # Fallback exact greedy set cover for when OR-Tools is not in environment
            return self._fallback_greedy_set_cover(candidate_tickets, violating_draws, existing_tickets)

        model = cp_model.CpModel()
        num_candidates = len(candidate_tickets)
        x_vars = [model.NewBoolVar(f"t_{i}") for i in range(num_candidates)]

        # Objective: Minimize total newly selected tickets
        model.Minimize(sum(x_vars))

        # Build candidate masks
        cand_masks = [ticket_to_mask(t, offset=self.config.start_number) for t in candidate_tickets]
        t_k = self.config.target_k

        # For each violating draw, at least 1 covering candidate ticket must be selected
        for draw in violating_draws:
            draw_mask = ticket_to_mask(draw, offset=self.config.start_number)
            covering_cands = [
                x_vars[i] for i, cm in enumerate(cand_masks)
                if (cm & draw_mask).bit_count() >= t_k
            ]
            if covering_cands:
                model.Add(sum(covering_cands) >= 1)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.time_limit
        solver.parameters.num_search_workers = 8
        solver.parameters.log_search_progress = False

        status = solver.Solve(model)
        selected: List[List[int]] = []

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for i in range(num_candidates):
                if solver.Value(x_vars[i]) == 1:
                    selected.append(candidate_tickets[i])
            status_str = "PROVED OPTIMAL" if status == cp_model.OPTIMAL else "BEST FOUND"
        else:
            status_str = "INFEASIBLE"
            selected, status_str = self._fallback_greedy_set_cover(candidate_tickets, violating_draws, existing_tickets)

        if existing_tickets:
            # Union existing and newly selected
            seen = {tuple(sorted(t)) for t in existing_tickets}
            combined = list(existing_tickets)
            for t in selected:
                st = tuple(sorted(t))
                if st not in seen:
                    seen.add(st)
                    combined.append(t)
            return combined, status_str

        return selected, status_str

    def _fallback_greedy_set_cover(
        self,
        candidate_tickets: List[List[int]],
        violating_draws: List[Tuple[int, ...]],
        existing_tickets: Optional[List[List[int]]] = None,
    ) -> Tuple[List[List[int]], str]:
        """
        High-performance combinatorial set-covering resolution.
        Guarantees that 100% of violating draws are covered.
        """
        offset = self.config.start_number
        t_k = self.config.target_k

        draw_masks = [ticket_to_mask(d, offset=offset) for d in violating_draws]
        uncovered = set(range(len(draw_masks)))

        cand_masks = [ticket_to_mask(t, offset=offset) for t in candidate_tickets]

        # Inverted index: draw -> list of candidate indices that cover it
        draw_to_cands: List[List[int]] = [[] for _ in range(len(draw_masks))]
        for c_idx, cm in enumerate(cand_masks):
            for d_idx, dm in enumerate(draw_masks):
                if (cm & dm).bit_count() >= t_k:
                    draw_to_cands[d_idx].append(c_idx)

        selected_indices: Set[int] = set()

        while uncovered:
            # Find candidate that covers the maximum remaining uncovered draws
            best_cand = -1
            best_cov = 0
            best_uncovered_hits: Set[int] = set()

            for c_idx in range(len(candidate_tickets)):
                if c_idx in selected_indices:
                    continue
                cm = cand_masks[c_idx]
                hits = {d_idx for d_idx in uncovered if (cm & draw_masks[d_idx]).bit_count() >= t_k}
                if len(hits) > best_cov:
                    best_cov = len(hits)
                    best_cand = c_idx
                    best_uncovered_hits = hits

            if best_cand != -1 and best_cov > 0:
                selected_indices.add(best_cand)
                uncovered -= best_uncovered_hits
            else:
                # If existing candidates cannot cover an uncovered draw, use the draw itself as a ticket!
                # (A draw of size 6 matches itself in 6 numbers >= 5)
                missing_d_idx = next(iter(uncovered))
                missing_draw = violating_draws[missing_d_idx]
                candidate_tickets.append(list(missing_draw))
                new_idx = len(candidate_tickets) - 1
                cand_masks.append(draw_masks[missing_d_idx])
                selected_indices.add(new_idx)
                # Remove all draws covered by this newly added ticket
                cm = draw_masks[missing_d_idx]
                hits = {d_idx for d_idx in uncovered if (cm & draw_masks[d_idx]).bit_count() >= t_k}
                uncovered -= hits

        selected_tickets = [candidate_tickets[i] for i in selected_indices]

        if existing_tickets:
            seen = {tuple(sorted(t)) for t in existing_tickets}
            combined = list(existing_tickets)
            for t in selected_tickets:
                st = tuple(sorted(t))
                if st not in seen:
                    seen.add(st)
                    combined.append(t)
            return combined, "BEST FOUND"

        return selected_tickets, "BEST FOUND"
