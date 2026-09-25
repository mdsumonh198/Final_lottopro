"""
Universal Lottery / Combination Optimizer - Production-Ready Entry Point for Dedicated DigitalOcean VPS.

Can be run in two modes:
1. Streamlit Web Dashboard:
   streamlit run app.py --server.port=8501 --server.address=0.0.0.0

2. Command Line Interface (CLI):
   python3 app.py --min 1 --max 12 -k 6 -m 6 --target 5 1 --mode exhaustive --export-csv tickets.csv
"""

import sys
import os
import argparse
import math
import time
import io
import textwrap
from itertools import combinations
from typing import List, Tuple, Dict, Any, Optional

import streamlit as st
import pandas as pd
import numpy as np

from src.core import (
    TargetTier,
    OptimizationMode,
    SolverBackend,
    SolverStatus,
    estimate_problem_complexity,
    numbers_to_mask,
)
from src.verifier import verify_tickets_exhaustive
from src.optimizer import run_delayed_constraint_generation, OptimizationOutput


# -----------------------------------------------------------------------------
# CLI Execution Mode
# -----------------------------------------------------------------------------
def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Universal Combinatorial Lottery Optimizer (Cutting Plane Engine)"
    )
    parser.add_argument("--min", type=int, default=1, help="Universe minimum number (e.g. 0 or 1)")
    parser.add_argument("--max", type=int, default=12, help="Universe maximum number (e.g. 12, 25, 40)")
    parser.add_argument("-k", "--ticket-size", type=int, default=6, help="Ticket size (k)")
    parser.add_argument("-m", "--draw-size", type=int, default=6, help="Result / draw size (m)")
    parser.add_argument(
        "--target",
        nargs=2,
        action="append",
        type=int,
        metavar=("TARGET_K", "MIN_COUNT"),
        help="Target requirement: exact TARGET_K matches >= MIN_COUNT. Can be specified multiple times.",
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "exhaustive"],
        default="fast",
        help="Optimization mode: fast (heuristic, BEST FOUND likely) or exhaustive (attempt PROVED OPTIMAL)",
    )
    parser.add_argument(
        "--backend",
        choices=["ortools", "scip", "gurobi"],
        default="ortools",
        help="Optimization solver backend (default: ortools)",
    )
    parser.add_argument(
        "--balance",
        dest="balance",
        action="store_true",
        default=False,
        help="Enable Stage 2 match-count variance balancing (default: False for VPS stability)",
    )
    parser.add_argument(
        "--no-balance",
        dest="balance",
        action="store_false",
        help="Disable Stage 2 match-count variance balancing",
    )
    parser.add_argument("--max-iters", type=int, default=50, help="Maximum cutting plane iterations (default: 50)")
    parser.add_argument("--cuts-per-iter", type=int, default=30, help="Cuts added per iteration (default: 30)")
    parser.add_argument("--time-limit", type=float, default=30.0, help="Time limit per solver iteration in seconds (default: 30.0)")
    parser.add_argument("--workers", type=int, default=4, help="Parallel worker threads (default: 4)")
    parser.add_argument("--export-csv", type=str, default=None, help="Export tickets to CSV file")
    parser.add_argument("--export-xlsx", type=str, default=None, help="Export tickets to Excel XLSX file")

    return parser.parse_args()


