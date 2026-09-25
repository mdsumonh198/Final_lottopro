# Universal Lottery / Combination Optimizer

Operations Research Delayed Constraint Generation (Cutting Plane) Engine for combinatorial lottery covering designs with exact match guarantees.

## Core Rules & Non-Negotiable Specifications
1. **Universal Configuration:** Arbitrary number range (any subset of 0–40), ticket size $k$, result size $m$, and compound exact-match targets (e.g. exact-5 $\ge$ 1, exact-4 $\ge$ 10, exact-3 $\ge$ 25).
2. **100% Exhaustive Verification:** Guarantees are checked against **every possible draw** in $C(N, m)$ — zero probabilistic sampling or approximations.
3. **Priority Order:**
   1. 100% worst-case guarantee.
   2. Minimum possible tickets.
   3. Match counts as balanced as possible across all results (variance minimization).
4. **Strict Solver Status:**
   - `PROVED OPTIMAL`: When mathematical proof establishes lower bound == upper bound over the complete problem space.
   - `BEST FOUND`: Valid integer solution satisfying 100% of draws found before optimality proof.
   - `INFEASIBLE`: Mathematically impossible to satisfy active constraints.
5. **Exact Matching:** Evaluated via `(ticket_mask & draw_mask).bit_count() == target_k`.
6. **Iterative Delayed Constraint Generation:**
   - Solve on subset of draws.
   - Verify against all $C(v, m)$ draws.
   - Add violating draws as cutting planes.
   - Expand candidate pool dynamically if needed.
   - Repeat until 0 violations remain.

## Recommended Technology & Solver Backends
- **Google OR-Tools CP-SAT (Default):** High-performance constraint programming solver with multi-threading and warm-start hints.
- **SCIP:** Mixed-Integer Programming solver via OR-Tools Linear Solver or PySCIPOpt.
- **Gurobi:** State-of-the-art commercial MIP solver (if installed/licensed).

## Quickstart

### 1. Web Application (Streamlit)
```bash
streamlit run app.py
```

### 2. Command Line Interface (CLI)
```bash
# Example 1: Fast mode with compound targets on 1–25
python3 app.py --min 1 --max 25 -k 6 -m 6 --target 5 1 --target 4 10 --target 3 25 --mode fast

# Example 2: Exhaustive mode proving optimality on 1–12
python3 app.py --min 1 --max 12 -k 6 -m 6 --target 5 1 --mode exhaustive --export-csv tickets.csv --export-xlsx tickets.xlsx
```

### 3. Python API
```python
from src.core import TargetTier, OptimizationMode
from src.optimizer import run_delayed_constraint_generation

output = run_delayed_constraint_generation(
    universe_min=1,
    universe_max=25,
    ticket_size=6,
    draw_size=6,
    targets=[
        TargetTier(target_k=5, min_count=1),
        TargetTier(target_k=4, min_count=10),
        TargetTier(target_k=3, min_count=25),
    ],
    mode=OptimizationMode.FAST.value,
    backend="ortools",
    balance_variance=True
)

print(output.status)        # "PROVED OPTIMAL" or "BEST FOUND"
print(output.total_tickets) # Total tickets selected
print(output.fully_verified)# True (0 violations across all 177,100 draws)
```
