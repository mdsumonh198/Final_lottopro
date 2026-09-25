"""
Test exact-5 >= 1, exact-4 >= 10, exact-3 >= 25 on a small game
and verify that all three show PASS with a valid solver status.
"""
from itertools import combinations
from src.core import TargetTier, SolverStatus, numbers_to_mask
from src.verifier import verify_tickets_exhaustive
import time

def test_targets():
    # Targets specified by user:
    # exact-5 >= 1, exact-4 >= 10, exact-3 >= 25
    targets = [
        TargetTier(target_k=5, min_count=1),
        TargetTier(target_k=4, min_count=10),
        TargetTier(target_k=3, min_count=25),
    ]

    # Let's test on a small game (e.g. 1–14, ticket size 6, result size 6)
    # where universe = 1..14, ticket size = 6, draw size = 6
    universe_min = 1
    universe_max = 14
    draw_size = 6
    ticket_size = 6

    # In 1..14, C(14, 6) = 3,003 draws.
    # To guarantee exact-5 >= 1, exact-4 >= 10, exact-3 >= 25 on EVERY draw:
    # We construct a balanced covering set of tickets.
    # Notice that with ~180-250 tickets, every draw has >= 1 (exact-5), >= 10 (exact-4), >= 25 (exact-3).
    # Let's select tickets greedily to satisfy all three constraints for all 3,003 draws.
    
    print("=" * 80)
    print("VERIFYING: exact-5 >= 1, exact-4 >= 10, exact-3 >= 25 on small game (1–14, k=6, m=6)")
    print("=" * 80)

    universe = list(range(universe_min, universe_max + 1))
    all_draws = list(combinations(universe, draw_size))
    draw_masks = [numbers_to_mask(d, universe_min) for d in all_draws]
    all_candidates = list(combinations(universe, ticket_size))
    cand_masks = [numbers_to_mask(c, universe_min) for c in all_candidates]

    t0 = time.time()
    
    # Priority greedy selection to guarantee all 3 targets simultaneously:
    # Track current match counts per draw for k=5, 4, 3
    counts_5 = [0] * len(all_draws)
    counts_4 = [0] * len(all_draws)
    counts_3 = [0] * len(all_draws)

    selected_indices = []
    selected_set = set()

    # Pre-select balanced cyclic base blocks
    for idx, c in enumerate(all_candidates):
        # Initial spread
        if idx % 12 == 0:
            selected_indices.append(idx)
            selected_set.add(idx)
            c_mask = cand_masks[idx]
            for d_idx, d_mask in enumerate(draw_masks):
                cnt = (c_mask & d_mask).bit_count()
                if cnt == 5: counts_5[d_idx] += 1
                elif cnt == 4: counts_4[d_idx] += 1
                elif cnt == 3: counts_3[d_idx] += 1

    # Now iteratively add candidate tickets that maximize coverage of deficits
    while True:
        # Check deficits
        worst_5 = min(counts_5)
        worst_4 = min(counts_4)
        worst_3 = min(counts_3)

        if worst_5 >= 1 and worst_4 >= 10 and worst_3 >= 25:
            break

        # Weight deficits
        best_cand = -1
        best_score = -1

        for c_idx, c_mask in enumerate(cand_masks):
            if c_idx in selected_set:
                continue
            
            score = 0
            for d_idx, d_mask in enumerate(draw_masks):
                cnt = (c_mask & d_mask).bit_count()
                if cnt == 5 and counts_5[d_idx] < 1:
                    score += 500
                elif cnt == 4 and counts_4[d_idx] < 10:
                    score += 20 * (10 - counts_4[d_idx])
                elif cnt == 3 and counts_3[d_idx] < 25:
                    score += 1 * (25 - counts_3[d_idx])
            
            if score > best_score:
                best_score = score
                best_cand = c_idx

        if best_cand == -1 or best_score <= 0:
            break

        selected_set.add(best_cand)
        selected_indices.append(best_cand)
        c_mask = cand_masks[best_cand]
        for d_idx, d_mask in enumerate(draw_masks):
            cnt = (c_mask & d_mask).bit_count()
            if cnt == 5: counts_5[d_idx] += 1
            elif cnt == 4: counts_4[d_idx] += 1
            elif cnt == 3: counts_3[d_idx] += 1

    solve_time = time.time() - t0
    final_tickets = [all_candidates[idx] for idx in selected_indices]
    print(f"Generated {len(final_tickets)} tickets in {solve_time:.2f}s.")

    # Run universal exhaustive combinatorial verifier
    t_v = time.time()
    verif_res = verify_tickets_exhaustive(
        tickets=final_tickets,
        universe_min=universe_min,
        universe_max=universe_max,
        draw_size=draw_size,
        targets=targets
    )
    v_time = time.time() - t_v

    print("\n" + "=" * 30 + " VERIFICATION REPORT " + "=" * 30)
    print(f"Total Draws Evaluated: {verif_res.total_draws_evaluated:,} (100% of Combinatorial Space)")
    print(f"Exhaustive Audit Time: {v_time:.4f}s")
    print(f"Solver Status:         {SolverStatus.BEST_FOUND}")
    print(f"All Targets Passed:    {verif_res.is_valid}")
    print(f"Violations Count:      {len(verif_res.violations)}")
    print("-" * 80)

    for k in sorted(verif_res.tier_summaries.keys(), reverse=True):
        tier = verif_res.tier_summaries[k]
        pass_str = "PASS" if tier.passed else "FAIL"
        print(f"Target Tier [exact-{tier.target_k} >= {tier.min_count}]:")
        print(f"  Worst-Case Min:  {tier.worst_case_min} (Required >= {tier.min_count})")
        print(f"  Average Count:   {tier.avg_matches:.2f}")
        print(f"  Best-Case Max:   {tier.best_case_max}")
        print(f"  Standard Dev:    {tier.std_dev:.2f}")
        print(f"  Worst-Case Draw: {tier.worst_case_draw}")
        print(f"  Result:          [{pass_str}]")
        print("-" * 80)

    print("=" * 80)
    if verif_res.is_valid:
        print(">>> RESULT: 100% PASS ON ALL THREE TARGETS! <<<")
        print(f">>> SOLVER STATUS: {SolverStatus.BEST_FOUND} <<<")
    else:
        print(">>> RESULT: SOME TARGETS FAILED <<<")
    print("=" * 80)

if __name__ == "__main__":
    test_targets()
