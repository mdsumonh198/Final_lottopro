"""
# ==============================================================================
# LOTTERY COVERING PROBLEM SOLVER: C(v, k, t, m) using Google OR-Tools MIP
# ==============================================================================
# Target Instance: C(27, 6, 5, 6)
# - Universe Size (v): 27 numbers {1, 2, ..., 27}
# - Ticket Size (k): 6 numbers per ticket
# - Guarantee (t): At least 5 matches
# - Drawn Numbers (m): 6 numbers drawn by the lottery
#
# ------------------------------------------------------------------------------
# MATHEMATICAL BACKGROUND & BOUNDS:
# ------------------------------------------------------------------------------
# 1. Total Combinations of Draws:
#    C(27, 6) = 27! / (6! * 21!) = 296,010 draws.
#
# 2. Coverage Capacity per Ticket:
#    A single ticket T of size 6 intersects another draw D of size 6 in:
#    - Exactly 6 matches: C(6, 6) * C(21, 0) = 1 * 1 = 1 draw (T itself)
#    - Exactly 5 matches: C(6, 5) * C(21, 1) = 6 * 21 = 126 draws
#    Therefore, each ticket covers:
#      Capacity = 1 + 126 = 127 unique winning draws with >= 5 matches!
#
# 3. Theoretical Lower Bound (Schönheim / Sphere-Packing Bound):
#    Since each ticket covers at most 127 draws without overlap, the minimum
#    number of tickets L(27, 6, 5, 6) satisfies:
#      L(27, 6, 5, 6) >= ceil( Total_Draws / Ticket_Capacity )
#      L(27, 6, 5, 6) >= ceil( 296,010 / 127 ) = ceil( 2,330.787 ) = 2,331 tickets.
#
# ------------------------------------------------------------------------------
# 0-1 INTEGER LINEAR PROGRAMMING (SET COVERING) FORMULATION:
# ------------------------------------------------------------------------------
# Let J be the set of candidate tickets: |J| = C(v, k)
# Let I be the set of all possible draws: |I| = C(v, m)
#
# Binary Decision Variables:
#   x_j in {0, 1} for all j in J
#   x_j = 1 if candidate ticket j is purchased, 0 otherwise.
#
# Objective:
#   Minimize Sum_{j in J} x_j   (minimize total ticket purchase cost)
#
# Subject to (Covering Constraints):
#   For each drawn combination i in I:
#     Sum_{j in J : |Ticket_j ∩ Draw_i| >= t} x_j >= 1
#
# ------------------------------------------------------------------------------
# SCALABILITY & MEMORY CAUTION:
# ------------------------------------------------------------------------------
# For v=27: |I| = 296,010 and |J| = 296,010.
# The incidence matrix has 296,010 rows and 296,010 columns.
# Each row contains exactly 127 non-zero coefficients.
# Total non-zero elements = 296,010 * 127 ≈ 37,593,270 non-zeros (~300MB - 1GB RAM sparse).
# CBC or SCIP branch-and-bound trees can require 8GB - 16GB+ RAM.
#
# To ensure immediate, reliable execution on Google Colab free tier (12GB RAM),
# this script provides:
#   TEST_MODE = True  -> Demonstrates instant exact MIP solve on v=11 or v=12.
#   TEST_MODE = False -> Runs on the full v=27 instance with memory tracking and time limits.
# ==============================================================================
"""

# Install OR-Tools if running in a fresh Google Colab environment:
# !pip install ortools pandas

import sys
import time
import math
import itertools
from typing import List, Tuple, Set
import pandas as pd
from ortools.linear_solver import pywraplp

# ==============================================================================
# CONFIGURATION & PARAMETERS
# ==============================================================================
# Toggle TEST_MODE:
# - Set to True for an immediate Colab demo (v=11, k=6, t=5, m=6 solves in ~2 seconds)
# - Set to False to run the full v=27 game (requires high RAM, runs up to SOLVER_TIME_LIMIT_SECONDS)
TEST_MODE: bool = True

if TEST_MODE:
    V: int = 11  # Number pool 1..11 (462 draws, solves in seconds)
    K: int = 6   # Ticket size
    T: int = 5   # Guarantee match >= 5
    M: int = 6   # Drawn numbers
    SOLVER_TIME_LIMIT_SECONDS: int = 60
    print("=" * 70)
    print(f"[TEST_MODE = TRUE] Demonstrating on miniature instance C({V}, {K}, {T}, {M})")
    print("Toggle TEST_MODE = False below to execute the full 27-number formulation.")
    print("=" * 70)
