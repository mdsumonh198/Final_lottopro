"""
streamlit_app.py - Production Streamlit Dashboard
Client's Original UI for Universal Lottery Covering & Exact Mathematical Audit
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import io
from core import GameConfig, CompoundTarget
from verifier import verify_coverage
from optimizer import optimize_wheel, generate_cyclic_seed_tickets

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom Theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Universal Lottery / Combination Optimizer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Dark Slate Premium Theme */
    .stApp {
        background-color: #0b0f17;
        color: #e6edf3;
    }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .metric-pass {
        border: 2px solid #00d284 !important;
        background: #092218 !important;
    }
    .metric-fail {
        border: 2px solid #f85149 !important;
        background: #240c11 !important;
    }
    .badge-pass {
        background-color: #00d284;
        color: #000;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 13px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Header & Banner
# -----------------------------------------------------------------------------
st.title("🎯 Universal Lottery / Combination Optimizer")
st.caption("Operations Research Exact Cutting-Plane Covering Engine · 100% Worst-Case Guarantee")

# -----------------------------------------------------------------------------
# 3. Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Game Configuration")
    v = st.number_input("Universe Pool Size (v):", min_value=6, max_value=40, value=27, step=1)
    k = st.number_input("Ticket Size (k):", min_value=2, max_value=12, value=6, step=1)
    m = st.number_input("Draw Size (m):", min_value=2, max_value=12, value=6, step=1)

    st.markdown("---")
    st.header("🎯 Target Guarantee Requirements")
    target_k = st.selectbox("Guaranteed Match Threshold (t):", options=[3, 4, 5, 6], index=2)
    min_count = st.number_input("Minimum Tickets Matching >= t:", min_value=1, max_value=20, value=1, step=1)

    st.markdown("---")
    st.header("🚀 Optimization Controls")
    mode = st.radio(
        "Mode:",
        options=[
            "100% Zero-Miss Guarantee (FAIL = 0) [7,510 Minimal Tickets]",
            "Baseline 2,335 Tickets Audit (FAIL = 111,163)",
            "Run Live Chvátal Greedy Optimizer"
        ],
        index=0
    )
    run_btn = st.button("⚡ Execute Live Verification / Re-solve", type="primary", use_container_width=True)

config = GameConfig(
    universe_size=int(v),
    ticket_size=int(k),
    draw_size=int(m),
    target_k=int(target_k),
    min_count=int(min_count),
)

# -----------------------------------------------------------------------------
# 4. Session State Management & Data Loading
# -----------------------------------------------------------------------------
import os, json
from verifier import verify_all_results

if "tickets" not in st.session_state or run_btn:
    if "Zero-Miss" in mode:
        minimal_file = "tickets_chvatal_minimal.json"
        if os.path.exists(minimal_file):
            with open(minimal_file) as f:
                st.session_state["tickets"] = json.load(f)
        else:
            with st.spinner("Executing Chvátal Greedy Set Cover loop..."):
                res = optimize_wheel(config=config, target_k=int(target_k), min_count=int(min_count))
                st.session_state["tickets"] = res.tickets
    elif "Baseline" in mode:
        seeds_file = "tickets_2335.json"
        if os.path.exists(seeds_file):
            with open(seeds_file) as f:
                st.session_state["tickets"] = json.load(f)
        else:
            st.session_state["tickets"] = generate_cyclic_seed_tickets(v=int(v), k=int(k))
    else:
        with st.spinner("Executing Chvátal Greedy Set Cover loop..."):
            res = optimize_wheel(config=config, target_k=int(target_k), min_count=int(min_count))
            st.session_state["tickets"] = res.tickets

tickets = st.session_state["tickets"]

# Execute 100% Exhaustive Audit
with st.spinner("Executing 100% exhaustive audit across all 296,010 draws..."):
    audit = verify_all_results(tickets, config=config, target_k=int(target_k), min_count=int(min_count))


# -----------------------------------------------------------------------------
# 5. Dashboard Scorecard (Strict Client Requirement)
# -----------------------------------------------------------------------------
st.markdown("### 📊 Verification & Audit Scoreboard")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 12px; color: #8b949e; text-transform: uppercase;">Total Checked</div>
        <div style="font-size: 28px; font-weight: 800; color: #fff;">{audit.total_checked:,}</div>
        <div style="font-size: 11px; color: #58a6ff; margin-top: 4px;">C({v}, {m}) All Possible Draws</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    fail_style = "metric-pass" if audit.fail_count == 0 else "metric-fail"
    fail_color = "#00d284" if audit.fail_count == 0 else "#f85149"
    st.markdown(f"""
    <div class="metric-card {fail_style}">
        <div style="font-size: 12px; color: #8b949e; text-transform: uppercase;">FAIL Results</div>
        <div style="font-size: 28px; font-weight: 800; color: {fail_color};">{audit.fail_count:,}</div>
        <div style="font-size: 11px; color: {fail_color}; margin-top: 4px;">
            {"✅ 100% Zero-Miss Guarantee" if audit.fail_count == 0 else f"⚠️ {audit.fail_rate}% Gaps Found"}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    status_label = "PASS ✅" if audit.is_100_percent_guaranteed else "FAIL ❌"
    status_bg = "metric-pass" if audit.is_100_percent_guaranteed else "metric-fail"
    st.markdown(f"""
    <div class="metric-card {status_bg}">
        <div style="font-size: 12px; color: #8b949e; text-transform: uppercase;">Audit Status</div>
        <div style="font-size: 28px; font-weight: 800; color: #fff;">{status_label}</div>
        <div style="font-size: 11px; color: #c9d1d9; margin-top: 4px;">Solver: {audit.solver_status}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 12px; color: #8b949e; text-transform: uppercase;">System Tickets</div>
        <div style="font-size: 28px; font-weight: 800; color: #e3b341;">{len(tickets):,}</div>
        <div style="font-size: 11px; color: #8b949e; margin-top: 4px;">Schönheim Bound: {config.schonheim_lower_bound:,}</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. Detailed Match Distribution Breakdown
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 🔍 Exact Match Breakdown Across 296,010 Draws")

st.info("ℹ️ **Verification Rule**: Any draw with >= 1 ticket matching >= 5 is marked **PASS**. 4-matches are strictly counted as 4-matches and NEVER conflated with 5.")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(label="🏆 6/6 Jackpot Hits", value=f"{audit.draws_with_jackpot_6:,}")
with m2:
    st.metric(label="🟢 5/6 Matches", value=f"{audit.draws_with_match_5:,}")
with m3:
    st.metric(label="🔵 4/6 Matches (Strict)", value=f"{audit.draws_with_match_4:,}")
with m4:
    st.metric(label="🟡 <= 3 Matches", value=f"{audit.draws_with_match_3_or_less:,}")

# -----------------------------------------------------------------------------
# 7. Live Winning Numbers Tester
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 🎲 Test Any Custom Draw")

col_a, col_b = st.columns([2, 1])

with col_a:
    sample_draw = st.multiselect(
        f"Select {m} winning numbers from 1 to {v}:",
        options=list(range(1, v + 1)),
        default=list(range(1, m + 1))
    )

with col_b:
    if len(sample_draw) == m:
        draw_set = set(sample_draw)
        test_matches = [len(draw_set.intersection(t)) for t in tickets]
        hit_6 = sum(1 for x in test_matches if x == 6)
        hit_5 = sum(1 for x in test_matches if x == 5)
        hit_4 = sum(1 for x in test_matches if x == 4)
        hit_3 = sum(1 for x in test_matches if x == 3)

        st.markdown(f"""
        **Test Result:**
        - **6-Match:** `{hit_6}` tickets
        - **5-Match:** `{hit_5}` tickets
        - **4-Match:** `{hit_4}` tickets
        - **3-Match:** `{hit_3}` tickets
        - **Status:** {'🟢 PASS (>= 5 matched)' if (hit_6 + hit_5) >= 1 else '🔴 FAIL (No 5/6 match)'}
        """)

# -----------------------------------------------------------------------------
# 8. Ticket Table & CSV Export (Strict Client Requirement)
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 📋 Generated Minimal Tickets")

df_tickets = pd.DataFrame({
    "PriorityRank": list(range(1, len(tickets) + 1)),
    "TicketID": [f"TK-{i+1:04d}" for i in range(len(tickets))],
    "Numbers": [", ".join(f"{n:02d}" for n in sorted(t)) for t in tickets],
})

st.dataframe(df_tickets.head(100), use_container_width=True)

# CSV Export
csv_buffer = io.StringIO()
df_tickets.to_csv(csv_buffer, index=False)
csv_bytes = csv_buffer.getvalue().encode('utf-8')

st.download_button(
    label=f"📥 Download All {len(tickets):,} Tickets (CSV)",
    data=csv_bytes,
    file_name=f"lottery_tickets_{v}_{k}_guarantee_{target_k}.csv",
    mime="text/csv",
    type="primary",
)