def run_cli():
    args = parse_cli_args()

    if args.target:
        targets = [TargetTier(target_k=t[0], min_count=t[1]) for t in args.target]
    else:
        targets = [TargetTier(target_k=max(1, args.ticket_size - 1), min_count=1)]

    mode_val = (
        OptimizationMode.EXHAUSTIVE.value
        if args.mode == "exhaustive"
        else OptimizationMode.FAST.value
    )

    print("=" * 78)
    print("🛡️  UNIVERSAL LOTTERY / COMBINATION OPTIMIZER ENGINE (VPS CLI)")
    print("=" * 78)
    print(f"Universe: [{args.min} to {args.max}] (Size: {args.max - args.min + 1})")
    print(f"Ticket Size (k): {args.ticket_size} | Draw Size (m): {args.draw_size}")
    print(f"Combinatorial universe: C({args.max - args.min + 1}, {args.draw_size}) = {math.comb(args.max - args.min + 1, args.draw_size):,} draws")
    print(f"Mode: {mode_val} | Backend: {args.backend}")
    print(f"Workers: {args.workers} | Max Iters: {args.max_iters} | Balance Variance: {args.balance}")
    print("Compound Targets:")
    for t in targets:
        print(f"  • Exact {t.target_k}-Match >= {t.min_count}")
    print("=" * 78)

    comp = estimate_problem_complexity(args.min, args.max, args.ticket_size, args.draw_size)
    if comp.warning_message:
        print(f"\n{comp.warning_message}\n")

    def cli_progress(info):
        phase = info.get("phase", "")
        it = info.get("iteration", 0)
        status = info.get("status", "")
        print(f"[{time.strftime('%H:%M:%S')}] Iteration {it} | Phase: {phase} | {status}")

    output: OptimizationOutput = run_delayed_constraint_generation(
        universe_min=args.min,
        universe_max=args.max,
        ticket_size=args.ticket_size,
        draw_size=args.draw_size,
        targets=targets,
        mode=mode_val,
        backend=args.backend,
        max_iterations=args.max_iters,
        cuts_per_iteration=args.cuts_per_iter,
        solver_time_limit_per_iter=args.time_limit,
        num_workers=args.workers,
        balance_variance=args.balance,
        progress_callback=cli_progress,
    )

    print("\n" + "=" * 78)
    print("📊 VERIFICATION & OPTIMIZATION REPORT")
    print("=" * 78)
    print(f"SOLVER STATUS:       {output.status}")
    print(f"FULLY VERIFIED:      {output.fully_verified}")
    print(f"TOTAL TICKETS:       {output.total_tickets:,}")
    print(f"DRAWS AUDITED:       {output.total_draws_in_universe:,} (100% Exhaustive C(N, m))")
    print(f"CUTTING ITERATIONS:  {output.total_iterations}")
    print(f"TOTAL RUNTIME:       {output.total_time_seconds:.2f} seconds")
    print(f"VARIANCE BALANCED:   {output.is_balanced}")
    print("-" * 78)

    if output.verification_summary:
        verif = output.verification_summary
        print("\nEXACT MATCH TARGET TIERS AUDIT:")
        print(f"{'Target Tier':<16} | {'Min Req':<8} | {'Worst Min':<10} | {'Best Max':<10} | {'Avg':<8} | {'StdDev':<8} | {'Status'}")
        print("-" * 78)
        for tk, summ in verif.tier_summaries.items():
            st_text = "PASS" if summ.passed else "FAIL"
            print(f"Exact {summ.target_k}-Match   | >= {summ.min_count:<5} | {summ.worst_case_min:<10} | {summ.best_case_max:<10} | {summ.avg_matches:<8.2f} | {summ.std_dev:<8.2f} | {st_text}")

    if args.export_csv and output.tickets:
        csv_rows = []
        for rank, ticket in enumerate(output.tickets, start=1):
            row = {"Rank": rank, "Ticket": " ".join(f"{x:02d}" for x in ticket), "Status": output.status}
            for i, val in enumerate(ticket, start=1):
                row[f"Ball_{i}"] = val
            csv_rows.append(row)
        pd.DataFrame(csv_rows).to_csv(args.export_csv, index=False)
        print(f"\n✅ Exported {output.total_tickets} tickets to CSV: {args.export_csv}")

    if args.export_xlsx and output.tickets:
        xlsx_rows = []
        for rank, ticket in enumerate(output.tickets, start=1):
            row = {"Rank": rank, "Ticket": " ".join(f"{x:02d}" for x in ticket), "Status": output.status}
            for i, val in enumerate(ticket, start=1):
                row[f"Ball_{i}"] = val
            xlsx_rows.append(row)
        pd.DataFrame(xlsx_rows).to_excel(args.export_xlsx, index=False)
        print(f"✅ Exported {output.total_tickets} tickets to Excel (XLSX): {args.export_xlsx}")

    print("=" * 78)