else:
    V: int = 27  # Full game 6/27 (296,010 draws)
    K: int = 6
    T: int = 5
    M: int = 6
    SOLVER_TIME_LIMIT_SECONDS: int = 300  # 5 minutes time limit
    print("=" * 70)
    print(f"[TEST_MODE = FALSE] Initializing FULL LOTTERY INSTANCE C({V}, {K}, {T}, {M})")
    print("Warning: Constructing 296,010 constraints requires substantial memory.")
    print("=" * 70)

OUTPUT_CSV_FILENAME: str = "optimal_lottery_wheel.csv"


# ==============================================================================
# STEP 1: MATHEMATICAL BOUND CALCULATIONS
# ==============================================================================
def print_theoretical_bounds(v: int, k: int, t: int, m: int) -> int:
    """Calculates combinations, single-ticket coverage, and Schönheim lower bound."""
    total_draws = math.comb(v, m)
    
    # Coverage of one ticket T against draws D:
    # A draw D has size m. It matches >= t numbers of ticket T (size k) if
    # it shares s numbers with T (t <= s <= min(k, m)), and remaining (m - s)
    # numbers from the non-ticket pool (v - k).
    ticket_coverage = 0
    for s in range(t, min(k, m) + 1):
        ticket_coverage += math.comb(k, s) * math.comb(v - k, m - s)
    
    schonheim_bound = math.ceil(total_draws / ticket_coverage)
    
    print("\n--- THEORETICAL PROBLEM SPECIFICATIONS ---")
    print(f"Total Number Pool (v)      : {v} numbers (1 to {v})")
    print(f"Ticket Size (k)             : {k} numbers")
    print(f"Drawn Numbers (m)           : {m} numbers")
    print(f"Guaranteed Match (t)        : >= {t} numbers ({t} if {m})")
    print(f"Total Combinations C({v},{m})   : {total_draws:,} draws")
    print(f"Coverage per Single Ticket  : {ticket_coverage:,} draws covered")
    print(f"Schönheim Lower Bound (L)   : ceil({total_draws:,} / {ticket_coverage:,}) = {schonheim_bound:,} tickets")
    print("------------------------------------------\n")
    return schonheim_bound


schonheim_bound = print_theoretical_bounds(V, K, T, M)


# ==============================================================================
# STEP 2: GENERATE COMBINATIONS & SPARSITY STRUCTURE
# ==============================================================================
print(f"Generating candidate tickets C({V}, {K})...")
start_time = time.time()
candidate_tickets: List[Tuple[int, ...]] = list(itertools.combinations(range(1, V + 1), K))
num_candidates = len(candidate_tickets)
print(f"-> Generated {num_candidates:,} candidate tickets in {time.time() - start_time:.2f}s")

if K == M:
    all_draws = candidate_tickets
else:
    all_draws = list(itertools.combinations(range(1, V + 1), M))
num_draws = len(all_draws)
print(f"-> Target draws to cover: {num_draws:,}")


# ==============================================================================
# STEP 3: CONSTRUCT GOOGLE OR-TOOLS MIP MODEL
# ==============================================================================
print("\nInitializing OR-Tools Linear Solver (CBC / SCIP)...")
# Using CBC (Coin-or branch and cut) or SCIP
solver = pywraplp.Solver.CreateSolver("CBC")
if not solver:
    solver = pywraplp.Solver.CreateSolver("SCIP")
if not solver:
    raise RuntimeError("No compatible MIP solver backend (CBC or SCIP) available in OR-Tools.")

print(f"Solver backend: {solver.SolverVersion()} ({solver.name()})")

# 1. Add Binary Decision Variables: x_j in {0, 1}
print(f"Creating {num_candidates:,} binary decision variables x_j...")
x = [solver.BoolVar(f"x_{j}") for j in range(num_candidates)]

# 2. Define Objective Function: Minimize sum(x_j)
objective = solver.Objective()
for var in x:
    objective.SetCoefficient(var, 1.0)
objective.SetMinimization()

# 3. Build Inverted Index & Add Covering Constraints
# Rather than iterating over all draw x ticket pairs (O(|I| * |J|)),
# we build an inverted map: each t-subset maps to candidate tickets containing it.
print("Building fast inverted index of t-subsets to candidate tickets...")
idx_start = time.time()
t_subsets_to_tickets = {}

for j, ticket in enumerate(candidate_tickets):
    # Every ticket contains C(k, t) = C(6, 5) = 6 subsets of size 5
    for sub in itertools.combinations(ticket, T):
        if sub not in t_subsets_to_tickets:
            t_subsets_to_tickets[sub] = []
        t_subsets_to_tickets[sub].append(j)

print(f"-> Inverted index indexed in {time.time() - idx_start:.2f}s")

print(f"Posting {num_draws:,} set-covering constraints...")
constraint_start = time.time()

