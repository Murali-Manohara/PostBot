"""
PostBot — India Post District Infrastructure AI
Group 10 | Great Lakes PGP Data Science & GenAI | Batch Sep 2025–Apr 2026
AI: Groq Llama 3.3 70B (Free) | Model: CatBoost R²=0.9243
Screens: Welcome → Login → District → Chat → Analysis
"""

import streamlit as st
from auth        import authenticate, get_demo_credentials
from model_utils import (
    load_district_data, get_states, get_districts,
    get_district_info, get_tier, calculate_suggestion,
    explain_office_types
)
from chatbot import ask_postbot
import pandas as pd

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PostBot — India Post AI",
    page_icon="📮",
    layout="wide",
    initial_sidebar_state="expanded"   # sidebar always open on load
)

# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif !important; }

.stApp { background-color: #060d18; }
.main .block-container { padding: 0 2rem 2rem 2rem; max-width: 1300px; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display:none; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#07111f 0%,#060d18 100%) !important;
    border-right: 1px solid #1e3a5f !important;
    min-width: 290px !important;
    max-width: 320px !important;
}
section[data-testid="stSidebar"] * { color:#e2e8f0 !important; }
/* Sidebar toggle button — make it bright orange so users always see it */
button[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background: #e8612c !important;
    color: white !important;
    border-radius: 0 8px 8px 0 !important;
    width: 28px !important;
    height: 60px !important;
    border: none !important;
}
button[data-testid="collapsedControl"]:hover {
    background: #c44d22 !important;
}
/* Keep sidebar visible even on smaller screens */
[data-testid="stSidebarNav"] { display:none; }

/* Inputs */
.stTextInput > div > div > input {
    background:#0d1b2a !important; border:1px solid #1e3a5f !important;
    border-radius:8px !important; color:#ffffff !important; font-size:14px !important;
}
.stSelectbox > div > div {
    background:#0d1b2a !important; border:1px solid #1e3a5f !important;
    border-radius:8px !important; color:#ffffff !important;
}
.stTextInput label, .stSelectbox label {
    color:#ffffff !important; font-size:13px !important; font-weight:700 !important;
}

/* Buttons */
.stButton > button {
    background:linear-gradient(135deg,#e8612c,#c44d22) !important;
    color:white !important; border:none !important; border-radius:10px !important;
    font-weight:700 !important; padding:10px 20px !important; width:100% !important;
    transition:all 0.2s !important; font-size:14px !important;
}
.stButton > button:hover { opacity:0.85 !important; transform:translateY(-1px) !important; }

/* Metric labels */
div[data-testid="stMetricLabel"] p { color:#ffffff !important; font-size:12px !important; font-weight:700 !important; }
div[data-testid="stMetricValue"]    { color:#ffffff !important; font-weight:900 !important; }

/* Headings */
h1,h2,h3,h4,h5,h6 { color:#ffffff !important; }
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3,
.stMarkdown h4,.stMarkdown h5 { color:#ffffff !important; }
.stMarkdown p { color:#e2e8f0 !important; }

/* Expander */
.streamlit-expanderHeader p { color:#ffffff !important; font-weight:700 !important; }
details summary p            { color:#ffffff !important; font-weight:700 !important; }

/* Progress */
.stProgress > div > div > div { background:linear-gradient(90deg,#e8612c,#22c55e) !important; border-radius:6px !important; }
.stProgress > div > div       { background:#1e3a5f !important; border-radius:6px !important; }

/* Alerts */
div[data-testid="stAlert"] p { color:#ffffff !important; font-weight:600 !important; }

/* Chat bubbles */
.user-bubble {
    background:linear-gradient(135deg,#1e3a5f,#162d4a);
    border:1px solid #2d5a8e; border-radius:20px 4px 20px 20px;
    padding:14px 20px; margin:10px 0 10px 15%;
    color:#ffffff; font-size:14px; line-height:1.7;
}
.bot-bubble {
    background:linear-gradient(135deg,#0d1b2a,#0a1628);
    border:1px solid #1e3a5f; border-radius:4px 20px 20px 20px;
    padding:14px 20px; margin:10px 15% 10px 0;
    color:#e2e8f0; font-size:14px; line-height:1.8; white-space:pre-wrap;
}

/* Step bar */
.step-divider { border-top:1px solid #1e3a5f; margin:8px 0 18px 0; }
</style>
""", unsafe_allow_html=True)


# ─── SESSION STATE ─────────────────────────────────────────────────────────────
def init():
    defaults = {
        "page":          "welcome",   # welcome|login|district|chat|analysis
        "officer":       None,
        "district_info": None,
        "suggestion":    None,
        "chat":          [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─── STEP BAR ─────────────────────────────────────────────────────────────────
STEPS = ["Welcome", "Login", "District", "Chat", "Analysis"]

def step_bar():
    page_to_step = {
        "welcome": 1, "login": 2, "district": 3, "chat": 4, "analysis": 5
    }
    current = page_to_step.get(st.session_state.page, 1)
    cols = st.columns(len(STEPS))
    for i, (col, lbl) in enumerate(zip(cols, STEPS)):
        n      = i + 1
        done   = n < current
        active = n == current
        bg  = "#e8612c"               if done   else ("rgba(232,97,44,0.2)" if active else "#0d1b2a")
        c   = "#e8612c"               if (done or active) else "#1e3a5f"
        tc  = "white"                 if done   else ("#e8612c" if active else "#334155")
        sym = "✓" if done else str(n)
        fw  = "800" if active else "400"
        with col:
            st.markdown(
                f'<div style="text-align:center;">'
                f'<div style="width:30px;height:30px;border-radius:50%;background:{bg};'
                f'border:2px solid {c};display:inline-flex;align-items:center;'
                f'justify-content:center;color:{tc};font-size:11px;font-weight:800;">{sym}</div>'
                f'<div style="font-size:9px;color:{c};margin-top:3px;font-weight:{fw};">{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    st.markdown('<div class="step-divider"></div>', unsafe_allow_html=True)


# ─── TOP BANNER ───────────────────────────────────────────────────────────────
def banner():
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown(
            '<div style="background:linear-gradient(90deg,#e8612c 0%,#c44d22 100%);'
            'border-radius:12px;padding:14px 24px;margin-bottom:8px;'
            'display:flex;align-items:center;gap:14px;">'
            '<span style="font-size:26px;">📮</span>'
            '<div>'
            '<div style="color:white;font-weight:900;font-size:17px;letter-spacing:1.5px;">'
            'POSTBOT — INDIA POST INFRASTRUCTURE AI</div>'
            '<div style="color:rgba(255,255,255,0.65);font-size:11px;margin-top:1px;">'
            'Department of Posts, Ministry of Communications &nbsp;|&nbsp; '
            'Group 10 · Great Lakes PGP · Powered by Groq AI</div>'
            '</div></div>',
            unsafe_allow_html=True
        )
    with c2:
        o = st.session_state.get("officer")
        if o:
            st.markdown(
                f'<div style="background:#0a1628;border:1px solid #e8612c50;'
                f'border-radius:10px;padding:10px 14px;text-align:center;">'
                f'<div style="color:#e8612c;font-size:22px;">👤</div>'
                f'<div style="color:#ffffff;font-weight:700;font-size:13px;">{o["name"]}</div>'
                f'<div style="color:#e2e8f0;font-size:10px;">{o["role"]}</div>'
                f'<div style="color:#94a3b8;font-size:10px;">{o["id"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 1 — WELCOME
# ══════════════════════════════════════════════════════════════════════════════
def welcome_page():
    # No sidebar on welcome
    with st.sidebar:
        st.markdown(
            '<div style="background:#0a1628;border-radius:10px;padding:20px;'
            'text-align:center;margin-top:20px;">'
            '<div style="font-size:40px;">📮</div>'
            '<div style="color:#e2e8f0;font-size:14px;margin-top:8px;font-weight:600;">'
            'Please login to access PostBot</div>'
            '</div>',
            unsafe_allow_html=True
        )

    banner()
    step_bar()

    # Hero — using columns to avoid HTML rendering issues
    st.markdown(
        '<div style="background:linear-gradient(135deg,#0a1628 0%,#0d1e33 50%,#0a1628 100%);'
        'border:1px solid #1e3a5f;border-radius:16px;padding:28px 36px;'
        'text-align:center;margin:8px 0 24px 0;">'
        '<div style="font-size:52px;margin-bottom:12px;">📮</div>'
        '<div style="color:#ffffff;font-weight:900;font-size:28px;margin-bottom:10px;">'
        'Welcome to PostBot</div>'
        '<div style="color:#94a3b8;font-size:14px;line-height:1.7;max-width:650px;margin:auto;">'
        "India Post's AI-powered District Infrastructure Efficiency System.<br>"
        'Analyse postal office data, understand delivery performance,'
        ' and get targeted AI recommendations — all in minutes.'
        '</div></div>',
        unsafe_allow_html=True
    )
    # Badge row using native columns (avoids HTML entity issues)
    b1, b2, b3, b4 = st.columns(4)
    badges = [
        (b1, "📊 754 Districts",  "#22c55e", "#052010", "#22c55e50"),
        (b2, "🤖 Groq Llama 3.3", "#3b82f6", "#030d1e", "#3b82f650"),
        (b3, "📍 36 States & UTs","#eab308", "#0c0a00", "#eab30850"),
        (b4, "🗓️ Group 10",        "#a78bfa", "#0a0714", "#a78bfa50"),
    ]
    for col, txt, color, bg, border in badges:
        with col:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {border};border-radius:20px;'
                f'padding:8px 14px;text-align:center;color:{color};font-size:12px;'
                f'font-weight:700;margin:0 4px;">{txt}</div>',
                unsafe_allow_html=True
            )
    st.markdown("<br>", unsafe_allow_html=True)

    # Feature cards
    st.markdown("<h4 style='color:white;font-weight:800;margin:20px 0 12px;'>🔍 What PostBot Does For You</h4>",
                unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    features = [
        (f1,"📦","Real Dataset","#22c55e","#052010",
         "Fetches actual BO, PO, HO counts for any district directly from the India Post dataset."),
        (f2,"📊","Delivery Analysis","#3b82f6","#030d1e",
         "Shows current delivery rate and classifies district as Low / Moderate / Good / High."),
        (f3,"💡","Smart Suggestions","#e8612c","#120800",
         "Calculates exactly how many Branch Offices to add to reach the next performance tier."),
        (f4,"🤖","AI Chatbot","#a78bfa","#0a0714",
         "Ask PostBot anything about the district — what-if scenarios, explanations, action plans."),
    ]
    for col, icon, title, color, bg, desc in features:
        with col:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {color}40;border-radius:12px;'
                f'padding:20px 16px;min-height:170px;transition:all 0.2s;">'
                f'<div style="font-size:32px;margin-bottom:10px;">{icon}</div>'
                f'<div style="color:{color};font-weight:800;font-size:14px;margin-bottom:8px;">{title}</div>'
                f'<div style="color:#e2e8f0;font-size:12px;line-height:1.7;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Office type explainer
    st.markdown("<h4 style='color:white;font-weight:800;margin:28px 0 12px;'>📖 The 3 Types of Post Offices</h4>",
                unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)
    types = [
        (e1,"🟩","Branch Post Office (BO)","#22c55e","#052010","98.7%",
         "Most common in villages. Deliver almost all mail. More BOs = better delivery rate."),
        (e2,"🟧","Sub Post Office (PO)","#f97316","#120800","76.2%",
         "Town-level offices. 1 in 4 has NO active delivery — biggest gap in the system."),
        (e3,"🟦","Head Post Office (HO)","#3b82f6","#030d1e","99.1%",
         "District headquarters. Very reliable but only 1–3 exist per district."),
    ]
    for col, icon, name, color, bg, rate, desc in types:
        with col:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {color}40;border-radius:12px;padding:20px;">'
                f'<div style="color:{color};font-size:16px;font-weight:800;margin-bottom:4px;">{icon} {name}</div>'
                f'<div style="color:{color};font-size:38px;font-weight:900;font-family:monospace;margin:8px 0;">{rate}</div>'
                f'<div style="color:#a3a3a3;font-size:11px;margin-bottom:8px;">delivery rate</div>'
                f'<div style="color:#e2e8f0;font-size:12px;line-height:1.6;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Performance tiers
    st.markdown("<h4 style='color:white;font-weight:800;margin:28px 0 12px;'>🎯 Performance Tiers</h4>",
                unsafe_allow_html=True)
    t1,t2,t3,t4 = st.columns(4)
    tiers = [
        (t1,"🔴","Low Performance","#ef4444","#120404","Below 70%","Needs urgent restructuring"),
        (t2,"🟡","Moderate","#eab308","#0c0a00","70% – 85%","Below national average (94.8%)"),
        (t3,"🔵","Good Performance","#3b82f6","#030d1e","85% – 95%","Above average — well managed"),
        (t4,"🟢","High Performance","#22c55e","#052010","Above 95%","Top tier — national benchmark"),
    ]
    for col, emoji, lbl, color, bg, rng, desc in tiers:
        with col:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {color}40;border-radius:12px;'
                f'padding:16px;text-align:center;">'
                f'<div style="font-size:28px;">{emoji}</div>'
                f'<div style="color:{color};font-weight:800;font-size:14px;margin:6px 0;">{lbl}</div>'
                f'<div style="color:#ffffff;font-size:20px;font-weight:900;">{rng}</div>'
                f'<div style="color:#e2e8f0;font-size:11px;margin-top:6px;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
    _, cc, _ = st.columns([1,2,1])
    with cc:
        if st.button("🚀  GET STARTED — LOGIN", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 2 — LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def login_page():
    with st.sidebar:
        st.markdown(
            '<div style="background:#0a1628;border:1px solid #1e3a5f;border-radius:10px;'
            'padding:16px;text-align:center;margin-top:10px;">'
            '<div style="font-size:32px;">🔐</div>'
            '<div style="color:#e2e8f0;font-size:13px;margin-top:8px;">'
            'Enter your credentials to access PostBot</div>'
            '</div>',
            unsafe_allow_html=True
        )

    banner()
    step_bar()

    _, cc, _ = st.columns([1,2,1])
    with cc:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0a1628,#0d1e33);border:1px solid #1e3a5f;
                    border-radius:16px;padding:40px 36px;margin-top:10px;">
          <div style="text-align:center;margin-bottom:30px;">
            <div style="font-size:52px;">🔐</div>
            <div style="color:#ffffff;font-weight:900;font-size:24px;margin-top:12px;">Officer Login</div>
            <div style="color:#e2e8f0;font-size:12px;margin-top:6px;letter-spacing:1px;">
              INDIA POST — AUTHORISED ACCESS ONLY
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        officer_id = st.text_input("🪪  Officer ID", placeholder="e.g. IP2024KA001  or  DEMO")
        password   = st.text_input("🔒  Password",   placeholder="Enter your password", type="password")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🔐  LOGIN TO POSTBOT", use_container_width=True):
            if not officer_id.strip() or not password.strip():
                st.error("⚠️ Please enter both Officer ID and Password.")
            else:
                officer = authenticate(officer_id.strip(), password.strip())
                if officer:
                    st.session_state.officer = officer
                    st.session_state.page    = "district"
                    st.session_state.chat    = []
                    st.session_state.district_info = None
                    st.session_state.suggestion    = None
                    st.rerun()
                else:
                    st.error("❌ Invalid Officer ID or Password. Please check and try again.")

        with st.expander("📋 Demo Login Credentials — click to view"):
            for d in get_demo_credentials():
                ca, cb = st.columns([3,2])
                with ca:
                    st.code(f"{d['id']}  /  {d['pw']}")
                with cb:
                    st.markdown(f"<span style='color:#e2e8f0;font-size:12px;'>{d['name']} · {d['circle']}</span>",
                                unsafe_allow_html=True)

        if st.button("← Back to Welcome", key="back_welcome"):
            st.session_state.page = "welcome"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 3 — DISTRICT SELECTION
# Dropdowns are in the MAIN area (always visible, no sidebar dependency)
# Sidebar: officer info only
# ══════════════════════════════════════════════════════════════════════════════
def district_page(df):
    o = st.session_state.officer

    # ── SIDEBAR: officer card + state/district dropdowns + buttons ────────────
    with st.sidebar:
        # Officer card
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#0a1628,#0d1e33);'
            f'border:1px solid #e8612c50;border-radius:12px;padding:14px;margin-bottom:16px;">'
            f'<div style="color:#e8612c;font-size:10px;font-weight:800;letter-spacing:2px;'
            f'margin-bottom:6px;">👤 LOGGED IN AS</div>'
            f'<div style="color:#ffffff;font-weight:800;font-size:15px;">{o["name"]}</div>'
            f'<div style="color:#e2e8f0;font-size:11px;margin-top:2px;">{o["role"]}</div>'
            f'<div style="color:#e2e8f0;font-size:11px;">Circle: {o["circle"]}</div>'
            f'<div style="color:#94a3b8;font-size:10px;margin-top:2px;">{o["id"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Select district header
        st.markdown(
            '<div style="background:#e8612c;border-radius:8px;padding:9px;'
            'text-align:center;margin-bottom:14px;">'
            '<span style="color:white;font-weight:800;font-size:13px;letter-spacing:1px;">'
            '📍 SELECT YOUR DISTRICT</span></div>',
            unsafe_allow_html=True
        )

        states    = get_states(df)
        sel_st_t  = st.selectbox(
            "🗺️ State",
            ["-- Select State --"] + [s.title() for s in states],
            key="sb_state_d"
        )
        fetch_clicked = False
        sel_state = sel_dist = ""

        if sel_st_t == "-- Select State --":
            st.info("👆 Select a state to see districts")
        else:
            sel_state = sel_st_t.upper()
            dists     = get_districts(df, sel_state)
            sel_dt_t  = st.selectbox(
                f"📍 District  ({len(dists)} available)",
                ["-- Select District --"] + [d.title() for d in dists],
                key="sb_dist_d"
            )
            if sel_dt_t != "-- Select District --":
                sel_dist = sel_dt_t.upper()
                preview  = get_district_info(df, sel_state, sel_dist)
                if preview:
                    tier = get_tier(preview['district_delivery_rate'])
                    st.markdown(
                        f'<div style="background:{tier["bg"]};border:1px solid {tier["color"]}50;'
                        f'border-radius:10px;padding:12px;margin:10px 0;">'
                        f'<div style="color:#ffffff;font-size:9px;font-weight:800;'
                        f'letter-spacing:1.5px;margin-bottom:6px;">PREVIEW</div>'
                        f'<div style="color:{tier["color"]};font-size:26px;font-weight:900;'
                        f'font-family:monospace;">{preview["district_delivery_rate"]*100:.1f}%</div>'
                        f'<div style="color:#e2e8f0;font-size:11px;margin-top:5px;">'
                        f'🟩 {preview["bo_count"]} &nbsp; '
                        f'🟧 {preview["po_count"]} &nbsp; '
                        f'🟦 {preview["ho_count"]}</div>'
                        f'<div style="color:{tier["color"]};font-size:11px;font-weight:700;margin-top:4px;">'
                        f'{tier["emoji"]} {tier["label"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                fetch_clicked = st.button(
                    "📊  ANALYSE DISTRICT",
                    use_container_width=True,
                    key="fetch_sidebar"
                )

        st.markdown("---")
        if st.button("🚪  Logout", use_container_width=True, key="logout_d"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # ── MAIN AREA ─────────────────────────────────────────────────────────────
    banner()
    step_bar()

    # Welcome card + dataset stats
    col_msg, col_stats = st.columns([3, 2])
    with col_msg:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#0a1628,#0d1e33);'
            f'border:1px solid #1e3a5f;border-radius:16px;padding:24px;margin-bottom:16px;">'
            f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">'
            f'<div style="width:46px;height:46px;border-radius:50%;flex-shrink:0;'
            f'background:linear-gradient(135deg,#e8612c,#c44d22);'
            f'display:flex;align-items:center;justify-content:center;font-size:22px;">📮</div>'
            f'<div>'
            f'<div style="color:#ffffff;font-size:20px;font-weight:900;">'
            f'👋 Welcome, {o["name"]}!</div>'
            f'<div style="color:#e2e8f0;font-size:12px;">{o["role"]} — {o["circle"]} Circle</div>'
            f'</div></div>'
            f'<div style="color:#e2e8f0;font-size:14px;line-height:1.8;margin-bottom:14px;">'
            f"I'm <strong style='color:#e8612c;'>PostBot</strong> — your AI assistant for India Post infrastructure."
            f'</div>'
            f'<div style="color:#ffffff;font-weight:700;font-size:13px;margin-bottom:8px;">📌 What I can do:</div>'
            f'<div style="color:#e2e8f0;font-size:13px;line-height:2;">'
            f'📦 Real <strong>BO / PO / HO counts</strong> for any district<br>'
            f'📊 Current <strong>delivery rate</strong> and performance tier<br>'
            f'💡 Exact <strong>recommendations</strong> to improve<br>'
            f'🤖 <strong>What-if simulations</strong> — add offices, see impact'
            f'</div></div>',
            unsafe_allow_html=True
        )
    with col_stats:
        st.markdown("<h4 style='color:white;font-weight:800;'>📊 Dataset Overview</h4>",
                    unsafe_allow_html=True)
        for val, lbl, color, bg in [
            ("165,627","Total Post Offices","#22c55e","#052010"),
            ("754",    "Districts",          "#3b82f6","#030d1e"),
            ("36",     "States & UTs",       "#eab308","#0c0a00"),
            ("94.8%",  "National Avg Rate",  "#a78bfa","#0a0714"),
        ]:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {color}40;border-radius:10px;'
                f'padding:10px 16px;margin-bottom:8px;display:flex;'
                f'justify-content:space-between;align-items:center;">'
                f'<span style="color:#e2e8f0;font-size:13px;font-weight:600;">{lbl}</span>'
                f'<span style="color:{color};font-size:18px;font-weight:900;font-family:monospace;">{val}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Handle fetch
    if fetch_clicked:
        info = get_district_info(df, sel_state, sel_dist)
        if info:
            sugg = calculate_suggestion(
                info['bo_count'], info['po_count'],
                info['ho_count'], info['district_delivery_rate']
            )
            st.session_state.district_info = info
            st.session_state.suggestion    = sugg
            st.session_state.chat          = [{
                "role": "bot",
                "content": (
                    f"📍 District loaded: **{info['district'].title()}, {info['statename'].title()}**\n\n"
                    f"I have the complete data for this district. Here's a quick summary:\n\n"
                    f"• **Total Offices:** {info['total_offices']} "
                    f"(BO: {info['bo_count']}, PO: {info['po_count']}, HO: {info['ho_count']})\n"
                    f"• **Current Delivery Rate:** {info['district_delivery_rate']*100:.1f}%\n"
                    f"• **Performance Tier:** {get_tier(info['district_delivery_rate'])['emoji']} "
                    f"{get_tier(info['district_delivery_rate'])['label']}\n"
                    f"• **BO Ratio:** {info['bo_ratio']*100:.1f}% (target: above 85%)\n\n"
                    f"Ask me anything about this district, or click the **⚡ Quick Questions** "
                    f"below to get started. You can also click the **📊 View Analysis** button "
                    f"(top-right of chat) for the full detailed report."
                )
            }]
            st.session_state.page = "chat"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 4 — CHAT
# Sidebar: officer info + district summary + navigation buttons
# Main: quick questions + chatbot
# Top-right: 📊 Analysis button
# ══════════════════════════════════════════════════════════════════════════════
def chat_page(df):
    o    = st.session_state.officer
    d    = st.session_state.district_info
    sugg = st.session_state.suggestion
    tier = get_tier(d['district_delivery_rate'])

    with st.sidebar:
        # Officer card
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#0a1628,#0d1e33);'
            f'border:1px solid #e8612c50;border-radius:12px;padding:14px;margin-bottom:14px;">'
            f'<div style="color:#e8612c;font-size:9px;font-weight:800;letter-spacing:2px;'
            f'margin-bottom:6px;">👤 LOGGED IN AS</div>'
            f'<div style="color:#ffffff;font-weight:800;font-size:14px;">{o["name"]}</div>'
            f'<div style="color:#e2e8f0;font-size:11px;">{o["role"]} · {o["circle"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # District summary card
        st.markdown(
            f'<div style="background:{tier["bg"]};border:1px solid {tier["color"]}50;'
            f'border-radius:12px;padding:14px;margin-bottom:14px;">'
            f'<div style="color:#ffffff;font-size:9px;font-weight:800;letter-spacing:2px;'
            f'margin-bottom:8px;">📍 CURRENT DISTRICT</div>'
            f'<div style="color:#ffffff;font-weight:800;font-size:14px;">{d["district"].title()}</div>'
            f'<div style="color:#e2e8f0;font-size:11px;">{d["statename"].title()}</div>'
            f'<div style="color:{tier["color"]};font-size:26px;font-weight:900;'
            f'font-family:monospace;margin:6px 0;">{d["district_delivery_rate"]*100:.1f}%</div>'
            f'<div style="color:{tier["color"]};font-size:11px;font-weight:700;">'
            f'{tier["emoji"]} {tier["label"]}</div>'
            f'<div style="color:#e2e8f0;font-size:11px;margin-top:6px;">'
            f'🟩 {d["bo_count"]} &nbsp; 🟧 {d["po_count"]} &nbsp; 🟦 {d["ho_count"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="background:#e8612c20;border:1px solid #e8612c40;border-radius:10px;'
            'padding:10px 12px;margin-bottom:14px;font-size:11px;color:#e2e8f0;">'
            '<strong style="color:#ffffff;">💡 Try asking:</strong><br><br>'
            '• "What if I add 30 BOs?"<br>'
            '• "How to reach 95% delivery?"<br>'
            '• "Why is our BO ratio low?"<br>'
            '• "Give me an action plan"'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")
        if st.button("📊  View Full Analysis", use_container_width=True, key="goto_analysis"):
            st.session_state.page = "analysis"
            st.rerun()
        if st.button("🔄  Change District", use_container_width=True, key="change_d"):
            st.session_state.district_info = None
            st.session_state.suggestion    = None
            st.session_state.chat          = []
            st.session_state.page          = "district"
            st.rerun()
        if st.button("🚪  Logout", use_container_width=True, key="logout_c"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # ── Main: banner + step bar ───────────────────────────────────────────────
    banner()
    step_bar()

    dist_t   = d['district'].title()
    rate_pct = round(d['district_delivery_rate'] * 100, 1)
    bo_pct   = round(d['bo_ratio'] * 100, 1)

    # ── Top row: district summary card (clickable dropdown) + analysis button ─
    tc1, tc2 = st.columns([4, 1])
    with tc1:
        with st.expander(
            f"{tier['emoji']} {d['district'].title()}, {d['statename'].title()}   "
            f"·   Delivery Rate: {rate_pct}%   ·   {tier['label']}   "
            f"·   BO: {d['bo_count']} | PO: {d['po_count']} | HO: {d['ho_count']}",
            expanded=False
        ):
            # Bot summary message inside expander
            for msg in st.session_state.chat:
                if msg["role"] == "bot":
                    st.markdown(
                        f'<div style="background:#0a1628;border:1px solid #1e3a5f;'
                        f'border-radius:10px;padding:14px 18px;color:#e2e8f0;'
                        f'font-size:13px;line-height:1.8;white-space:pre-wrap;">'
                        f'📮 &nbsp; {msg["content"]}</div>',
                        unsafe_allow_html=True
                    )
                    break  # only show the first bot message (district summary)
    with tc2:
        st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
        if st.button("📊  View Full Analysis →", use_container_width=True, key="analysis_top"):
            st.session_state.page = "analysis"
            st.rerun()

    # ── Chat messages (skip first bot message — shown in expander) ────────────
    chat_to_show = st.session_state.chat[1:] if len(st.session_state.chat) > 1 else []
    for msg in chat_to_show:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="user-bubble">👤 &nbsp; {msg["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="bot-bubble">📮 &nbsp; {msg["content"]}</div>',
                unsafe_allow_html=True
            )

    # ── Chat input ────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="background:linear-gradient(135deg,#0a1628,#0d1e33);'
        'border:1px solid #1e3a5f;border-radius:12px;padding:16px 20px;margin-top:12px;">'
        '<div style="color:#ffffff;font-weight:800;font-size:14px;margin-bottom:10px;">'
        '✍️ Ask PostBot Anything About This District</div>',
        unsafe_allow_html=True
    )
    ci, cb = st.columns([5, 1])
    with ci:
        user_q = st.text_input(
            "q", label_visibility="collapsed",
            placeholder="e.g. What if I add 50 BOs?  /  Why is delivery rate low?  /  How to reach top tier?",
            key="q_input"
        )
    with cb:
        send = st.button("➤ Ask", use_container_width=True, key="send_btn")
    st.markdown('</div>', unsafe_allow_html=True)

    if send and user_q.strip():
        _send_bot(user_q.strip())

    # ── Quick Questions dropdown (BELOW chat input) ───────────────────────────
    with st.expander("⚡ Quick Questions — Click to Ask PostBot", expanded=False):
        st.markdown(
            '<div style="color:#e2e8f0;font-size:12px;margin-bottom:12px;">'
            'Not sure what to ask? Click any question below to send it instantly.</div>',
            unsafe_allow_html=True
        )
        chip_q = None
        q1,q2 = st.columns(2)
        q3,q4 = st.columns(2)
        with q1:
            if st.button(f"➕ If I add 30 BOs to {dist_t}, what will the new delivery rate be?",
                         key="c1", use_container_width=True):
                chip_q = f"If I add 30 Branch Offices to {dist_t}, what will the new delivery rate be? Show step-by-step calculation."
        with q2:
            if st.button(f"🎯 How many BOs needed to reach 95% delivery in {dist_t}?",
                         key="c2", use_container_width=True):
                chip_q = f"How many Branch Offices do I need to add to {dist_t} to reach 95% delivery rate? Show the math."
        with q3:
            if st.button(f"🔄 What happens if I activate all inactive POs in {dist_t}?",
                         key="c3", use_container_width=True):
                chip_q = f"How much will delivery rate improve in {dist_t} if all non-delivering Sub Post Offices are activated?"
        with q4:
            if st.button(f"📋 Give me a 5-step action plan to improve {dist_t}",
                         key="c4", use_container_width=True):
                chip_q = f"Give me a detailed 5-step action plan to improve delivery rate in {dist_t} to the next tier."
        if chip_q:
            _send_bot(chip_q)


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 5 — ANALYSIS (only when icon clicked)
# Shows: office counts + delivery rate + tier + recommendations + before/after
# ══════════════════════════════════════════════════════════════════════════════
def analysis_page():
    o    = st.session_state.officer
    d    = st.session_state.district_info
    sugg = st.session_state.suggestion
    tier = get_tier(d['district_delivery_rate'])
    rate_pct = round(d['district_delivery_rate'] * 100, 1)
    bo_pct   = round(d['bo_ratio'] * 100, 1)

    with st.sidebar:
        st.markdown(
            f'<div style="background:#0a1628;border:1px solid #e8612c50;border-radius:12px;'
            f'padding:14px;margin-bottom:14px;">'
            f'<div style="color:#e8612c;font-size:9px;font-weight:800;letter-spacing:2px;'
            f'margin-bottom:6px;">👤 LOGGED IN AS</div>'
            f'<div style="color:#ffffff;font-weight:800;font-size:14px;">{o["name"]}</div>'
            f'<div style="color:#e2e8f0;font-size:11px;">{o["role"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown("---")
        if st.button("💬  Back to Chat", use_container_width=True, key="back_chat"):
            st.session_state.page = "chat"
            st.rerun()
        if st.button("🔄  Change District", use_container_width=True, key="change_a"):
            st.session_state.district_info = None
            st.session_state.suggestion    = None
            st.session_state.chat          = []
            st.session_state.page          = "district"
            st.rerun()
        if st.button("🚪  Logout", use_container_width=True, key="logout_a"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    banner()
    step_bar()

    # Page header
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#0a1628,#0d1e33);'
        f'border:1px solid {tier["color"]}60;border-left:5px solid {tier["color"]};'
        f'border-radius:12px;padding:18px 24px;margin-bottom:20px;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;">'
        f'<div>'
        f'<div style="color:#ffffff;font-size:22px;font-weight:900;">'
        f'📊 Full Analysis — {d["district"].title()}</div>'
        f'<div style="color:#e2e8f0;font-size:13px;margin-top:4px;">'
        f'{d["statename"].title()} &nbsp;·&nbsp; Total Offices: {d["total_offices"]}'
        f'</div></div>'
        f'<div style="text-align:right;">'
        f'<div style="color:{tier["color"]};font-size:40px;font-weight:900;font-family:monospace;">'
        f'{rate_pct}%</div>'
        f'<div style="color:#e2e8f0;font-size:10px;letter-spacing:1px;">DELIVERY RATE</div>'
        f'<div style="color:{tier["color"]};font-size:12px;font-weight:700;margin-top:2px;">'
        f'{tier["emoji"]} {tier["label"]}</div>'
        f'</div></div></div>',
        unsafe_allow_html=True
    )

    # ── Section A: Office Counts ───────────────────────────────────────────────
    st.markdown("<h4 style='color:white;font-weight:800;margin:0 0 12px;'>📦 Current Office Counts</h4>",
                unsafe_allow_html=True)

    bo_del = int(d['bo_count'] * 0.987)
    po_del = int(d['po_count'] * 0.762)
    po_no  = d['po_count'] - po_del
    ho_del = int(d['ho_count'] * 0.991)

    a1,a2,a3,a4 = st.columns(4)
    office_cards = [
        (a1, "🟩 Branch Offices (BO)", d['bo_count'], "#22c55e", "#052010",
         f"✅ {bo_del} actively delivering", "98.7% delivery rate"),
        (a2, "🟧 Sub Post Offices (PO)", d['po_count'], "#f97316", "#120800",
         f"⚠️ {po_no} NOT delivering", "Only 76.2% delivery rate"),
        (a3, "🟦 Head Offices (HO)", d['ho_count'], "#3b82f6", "#030d1e",
         f"✅ {ho_del} actively delivering", "99.1% delivery rate"),
        (a4, "📦 Total Offices", d['total_offices'], "#a78bfa", "#0a0714",
         f"BO ratio: {bo_pct}%", "Target: above 85%"),
    ]
    for col, lbl, val, color, bg, sub1, sub2 in office_cards:
        with col:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {color}50;border-radius:12px;'
                f'padding:16px;text-align:center;">'
                f'<div style="color:#ffffff;font-size:12px;font-weight:700;margin-bottom:8px;">{lbl}</div>'
                f'<div style="color:{color};font-size:38px;font-weight:900;font-family:monospace;">{val}</div>'
                f'<div style="color:#e2e8f0;font-size:11px;margin-top:6px;">{sub1}</div>'
                f'<div style="color:#e2e8f0;font-size:10px;margin-top:3px;">{sub2}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section B: Delivery Rate + BO Ratio side by side ─────────────────────
    st.markdown("<h4 style='color:white;font-weight:800;margin:0 0 12px;'>📊 Delivery Rate & BO Ratio</h4>",
                unsafe_allow_html=True)

    b1, b2 = st.columns(2)
    with b1:
        nat_avg = 94.8
        vs_nat  = round(rate_pct - nat_avg, 1)
        sign    = "+" if vs_nat >= 0 else ""
        nc      = "#22c55e" if vs_nat >= 0 else "#ef4444"
        above   = "Above" if vs_nat >= 0 else "Below"
        st.markdown(
            f'<div style="background:{tier["bg"]};border:1px solid {tier["color"]}50;'
            f'border-radius:12px;padding:20px;">'
            f'<div style="color:#ffffff;font-size:10px;font-weight:800;letter-spacing:2px;'
            f'margin-bottom:10px;">PERFORMANCE LEVEL</div>'
            f'<div style="color:{tier["color"]};font-size:52px;font-weight:900;'
            f'font-family:monospace;line-height:1;">{rate_pct}%</div>'
            f'<div style="color:{tier["color"]};font-size:18px;font-weight:800;margin:8px 0;">'
            f'{tier["emoji"]} {tier["label"]}</div>'
            f'<div style="color:#e2e8f0;font-size:13px;line-height:1.6;margin-bottom:12px;">'
            f'{tier["description"]}</div>'
            f'<div style="background:#060d18;border-radius:8px;padding:10px 14px;">'
            f'<span style="color:#e2e8f0;font-size:12px;">vs National avg ({nat_avg}%): </span>'
            f'<span style="color:{nc};font-weight:700;font-size:13px;">'
            f'{above} ({sign}{vs_nat}%)</span>'
            f'</div></div>',
            unsafe_allow_html=True
        )
    with b2:
        bos_need  = max(0, int((0.85 - d['bo_ratio']) * d['total_offices']))
        bar_color = "#22c55e" if d['bo_ratio'] >= 0.85 else "#f97316"
        st.markdown(
            f'<div style="background:#0a1628;border:1px solid #1e3a5f;border-radius:12px;padding:20px;">'
            f'<div style="color:#ffffff;font-size:10px;font-weight:800;letter-spacing:2px;'
            f'margin-bottom:10px;">BO RATIO — #1 PREDICTOR (r=+0.87)</div>'
            f'<div style="color:{bar_color};font-size:48px;font-weight:900;font-family:monospace;">'
            f'{bo_pct}%</div>',
            unsafe_allow_html=True
        )
        st.progress(min(1.0, d['bo_ratio']),
                    text=f"Current: {bo_pct}%  |  Target: 85%")
        if d['bo_ratio'] >= 0.85:
            st.success("✅ BO ratio above 85% — strong delivery infrastructure.")
        else:
            st.warning(f"⚠️ Need **{bos_need} more Branch Offices** to reach 85% target.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section C: Recommendations ────────────────────────────────────────────
    st.markdown("<h4 style='color:white;font-weight:800;margin:0 0 12px;'>💡 Recommendations to Improve</h4>",
                unsafe_allow_html=True)

    if sugg['already_top']:
        st.success(
            f"🏆 **Top Tier — Excellent!** {d['district'].title()} is already at "
            f"High Performance ({rate_pct}%). Focus on maintaining quality."
        )
    else:
        nt       = sugg['next_tier']
        exp_rate = round(sugg['expected_rate'] * 100, 1)
        impr     = sugg['improvement']

        st.info(f"**Target:** {tier['emoji']} {tier['label']}  →  {nt['emoji']} {nt['label']}")

        c1,c2,c3 = st.columns(3)
        for col, lbl, val, color, sub in [
            (c1, "ADD BRANCH OFFICES",  f"+{sugg['bo_to_add']}", "#e8612c", f"Current {d['bo_count']} → New {sugg['new_bo']}"),
            (c2, "EXPECTED NEW RATE",   f"{exp_rate}%",          "#22c55e", f"Up from {rate_pct}%"),
            (c3, "IMPROVEMENT",         f"+{impr}%",             "#3b82f6", f"{tier['emoji']} → {nt['emoji']} tier"),
        ]:
            with col:
                st.markdown(
                    f'<div style="background:#0a1628;border:2px solid {color};'
                    f'border-radius:12px;padding:20px;text-align:center;">'
                    f'<div style="color:#ffffff;font-size:10px;font-weight:800;'
                    f'letter-spacing:1px;margin-bottom:8px;">{lbl}</div>'
                    f'<div style="color:{color};font-size:42px;font-weight:900;font-family:monospace;">{val}</div>'
                    f'<div style="color:#e2e8f0;font-size:12px;margin-top:8px;">{sub}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # Before → After
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:white;font-weight:800;margin:0 0 12px;'>📋 Before → After Comparison</h4>",
                    unsafe_allow_html=True)
        ba1, mid, ba2 = st.columns([5,1,5])
        br_cur = round(d['bo_ratio']*100,1)
        br_aft = round(sugg.get('bo_ratio_after',0)*100,1)
        with ba1:
            st.markdown(
                f'<div style="background:{tier["bg"]};border:1px solid {tier["color"]}50;'
                f'border-radius:12px;padding:20px;text-align:center;">'
                f'<div style="color:{tier["color"]};font-size:11px;font-weight:800;'
                f'letter-spacing:1px;">CURRENT STATE</div>'
                f'<div style="color:{tier["color"]};font-size:40px;font-weight:900;'
                f'font-family:monospace;margin:8px 0;">{rate_pct}%</div>'
                f'<div style="color:#e2e8f0;font-size:14px;font-weight:700;">'
                f'{tier["emoji"]} {tier["label"]}</div>'
                f'<div style="color:#e2e8f0;font-size:12px;margin-top:8px;">'
                f'BO: {d["bo_count"]} &nbsp;|&nbsp; BO ratio: {br_cur}%</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with mid:
            st.markdown(
                '<div style="text-align:center;padding-top:60px;'
                'color:#e8612c;font-size:36px;font-weight:900;">→</div>',
                unsafe_allow_html=True
            )
        with ba2:
            st.markdown(
                f'<div style="background:{nt["bg"]};border:1px solid {nt["color"]}50;'
                f'border-radius:12px;padding:20px;text-align:center;">'
                f'<div style="color:{nt["color"]};font-size:11px;font-weight:800;'
                f'letter-spacing:1px;">AFTER ADDING {sugg["bo_to_add"]} BOs</div>'
                f'<div style="color:{nt["color"]};font-size:40px;font-weight:900;'
                f'font-family:monospace;margin:8px 0;">{exp_rate}%</div>'
                f'<div style="color:#e2e8f0;font-size:14px;font-weight:700;">'
                f'{nt["emoji"]} {nt["label"]}</div>'
                f'<div style="color:#e2e8f0;font-size:12px;margin-top:8px;">'
                f'BO: {sugg["new_bo"]} &nbsp;|&nbsp; BO ratio: {br_aft}%</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        # Quick win tip
        inactive_po = int(d['po_count'] * 0.238)
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(
            f"⚡ **Quick Win:** Approximately **{inactive_po} Sub Post Offices** in this district "
            f"currently have no active delivery. Activating even half would improve the delivery rate "
            f"without adding new offices."
        )

    # Back to chat button
    st.markdown("<br>", unsafe_allow_html=True)
    _, bc, _ = st.columns([1,2,1])
    with bc:
        if st.button("💬  Back to Chat", use_container_width=True, key="back_chat_bottom"):
            st.session_state.page = "chat"
            st.rerun()


# ─── SEND MESSAGE HELPER ──────────────────────────────────────────────────────
def _send_bot(question: str):
    st.session_state.chat.append({"role": "user", "content": question})
    with st.spinner("📮 PostBot is thinking..."):
        reply = ask_postbot(
            question,
            st.session_state.officer,
            st.session_state.district_info,
            st.session_state.suggestion,
            st.session_state.chat
        )
    # Quota fallback
    if "quota" in reply.lower() or "rate_limit" in reply.lower():
        d    = st.session_state.district_info
        sugg = st.session_state.suggestion
        tier = get_tier(d['district_delivery_rate'])
        rate_pct = round(d['district_delivery_rate'] * 100, 1)
        exp_rate = round(sugg['expected_rate'] * 100, 1) if sugg else 0
        reply = (
            "⚠️ **API limit reached temporarily.** Here is the pre-calculated data:\n\n"
            f"**{d['district'].title()}, {d['statename'].title()}**\n"
            f"• Delivery Rate: {rate_pct}% — {tier['emoji']} {tier['label']}\n"
            f"• BO: {d['bo_count']} | PO: {d['po_count']} | HO: {d['ho_count']}\n"
            f"• BO Ratio: {d['bo_ratio']*100:.1f}% (target: 85%)\n"
        )
        if sugg and not sugg['already_top'] and sugg['next_tier']:
            reply += (
                f"• Add **{sugg['bo_to_add']} Branch Offices** → "
                f"rate improves to **{exp_rate}%** (+{sugg['improvement']}%)\n\n"
            )
        reply += "*Please wait 60 seconds and try again.*"

    st.session_state.chat.append({"role": "bot", "content": reply})
    st.rerun()


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
def main():
    init()
    df = load_district_data("district_aggregated.csv")

    page = st.session_state.page

    if page == "welcome":
        welcome_page()
    elif page == "login":
        login_page()
    elif page == "district":
        if not st.session_state.officer:
            st.session_state.page = "login"
            st.rerun()
        district_page(df)
    elif page == "chat":
        if not st.session_state.district_info:
            st.session_state.page = "district"
            st.rerun()
        chat_page(df)
    elif page == "analysis":
        if not st.session_state.district_info:
            st.session_state.page = "district"
            st.rerun()
        analysis_page()
    else:
        st.session_state.page = "welcome"
        st.rerun()


if __name__ == "__main__":
    main()