# -----------------------------------------------------------------------------
# Streamlit Web Dashboard Mode (Production Dedicated VPS Optimized)
# -----------------------------------------------------------------------------
def run_web_dashboard():
    st.set_page_config(
        page_title="Universal Lottery Optimizer (OR-Tools / SCIP / Gurobi)",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    CUSTOM_CSS = textwrap.dedent("""
    <style>
    /* Main Dark Theme Canvas */
    .main, .block-container {
        background-color: #0b0e14 !important;
        color: #e2e8f0 !important;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif !important;
    }

    /* Status Badges */
    .badge-optimal {
        display: inline-block;
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: #ffffff;
        font-weight: 900;
        font-size: 0.9rem;
        padding: 6px 16px;
        border-radius: 9999px;
        letter-spacing: 0.05em;
        border: 1.5px solid #34d399;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);
    }

    .badge-best-found {
        display: inline-block;
        background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%);
        color: #ffffff;
        font-weight: 900;
        font-size: 0.9rem;
        padding: 6px 16px;
        border-radius: 9999px;
        letter-spacing: 0.05em;
        border: 1.5px solid #7dd3fc;
        box-shadow: 0 4px 14px rgba(56, 189, 248, 0.4);
    }

    .badge-infeasible {
        display: inline-block;
        background: linear-gradient(135deg, #b91c1c 0%, #ef4444 100%);
        color: #ffffff;
        font-weight: 900;
        font-size: 0.9rem;
        padding: 6px 16px;
        border-radius: 9999px;
        letter-spacing: 0.05em;
        border: 1.5px solid #f87171;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 0.4);
    }

    /* Metric Cards */
    .or-metric-box {
        background: #111827;
        border: 1px solid #1f293d;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    .or-metric-val {
        font-size: 1.8rem;
        font-weight: 900;
        color: #f8fafc;
        font-family: ui-monospace, monospace;
    }

    .or-metric-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 4px;
    }

    /* Ball Badges */
    .lotto-ball {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #1e293b;
        border: 1.5px solid #475569;
        color: #f1f5f9;
        font-weight: 800;
        font-size: 0.75rem;
        font-family: ui-monospace, monospace;
        margin: 2px;
    }

    .lotto-ball.hit {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        border-color: #34d399;
        color: #ffffff;
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
    }

    .draw-ball {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #1e3a8a;
        border: 2px solid #38bdf8;
        color: #ffffff;
        font-weight: 900;
        font-size: 0.85rem;
        font-family: ui-monospace, monospace;
        margin: 3px;
    }
    </style>
    """).strip()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Session State Initialization (VPS Defaults)
    if "targets" not in st.session_state:
        st.session_state["targets"] = [
            {"target_k": 5, "min_count": 1}
        ]

    if "opt_output" not in st.session_state:
        st.session_state["opt_output"] = None

    if "opt_mode" not in st.session_state:
        st.session_state["opt_mode"] = OptimizationMode.FAST.value

    if "solver_backend" not in st.session_state:
        st.session_state["solver_backend"] = SolverBackend.ORTOOLS.value

    if "balance_variance" not in st.session_state:
        st.session_state["balance_variance"] = False

    # -------------------------------------------------------------------------
    # Sidebar - Parameters & Target Configuration
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### ⚙️ Game Universe & Range")
        st.caption("Universal user-defined integer range, ticket size, and result size.")

        presets = {
            "Custom Configuration": None,
            "⚡ Fast Optimal 1–12 (k=6, m=6, 5-match >= 1)": {
                "min": 1, "max": 12, "k": 6, "m": 6,
                "targets": [{"target_k": 5, "min_count": 1}]
            },
            "🧪 Small Verified 1–25 (k=6, m=6, 5≥1, 4≥10, 3≥25)": {
                "min": 1, "max": 25, "k": 6, "m": 6,
                "targets": [
                    {"target_k": 5, "min_count": 1},
                    {"target_k": 4, "min_count": 10},
                    {"target_k": 3, "min_count": 25},
                ]
            },
            "🎯 Fantasy 5/14 (k=5, m=5, 4-match >= 1)": {
                "min": 1, "max": 14, "k": 5, "m": 5,
                "targets": [{"target_k": 4, "min_count": 1}]
            },
            "💎 Exact 4-Match Guarantee 0–11 (k=6, m=6, 4-match >= 1)": {
                "min": 0, "max": 11, "k": 6, "m": 6,
                "targets": [{"target_k": 4, "min_count": 1}]
            },
        }

        preset_choice = st.selectbox("Load Preset Scenario:", list(presets.keys()), index=0)

        if preset_choice != "Custom Configuration" and preset_choice != st.session_state.get("last_preset"):
            p = presets[preset_choice]
            st.session_state["universe_min"] = p["min"]
            st.session_state["universe_max"] = p["max"]
            st.session_state["ticket_size"] = p["k"]
            st.session_state["draw_size"] = p["m"]
            st.session_state["targets"] = list(p["targets"])
            st.session_state["last_preset"] = preset_choice
            st.rerun()

        u_col1, u_col2 = st.columns(2)
        with u_col1:
            u_min = st.number_input(
                "Universe Min:",
                min_value=0,
                max_value=39,
                value=st.session_state.get("universe_min", 1),
                step=1
            )
            st.session_state["universe_min"] = int(u_min)
        with u_col2:
            u_max = st.number_input(
                "Universe Max:",
                min_value=int(u_min) + 1,
                max_value=40,
                value=max(int(u_min) + 1, st.session_state.get("universe_max", 25)),
                step=1
            )
            st.session_state["universe_max"] = int(u_max)

        v_size = int(u_max) - int(u_min) + 1

        t_col1, t_col2 = st.columns(2)
        with t_col1:
            ticket_k = st.number_input(
                "Ticket Size (k):",
                min_value=2,
                max_value=min(15, v_size),
                value=min(st.session_state.get("ticket_size", 6), v_size),
                step=1
            )
            st.session_state["ticket_size"] = int(ticket_k)
        with t_col2:
            draw_m = st.number_input(
                "Draw Size (m):",
                min_value=2,
                max_value=min(15, v_size),
                value=min(st.session_state.get("draw_size", 6), v_size),
                step=1
            )
            st.session_state["draw_size"] = int(draw_m)

        comp = estimate_problem_complexity(int(u_min), int(u_max), int(ticket_k), int(draw_m))

        comp_html = textwrap.dedent(f"""
        <div style="background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:10px; margin-top:8px; font-size:0.75rem; font-family:ui-monospace, monospace;">
            <div>Candidates C({v_size}, {ticket_k}): <strong>{comp.total_candidates:,}</strong></div>
            <div>Exhaustive Draws C({v_size}, {draw_m}): <strong>{comp.total_draws:,}</strong></div>
        </div>
        """).strip()
        st.markdown(comp_html, unsafe_allow_html=True)

        if comp.warning_message:
            st.warning(comp.warning_message)

        st.markdown("---")
        st.markdown("### 🎯 Compound Exact-Match Targets")
        st.caption("STRICTLY EXACT match: `(mask & rmask).bit_count() == target_k`")

        current_targets = st.session_state["targets"]
        max_k_possible = min(int(ticket_k), int(draw_m))

        indices_to_remove = []
        updated_targets = []

        for idx, tgt in enumerate(current_targets):
            st.markdown(f"**Target Tier #{idx + 1}**")
            t_col1, t_col2, t_col3 = st.columns([4, 4, 2])

            with t_col1:
                t_k = st.number_input(
                    "Exact Match (k)",
                    min_value=1,
                    max_value=max_k_possible,
                    value=min(tgt.get("target_k", max_k_possible), max_k_possible),
                    step=1,
                    key=f"tgt_k_{idx}"
                )
            with t_col2:
                min_c = st.number_input(
                    "Min Count (>=)",
                    min_value=1,
                    max_value=2000,
                    value=max(1, tgt.get("min_count", 1)),
                    step=1,
                    key=f"tgt_min_{idx}"
                )
            with t_col3:
                st.write("")
                st.write("")
                if len(current_targets) > 1:
                    if st.button("✕", key=f"del_{idx}", help="Remove this target tier"):
                        indices_to_remove.append(idx)

            updated_targets.append({"target_k": int(t_k), "min_count": int(min_c)})

        if indices_to_remove:
            for rem_idx in sorted(indices_to_remove, reverse=True):
                updated_targets.pop(rem_idx)
            st.session_state["targets"] = updated_targets
            st.rerun()
        else:
            st.session_state["targets"] = updated_targets

        if st.button("➕ Add Compound Target", use_container_width=True):
            default_next_k = max(1, current_targets[-1]["target_k"] - 1 if current_targets else max_k_possible)
            st.session_state["targets"].append({"target_k": default_next_k, "min_count": 1})
            st.rerun()

        st.markdown("---")
        st.markdown("### ⚡ Optimization Engine Settings (VPS Defaults)")

        opt_mode = st.selectbox(
            "Optimization Mode:",
            [OptimizationMode.FAST.value, OptimizationMode.EXHAUSTIVE.value],
            index=0 if comp.is_large else 1,
            help="Fast mode uses smart candidate generation for fast convergence. Exhaustive evaluates all combinations to prove mathematical global optimality."
        )
        st.session_state["opt_mode"] = opt_mode

        backend_options = [SolverBackend.ORTOOLS.value, SolverBackend.SCIP.value, SolverBackend.GUROBI.value]
        chosen_backend = st.selectbox(
            "Solver Backend:",
            backend_options,
            index=0,
            help="OR-Tools CP-SAT is the recommended default. SCIP and Gurobi are alternative mathematical programming solvers."
        )
        st.session_state["solver_backend"] = chosen_backend

        # Variance Reduction: default FALSE (unchecked) for VPS stability
        balance_var = st.checkbox(
            "Balance Match Counts Across Results (Variance Reduction)",
            value=st.session_state.get("balance_variance", False),
            help="Stage 2: Re-solves to minimize match variance across draws. Keep unchecked for faster solve and lower risk of infeasibility."
        )
        st.session_state["balance_variance"] = balance_var

        # Sliders: Max Iters default 50, Workers default 4
        max_iters = st.slider("Max Cutting-Plane Iterations:", min_value=5, max_value=100, value=50, step=5)
        cuts_per_iter = st.slider("Cuts Added per Iteration:", min_value=5, max_value=60, value=30, step=5)
        time_limit = st.slider("Solver Time Limit / Iter (s):", min_value=5, max_value=120, value=25, step=5)
        num_workers = st.slider("Parallel Worker Threads:", min_value=1, max_value=16, value=4, step=1)

    # -------------------------------------------------------------------------
    # Main Page Header & Banner
    # -------------------------------------------------------------------------
    header_html = textwrap.dedent("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; border-bottom:1px solid #1e293b; padding-bottom:12px;">
        <div>
            <h1 style="font-size:1.8rem; font-weight:900; color:#f8fafc; margin:0;">
                🛡️ Universal Lottery / Combination Optimizer
            </h1>
            <p style="color:#94a3b8; font-size:0.85rem; margin:4px 0 0 0;">
                Cutting Plane Delayed Constraint Generation & Exhaustive Audit with Google OR-Tools, SCIP & Gurobi
            </p>
        </div>
        <div>
            <span style="background:#1e293b; color:#38bdf8; font-weight:800; font-size:0.75rem; padding:5px 12px; border-radius:6px; font-family:ui-monospace, monospace; border:1px solid #38bdf8;">
                100% EXHAUSTIVE GUARANTEE · ZERO ESTIMATION
            </span>
        </div>
    </div>
    """).strip()
    st.markdown(header_html, unsafe_allow_html=True)

    target_strings = [
        f"<span style='color:#38bdf8; font-weight:800;'>Exact {t['target_k']}-Match</span> ≥ <strong style='color:#ffffff;'>{t['min_count']}</strong>"
        for t in st.session_state["targets"]
    ]
    banner_html = textwrap.dedent(f"""
    <div style="background:#0f172a; border:1.5px solid #1e3a8a; border-radius:10px; padding:10px 14px; margin-bottom:16px;">
        <span style="font-size:0.78rem; font-weight:800; color:#93c5fd; text-transform:uppercase; letter-spacing:0.04em;">Active Compound Requirements:</span>
        <div style="font-size:0.92rem; color:#e2e8f0; margin-top:4px;">
            {' &nbsp;·&nbsp; '.join(target_strings)}
        </div>
    </div>
    """).strip()
    st.markdown(banner_html, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Run Optimizer Action
    # -------------------------------------------------------------------------
    run_col1, run_col2 = st.columns([3, 1])
    with run_col1:
        execute_btn = st.button("🚀 Run Delayed Constraint Optimizer", type="primary", use_container_width=True)
    with run_col2:
        if st.button("↺ Reset Results", use_container_width=True):
            st.session_state["opt_output"] = None
            st.rerun()

    if execute_btn:
        target_tiers = [TargetTier(target_k=t["target_k"], min_count=t["min_count"]) for t in st.session_state["targets"]]
        progress_bar = st.progress(0.0)
        status_placeholder = st.empty()

        def update_progress(info: Dict[str, Any]):
            it = info.get("iteration", 1)
            max_it = info.get("max_iterations", max_iters)
            pct = min(1.0, it / max_it)
            progress_bar.progress(pct)

            status_text = info.get("status", "Optimizing...")
            phase = info.get("phase", "")
            active_cnt = info.get("active_draws", 0)
            t_cnt = info.get("tickets_count", 0)
            c_cnt = info.get("candidates_count", 0)

            p_html = textwrap.dedent(f"""
            <div style="background:#111827; border:1px solid #374151; border-radius:8px; padding:10px 14px; margin: 8px 0; font-family:ui-monospace, monospace;">
                <div style="color:#38bdf8; font-weight:800; font-size:0.85rem;">🔄 Iteration {it}/{max_it} · Phase: {phase}</div>
                <div style="color:#f3f4f6; font-size:0.8rem; margin-top:2px;">{status_text}</div>
                <div style="color:#9ca3af; font-size:0.75rem; margin-top:4px;">
                    Active Constraints: <strong>{active_cnt:,}</strong> | Active Candidates: <strong>{c_cnt:,}</strong> | Current Tickets: <strong>{t_cnt:,}</strong>
                </div>
            </div>
            """).strip()
            status_placeholder.markdown(p_html, unsafe_allow_html=True)

        with st.spinner("Executing Cutting Plane Optimization & 100% Combinatorial Audit..."):
            try:
                output: OptimizationOutput = run_delayed_constraint_generation(
                    universe_min=st.session_state["universe_min"],
                    universe_max=st.session_state["universe_max"],
                    ticket_size=st.session_state["ticket_size"],
                    draw_size=st.session_state["draw_size"],
                    targets=target_tiers,
                    mode=st.session_state["opt_mode"],
                    backend="scip" if "scip" in chosen_backend.lower() else "gurobi" if "gurobi" in chosen_backend.lower() else "ortools",
                    max_iterations=max_iters,
                    cuts_per_iteration=cuts_per_iter,
                    solver_time_limit_per_iter=time_limit,
                    num_workers=num_workers,
                    balance_variance=st.session_state["balance_variance"],
                    progress_callback=update_progress
                )
                st.session_state["opt_output"] = output
                progress_bar.progress(1.0)
                status_placeholder.success("✅ Optimization Process Complete!")
            except Exception as e:
                st.error(f"Optimization Error: {str(e)}")

    # -------------------------------------------------------------------------
    # Comprehensive Results Dashboard
    # -------------------------------------------------------------------------
    opt_res: Optional[OptimizationOutput] = st.session_state.get("opt_output")

    if opt_res is not None:
        st.markdown("---")
        st.markdown("## 📊 Comprehensive Results Dashboard")

        badge_class = (
            "badge-optimal" if opt_res.status == SolverStatus.PROVED_OPTIMAL
            else "badge-best-found" if opt_res.status == SolverStatus.BEST_FOUND
            else "badge-infeasible"
        )

        badge_desc = (
            "Mathematical proof complete: global minimum lower bound == upper bound."
            if opt_res.status == SolverStatus.PROVED_OPTIMAL
            else "Valid integer solution found satisfying 100% combinatorial space; branch-and-bound reached iteration/time limit."
            if opt_res.status == SolverStatus.BEST_FOUND
            else "Mathematically impossible to satisfy active compound constraints simultaneously with current solver settings."
        )

        status_border_color = (
            "#10b981" if opt_res.status == SolverStatus.PROVED_OPTIMAL
            else "#38bdf8" if opt_res.status == SolverStatus.BEST_FOUND
            else "#ef4444"
        )

        status_box_html = textwrap.dedent(f"""
        <div style="background:#0f172a; border:2px solid {status_border_color}; border-radius:12px; padding:16px; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                <div>
                    <span class="{badge_class}">{opt_res.status}</span>
                    <span style="margin-left:10px; font-size:0.8rem; font-weight:700; color:{'#34d399' if opt_res.fully_verified else '#fbbf24'};">
                        {'✓ 100% EXHAUSTIVELY VERIFIED' if opt_res.fully_verified else '⚠ NOT FULLY VERIFIED'}
                    </span>
                    {f"<span style='margin-left:10px; font-size:0.75rem; background:#1e293b; color:#a78bfa; padding:3px 8px; border-radius:4px;'>VARIANCE BALANCED</span>" if opt_res.is_balanced else ""}
                    <div style="color:#cbd5e1; font-size:0.85rem; margin-top:8px;">{badge_desc}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:2.2rem; font-weight:900; color:#ffffff; font-family:ui-monospace, monospace;">
                        {opt_res.total_tickets:,} <span style="font-size:1rem; color:#94a3b8; font-weight:600;">Tickets</span>
                    </div>
                </div>
            </div>
        </div>
        """).strip()
        st.markdown(status_box_html, unsafe_allow_html=True)

        # Robust INFEASIBLE Guidance Alert
        if opt_res.status == SolverStatus.INFEASIBLE or opt_res.total_tickets == 0:
            infeasible_alert_html = textwrap.dedent("""
            <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.14) 0%, rgba(185, 28, 28, 0.24) 100%); border: 1.5px solid #ef4444; border-radius: 12px; padding: 18px 22px; margin: 16px 0; box-shadow: 0 4px 16px rgba(239, 68, 68, 0.25);">
                <div style="display:flex; align-items:flex-start; gap:14px;">
                    <div style="font-size:1.8rem; line-height:1;">⚠️</div>
                    <div style="flex:1;">
                        <div style="font-size:1.12rem; font-weight:800; color:#fca5a5; margin-bottom:6px;">
                            Optimization Infeasible: No Valid Ticket Set Satisfies Active Constraints
                        </div>
                        <div style="color:#e2e8f0; font-size:0.88rem; line-height:1.55; margin-bottom:12px;">
                            The mathematical solver (CP-SAT / MIP) determined that it is either combinatorial impossibility to satisfy all required target tiers simultaneously on every single draw, or the solver reached its time limit before finding a feasible integer solution.
                        </div>
                        <div style="background:#0b0f19; border-radius:8px; padding:12px 16px; border:1px solid #1e293b;">
                            <div style="font-weight:700; color:#38bdf8; font-size:0.84rem; margin-bottom:6px;">
                                🔧 Recommended Actions to Resolve Infeasibility:
                            </div>
                            <ul style="margin:0; padding-left:18px; color:#cbd5e1; font-size:0.82rem; line-height:1.65;">
                                <li><strong>Relax Compound Constraints:</strong> If multiple target tiers are active (e.g. 5≥1, 4≥10, 3≥25), delete secondary tiers using the <strong>✕</strong> button in the sidebar. Start with a single primary requirement (e.g. Exact 5-Match ≥ 1 or 4-Match ≥ 1).</li>
                                <li><strong>Keep Variance Balancing Disabled:</strong> Ensure <em>"Balance Match Counts Across Results (Variance Reduction)"</em> remains unchecked (OFF).</li>
                                <li><strong>Extend Solver Time Limit:</strong> For universes larger than 20 numbers, increase <em>"Solver Time Limit / Iter"</em> from 25s to 60s or 90s.</li>
                                <li><strong>Use Fast Heuristic Mode:</strong> Switch Optimization Mode to <em>"Fast (heuristic, BEST FOUND likely)"</em> for efficient candidate generation.</li>
                                <li><strong>Verify Range:</strong> Ensure Ticket Size (k) and Draw Size (m) do not exceed the universe range (Max - Min + 1).</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            """).strip()
            st.markdown(infeasible_alert_html, unsafe_allow_html=True)

        # Key Metrics Grid
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(
                textwrap.dedent(f"""
                <div class="or-metric-box">
                    <div class="or-metric-val">{opt_res.total_tickets:,}</div>
                    <div class="or-metric-label">Winning Wheel Tickets</div>
                </div>
                """).strip(),
                unsafe_allow_html=True
            )
        with m_col2:
            st.markdown(
                textwrap.dedent(f"""
                <div class="or-metric-box">
                    <div class="or-metric-val">{opt_res.total_draws_in_universe:,}</div>
                    <div class="or-metric-label">Exhaustive Draws Audited</div>
                </div>
                """).strip(),
                unsafe_allow_html=True
            )
        with m_col3:
            st.markdown(
                textwrap.dedent(f"""
                <div class="or-metric-box">
                    <div class="or-metric-val">{opt_res.total_iterations} <span style="font-size:1rem; color:#94a3b8;">({opt_res.active_draws_count} cuts)</span></div>
                    <div class="or-metric-label">Cutting Iterations</div>
                </div>
                """).strip(),
                unsafe_allow_html=True
            )
        with m_col4:
            st.markdown(
                textwrap.dedent(f"""
                <div class="or-metric-box">
                    <div class="or-metric-val">{opt_res.total_time_seconds:.2f}s</div>
                    <div class="or-metric-label">Total Execution Time</div>
                </div>
                """).strip(),
                unsafe_allow_html=True
            )

        # Target Tiers Audit Table
        if opt_res.verification_summary:
            st.markdown("### 🛡️ Compound Targets Verification Report")
            st.caption(f"Evaluated against all {opt_res.total_draws_in_universe:,} draws in C({v_size}, {st.session_state['draw_size']}). No sampling.")

            verif_data = []
            for k, summ in opt_res.verification_summary.tier_summaries.items():
                status_text = "PASS ✅" if summ.passed else "FAIL ❌"
                verif_data.append({
                    "Target Tier": f"Exact {summ.target_k}-Match",
                    "Requirement": f"≥ {summ.min_count}",
                    "Worst-Case Min": summ.worst_case_min,
                    "Best-Case Max": summ.best_case_max,
                    "Average Matches": f"{summ.avg_matches:.3f}",
                    "Std Deviation": f"{summ.std_dev:.3f}",
                    "Worst-Case Result": " ".join(f"{x:02d}" for x in summ.worst_case_draw),
                    "Status": status_text
                })

            df_verif = pd.DataFrame(verif_data)
            st.dataframe(df_verif, use_container_width=True, hide_index=True)

            if opt_res.verification_summary.all_levels_stats:
                st.markdown("### 📈 All Exact-Match Levels Distribution (0 to k)")
                st.caption("Complete breakdown of match counts across every possible combinatorial draw.")

                levels_data = []
                for lvl, stat in opt_res.verification_summary.all_levels_stats.items():
                    levels_data.append({
                        "Match Level": f"Exact {stat.match_level}-Match",
                        "Min Matches": stat.min_matches,
                        "Max Matches": stat.max_matches,
                        "Average Matches": f"{stat.avg_matches:.3f}",
                        "Std Dev (Variance)": f"{stat.std_dev:.3f}",
                        "Worst-Case Draw": " ".join(f"{x:02d}" for x in stat.worst_case_draw),
                        "Best-Case Draw": " ".join(f"{x:02d}" for x in stat.best_case_draw),
                    })
                df_levels = pd.DataFrame(levels_data)
                st.dataframe(df_levels, use_container_width=True, hide_index=True)

        # Worst-Case Result Inspector
        if opt_res.verification_summary and opt_res.verification_summary.tier_summaries:
            st.markdown("### 🔍 Worst-Case Result Inspector")
            st.caption("Inspect the exact draw where the minimum hit count occurred.")

            inspect_tiers = list(opt_res.verification_summary.tier_summaries.keys())
            selected_inspect_tier = st.selectbox(
                "Select Target Tier to Inspect Worst-Case Draw:",
                inspect_tiers,
                format_func=lambda k: f"Exact {k}-Match Tier (Worst-Case Min: {opt_res.verification_summary.tier_summaries[k].worst_case_min})"
            )

            target_summ = opt_res.verification_summary.tier_summaries[selected_inspect_tier]
            worst_draw = target_summ.worst_case_draw
            worst_draw_set = set(worst_draw)

            balls_markup = "".join([f"<span class='draw-ball'>{num:02d}</span>" for num in worst_draw])
            worst_draw_html = textwrap.dedent(f"""
            <div style="background:#111827; border:1px solid #1e3a8a; border-radius:10px; padding:12px 16px; margin-bottom:12px;">
                <div style="color:#93c5fd; font-size:0.78rem; font-weight:800; text-transform:uppercase;">
                    Worst-Case Draw for Exact {target_summ.target_k}-Match:
                </div>
                <div style="margin-top:6px;">{balls_markup}</div>
                <div style="color:#cbd5e1; font-size:0.8rem; margin-top:6px; font-family:ui-monospace, monospace;">
                    Minimum tickets matching exactly {target_summ.target_k}: <strong>{target_summ.worst_case_min}</strong> (Required: ≥ {target_summ.min_count})
                </div>
            </div>
            """).strip()
            st.markdown(worst_draw_html, unsafe_allow_html=True)

            ticket_match_details = []
            for rank, ticket in enumerate(opt_res.tickets, start=1):
                overlap = len(set(ticket).intersection(worst_draw_set))
                ticket_match_details.append({
                    "rank": rank,
                    "ticket": ticket,
                    "overlap": overlap,
                    "hits_tier": overlap == target_summ.target_k
                })

            tier_hits_count = sum(1 for item in ticket_match_details if item["hits_tier"])

            insp_col1, insp_col2 = st.columns([1, 1])
            with insp_col1:
                st.markdown(f"**Tickets hitting EXACTLY {target_summ.target_k} matches on this draw ({tier_hits_count}):**")
                matching_tickets = [it for it in ticket_match_details if it["hits_tier"]]
                if matching_tickets:
                    for item in matching_tickets[:15]:
                        t_balls = "".join([
                            f"<span class='lotto-ball {'hit' if b in worst_draw_set else ''}'>{b:02d}</span>"
                            for b in item["ticket"]
                        ])
                        ticket_line_html = f"<div style='margin-bottom:3px;'><code>#{item['rank']:03d}</code> {t_balls}</div>"
                        st.markdown(ticket_line_html, unsafe_allow_html=True)
                    if len(matching_tickets) > 15:
                        st.caption(f"... and {len(matching_tickets) - 15} more tickets.")
                else:
                    st.warning(f"0 tickets matched exactly {target_summ.target_k}.")

            with insp_col2:
                st.markdown("**Other match count breakdown on this draw:**")
                counts_on_worst = {}
                for item in ticket_match_details:
                    m_cnt = item["overlap"]
                    counts_on_worst[m_cnt] = counts_on_worst.get(m_cnt, 0) + 1

                for m_level in sorted(counts_on_worst.keys(), reverse=True):
                    is_target = (m_level == target_summ.target_k)
                    style_prefix = "⭐ " if is_target else "• "
                    st.markdown(f"{style_prefix}Exact **{m_level}** matches: **{counts_on_worst[m_level]}** tickets")

        # Ticket Export (CSV & Excel)
        if opt_res.tickets:
            st.markdown("---")
            st.markdown("### 📥 Download Tickets (CSV & Excel XLSX)")

            export_rows = []
            for rank, ticket in enumerate(opt_res.tickets, start=1):
                row_dict = {
                    "Priority_Rank": rank,
                    "Ticket_ID": f"TK-{rank:05d}",
                    "Formatted_Ticket": " ".join(f"{num:02d}" for num in ticket)
                }
                for b_idx, b_val in enumerate(ticket, start=1):
                    row_dict[f"Ball_{b_idx}"] = b_val
                row_dict["Solver_Status"] = opt_res.status
                export_rows.append(row_dict)

            df_export = pd.DataFrame(export_rows)

            csv_bytes = df_export.to_csv(index=False).encode("utf-8")

            xlsx_buffer = io.BytesIO()
            with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Optimal_Tickets")
            xlsx_bytes = xlsx_buffer.getvalue()

            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                st.download_button(
                    label=f"📥 Download {opt_res.total_tickets:,} Tickets (CSV)",
                    data=csv_bytes,
                    file_name=f"lottery_optimizer_{opt_res.total_tickets}_tickets.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with exp_col2:
                st.download_button(
                    label=f"📊 Download {opt_res.total_tickets:,} Tickets (Excel XLSX)",
                    data=xlsx_bytes,
                    file_name=f"lottery_optimizer_{opt_res.total_tickets}_tickets.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with st.expander(f"View All {opt_res.total_tickets:,} Tickets in Browser"):
                st.dataframe(df_export[["Priority_Rank", "Ticket_ID", "Formatted_Ticket"]], use_container_width=True, hide_index=True)

        # Iteration History
        if opt_res.iteration_history:
            with st.expander("🔬 View Cutting-Plane Iteration History"):
                hist_data = []
                for h in opt_res.iteration_history:
                    hist_data.append({
                        "Iteration": h.iteration,
                        "Active Draws": h.num_active_draws,
                        "Candidate Pool": h.num_candidate_tickets,
                        "Tickets Solved": h.num_tickets_found,
                        "Violations Added": h.num_violations_added,
                        "Time (s)": f"{h.iteration_time_seconds:.2f}",
                        "Status": h.status
                    })
                st.dataframe(pd.DataFrame(hist_data), use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# Runtime Selector
# -----------------------------------------------------------------------------
def is_streamlit_runtime() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_context
        if get_script_run_context() is not None:
            return True
    except Exception:
        pass
    try:
        from streamlit.runtime import exists
        if exists():
            return True
    except Exception:
        pass
    return False


if __name__ == "__main__":
    cli_flags = {
        "--min", "--max", "-k", "--ticket-size", "-m", "--draw-size",
        "--target", "--mode", "--backend", "--balance", "--no-balance",
        "--export-csv", "--export-xlsx", "--workers", "--max-iters", "--cuts-per-iter", "--time-limit"
    }
    has_cli_args = any(arg in cli_flags for arg in sys.argv)

    if has_cli_args and not is_streamlit_runtime():
        run_cli()
    else:
        run_web_dashboard()
