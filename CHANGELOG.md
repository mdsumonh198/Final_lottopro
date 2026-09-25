# Changelog

All notable changes to the Lottery Wheeling System and Universal Exact-Match Combinatorial Optimization Engine are documented below.

## [2.0.0] - Universal Exact-Match Combinatorial Optimizer & Zero-Miss Covering Engine

### Added
- **Exact-Match Multi-Tier Target Specification**: Full support for defining arbitrary compound exact-match targets (e.g. `exact-5 >= 1`, `exact-4 >= 10`, `exact-3 >= 25`) with strict equality semantics (`(ticket & draw).bit_count() == target_k`).
- **Flexible Game Configuration**: Configurable number universe (subset of 0–40), pick/ticket size ($k$), and draw/result size ($m$) with validation.
- **Two Solver Backends**:
  - **OR-Tools CP-SAT Backend**: Industrial Constraint Programming solver with lazy constraint addition and symmetry-breaking constraints.
  - **PuLP / CBC Backend**: Fallback integer linear programming engine supporting standard MILP solvers.
- **Delayed Constraint Generation**: Cutting plane algorithm for large instances:
  1. Solve reduced subproblem on active results subset with warm-start heuristic hints.
  2. Verify candidate tickets exhaustively against 100% of all possible combinatorial draws using 64-bit integer bitmasks.
  3. Identify violations (uncovered draws) and generate cutting planes until 0 violations remain.
  4. Final exhaustive audit guarantees 100% mathematical zero-miss certainty.
- **Exhaustive Combinatorial Verifier (`src/verifier.py`)**:
  - Evaluates all $\binom{N}{m}$ combinatorial draws without sampling or probabilistic shortcuts.
  - Computes complete statistical distribution (min, max, average, standard deviation) for every match level ($0$ to $\min(k, m)$).
  - Explicitly reports the worst-case and best-case result draws and PASS/FAIL status for each configured target.
- **Secondary Objective Variance Balancing (`src/optimizer.py`)**:
  - Stage 2 quadratic/linear balancing to minimize match-count variance and distribute prize coverage uniformly across draws while preserving ticket count minimality.
- **Interactive UI with Dual-Language (Bangla & English)**:
  - Real-time lottery wheeling dashboard, interactive budget sliders, combinatorial match tables, and verified coverage statistics.
  - Live export of generated wheels to CSV.
  - Technical panels displaying the complete Python MILP/CP-SAT source code, Google Colab script, and C++ engine.

### Changed
- **CP-SAT Solver Performance**: Added greedy warm-start primal heuristics to feed initial feasible hints to CP-SAT, preventing empty constraint groups and accelerating branch-and-bound convergence.
- **Status Mapping**: Standardized solver status reporting strictly to the three valid statuses: `PROVED OPTIMAL`, `BEST FOUND`, and `INFEASIBLE`.
- **Candidate Pool Generation**: Automated full combinatorial candidate inclusion when $\binom{N}{k} \le 60,000$ to prevent false infeasibility in small games.

### Verification & Testing
To run the automated verification test on the example targets (`exact-5 >= 1`, `exact-4 >= 10`, `exact-3 >= 25`):
```bash
python3 audit_pass.py
```
This performs a 100% exhaustive combinatorial audit across all draws in the combinatorial space and confirms `PASS` on all target tiers with status `BEST FOUND`.