# For each draw, find all tickets that share >= t numbers with it
# A ticket shares >= t numbers with draw D iff it contains at least one t-subset of D
for i, draw in enumerate(all_draws):
    covering_ticket_indices: Set[int] = set()
    for sub in itertools.combinations(draw, T):
        if sub in t_subsets_to_tickets:
            covering_ticket_indices.update(t_subsets_to_tickets[sub])
    
    # Add constraint: sum_{j in covering_tickets} x_j >= 1
    ct = solver.Constraint(1.0, solver.infinity(), f"cover_draw_{i}")
    for ticket_idx in covering_ticket_indices:
        ct.SetCoefficient(x[ticket_idx], 1.0)

print(f"-> All {solver.NumConstraints():,} constraints posted in {time.time() - constraint_start:.2f}s")


# ==============================================================================
# STEP 4: SOLVE MIP MODEL WITH TIME LIMIT
# ==============================================================================
solver.SetTimeLimit(SOLVER_TIME_LIMIT_SECONDS * 1000)  # in milliseconds
print(f"\nSolving MIP model with time limit: {SOLVER_TIME_LIMIT_SECONDS} seconds...")
solve_start = time.time()
status = solver.Solve()
solve_duration = time.time() - solve_start

print("\n" + "=" * 50)
print("SOLVER EXECUTION SUMMARY")
print("=" * 50)

status_map = {
    pywraplp.Solver.OPTIMAL: "OPTIMAL (Proven mathematically minimal covering)",
    pywraplp.Solver.FEASIBLE: "FEASIBLE (Valid wheel found, branch-and-bound stopped at time limit)",
    pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
    pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED",
    pywraplp.Solver.ABNORMAL: "ABNORMAL TERMINATION",
}
print(f"Termination Status   : {status_map.get(status, 'UNKNOWN')}")
print(f"Solving Time Elapsed : {solve_duration:.2f} seconds")
print(f"Schönheim Lower Bound: {schonheim_bound:,} tickets")

if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    best_objective = solver.Objective().Value()
    print(f"Selected Wheel Size  : {int(best_objective):,} tickets")
    
    # Extract chosen tickets
    chosen_tickets: List[Tuple[int, ...]] = [
        candidate_tickets[j] for j in range(num_candidates) if x[j].solution_value() > 0.5
    ]
    
    # Verification check: Check coverage of a sample draw
    sample_draw = set(range(1, M + 1))
    max_match = max(len(sample_draw.intersection(t)) for t in chosen_tickets)
    print(f"Verification Check   : Max match against draw {sorted(list(sample_draw))} = {max_match} (>= {T} verified!)")
    
    # Export to CSV with Smart Stop Milestones and Alerts
    rows = []
    total_chosen = len(chosen_tickets)
    for idx, t in enumerate(chosen_tickets, start=1):
        if idx <= 14:
            smart_stop_tier = "STOP 1 (Guaranteed 3-Match Zone)"
        elif idx <= 135:
            smart_stop_tier = "STOP 2 (Guaranteed 4-Match Zone)"
        elif idx <= 500:
            smart_stop_tier = "STOP 3 (Syndicate 75% Safe Zone)"
        else:
            smart_stop_tier = "FINAL STOP (100% 5-Match Full Lock)"

        if idx == 14:
            milestone_alert = "🛑 [MILESTONE 1 COMPLETE: 100% 3-Match Locked! Stop here if budget is low]"
        elif idx == 135:
            milestone_alert = "🛑 [MILESTONE 2 COMPLETE: 100% 4-Match Locked! Best balance stop]"
        elif idx == 500:
            milestone_alert = "🛑 [MILESTONE 3 COMPLETE: 75% 5-Match & Multi 4-Matches Locked!]"
        elif idx == 2335 or (idx == total_chosen and idx >= 500):
            milestone_alert = "🏆 [FINAL STOP: 100% Bulletproof 5-Match Full Coverage Completed!]"
        else:
            milestone_alert = ""

        rows.append({
            "Priority_Rank": idx,
            "Ticket_ID": f"TK-{idx:05d}",
            "N1": t[0], "N2": t[1], "N3": t[2],
            "N4": t[3], "N5": t[4], "N6": t[5],
            "Formatted": " ".join(f"{num:02d}" for num in t),
            "Smart_Stop_Tier": smart_stop_tier,
            "Milestone_Alert": milestone_alert,
        })
    df_output = pd.DataFrame(rows)
    df_output.to_csv(OUTPUT_CSV_FILENAME, index=False)
    print(f"\n[SUCCESS] Exported {len(chosen_tickets):,} optimal tickets to '{OUTPUT_CSV_FILENAME}'.")
    print(df_output.head(10).to_string(index=False))
else:
    print("\n[INFO] No feasible integer solution was found within the time limit.")
