import streamlit as st
from typing import Dict, Any, List, Optional

def apply_custom_css():
    """Injects high-end, futuristic Cyber/Academic Black and Neon Green styling."""
    st.markdown("""
        <style>
        /* ══════════════════════════════════════════════
           GLOBAL DARK & NEON GREEN BASE
           ══════════════════════════════════════════════ */
        .stApp {
            background-color: #080808 !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #E6E6E6 !important;
        }

        /* Top Header Area */
        header[data-testid="stHeader"] {
            background-color: #080808 !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0D0D0D !important;
            border-right: 1px solid #1C241E !important;
        }

        [data-testid="stSidebar"] .stRadio label {
            color: #D4D4D4 !important;
            transition: color 0.15s ease;
        }
        [data-testid="stSidebar"] .stRadio label:hover {
            color: #00FF66 !important;
        }

        /* Top Brand Header in Sidebar */
        .edumate-brand {
            padding: 1.25rem 0.75rem 1rem 0.75rem;
            border-bottom: 1px solid #1F2923;
            margin-bottom: 1rem;
            background: linear-gradient(180deg, #121814 0%, #0D0D0D 100%);
            border-radius: 8px;
        }
        .edumate-brand-title {
            font-size: 1.55rem;
            font-weight: 900;
            color: #FFFFFF !important;
            letter-spacing: -0.025em;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-shadow: 0 0 10px rgba(0, 255, 102, 0.35);
        }
        .edumate-brand-title span {
            color: #00FF66 !important;
        }
        .edumate-brand-tagline {
            font-size: 0.8rem;
            color: #00FF66 !important;
            font-weight: 700;
            margin-top: 0.25rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        /* Modern Dashboard Metric Card */
        .metric-card {
            background: #121413 !important;
            border: 1px solid #1E2B22 !important;
            border-left: 4px solid #00FF66 !important;
            border-radius: 10px;
            padding: 1.25rem 1.4rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
            transition: all 0.2s ease;
        }
        .metric-card:hover {
            box-shadow: 0 0 20px rgba(0, 255, 102, 0.2) !important;
            border-color: #00FF66 !important;
            transform: translateY(-2px);
        }
        .metric-title {
            font-size: 0.82rem;
            font-weight: 700;
            color: #8C9990 !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .metric-value {
            font-size: 1.95rem;
            font-weight: 900;
            color: #00FF66 !important;
            margin-top: 0.25rem;
            text-shadow: 0 0 12px rgba(0, 255, 102, 0.3);
        }
        .metric-sub {
            font-size: 0.82rem;
            color: #E0E0E0 !important;
            font-weight: 600;
            margin-top: 0.35rem;
        }

        /* Universal card override for legacy white container blocks */
        div[style*="background-color: #FFFFFF"],
        div[style*="background-color: #ffffff"],
        div[style*="background-color: #F8FAFC"],
        div[style*="background-color: #F0F9FF"],
        div[style*="background-color: #EFF6FF"],
        div[style*="background-color: #FFFBEB"],
        div[style*="background-color: #ECFDF5"],
        div[style*="background: #FFFFFF"],
        div[style*="background:#FFFFFF"] {
            background-color: #121413 !important;
            border-color: #1E2922 !important;
            color: #E6E6E6 !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5) !important;
        }

        /* Headings & Texts inside cards */
        div[style*="color: #1E3A8A"],
        div[style*="color: #0F172A"],
        span[style*="color: #1E3A8A"],
        span[style*="color: #0F172A"],
        b[style*="color: #1E3A8A"] {
            color: #00FF66 !important;
            text-shadow: 0 0 8px rgba(0, 255, 102, 0.25);
        }

        div[style*="color: #475569"],
        div[style*="color: #64748B"],
        div[style*="color: #334155"],
        span[style*="color: #475569"],
        span[style*="color: #64748B"] {
            color: #A3A3A3 !important;
        }

        /* General Headings */
        h1, h2, h3, h4, h5, h6 {
            color: #FFFFFF !important;
        }
        h2 {
            border-bottom: 1px solid #1E2922;
            padding-bottom: 0.4rem;
        }

        /* Primary Buttons - Neon Green Glow */
        .stButton button[kind="primary"] {
            background-color: #00FF66 !important;
            color: #000000 !important;
            font-weight: 800 !important;
            border: 1px solid #00FF66 !important;
            border-radius: 6px !important;
            box-shadow: 0 0 14px rgba(0, 255, 102, 0.4) !important;
            transition: all 0.2s ease !important;
        }
        .stButton button[kind="primary"]:hover {
            background-color: #33FF85 !important;
            box-shadow: 0 0 22px rgba(0, 255, 102, 0.7) !important;
            transform: scale(1.02);
        }

        /* Secondary Buttons */
        .stButton button:not([kind="primary"]) {
            background-color: #141715 !important;
            color: #00FF66 !important;
            border: 1px solid #283D30 !important;
            font-weight: 700 !important;
            border-radius: 6px !important;
            transition: all 0.2s ease !important;
        }
        .stButton button:not([kind="primary"]):hover {
            border-color: #00FF66 !important;
            background-color: #1A221C !important;
            box-shadow: 0 0 10px rgba(0, 255, 102, 0.25) !important;
        }

        /* Input fields and selects */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            background-color: #101211 !important;
            color: #FFFFFF !important;
            border-color: #243329 !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #00FF66 !important;
            box-shadow: 0 0 10px rgba(0, 255, 102, 0.3) !important;
        }

        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            background-color: transparent !important;
            border-bottom: 1px solid #1E2922 !important;
            gap: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #0E100F !important;
            border: 1px solid #1E2922 !important;
            border-radius: 6px 6px 0 0 !important;
            color: #8C9990 !important;
            font-weight: 700 !important;
            padding: 0.5rem 1rem !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #161D18 !important;
            border-color: #00FF66 !important;
            color: #00FF66 !important;
            border-bottom: 2px solid #00FF66 !important;
            text-shadow: 0 0 8px rgba(0, 255, 102, 0.4);
        }

        /* Dataframes & Tables */
        [data-testid="stDataFrame"] {
            border: 1px solid #1E2922 !important;
            border-radius: 8px;
            background-color: #101211 !important;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background-color: #121513 !important;
            border: 1px solid #1E2922 !important;
            border-radius: 8px !important;
            color: #00FF66 !important;
            font-weight: 700 !important;
        }

        /* Horizontal Divider */
        hr {
            border-color: #1A241E !important;
        }

        /* Slider */
        div[data-baseweb="slider"] {
            color: #00FF66 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_brand_sidebar(current_student_name: str, department: str, semester: int):
    """Renders persistent branded sidebar header in black and neon green."""
    st.sidebar.markdown(f"""
        <div class="edumate-brand">
            <div class="edumate-brand-title">
                🎓 <span>EduMate</span>
            </div>
            <div class="edumate-brand-tagline">Academic OS & Companion</div>
            <div style="margin-top: 0.75rem; font-size: 0.85rem; color: #CCCCCC; line-height: 1.4;">
                👤 <b style="color: #00FF66;">{current_student_name}</b><br>
                🏫 <span style="color: #8C9990;">{department} (Sem {semester})</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_metric_card(title: str, value: str, subtext: str = ""):
    """Renders a modern metric card in dark and neon green."""
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{subtext}</div>
        </div>
    """, unsafe_allow_html=True)

def render_alert_box(title: str, message: str, level: str = "warning"):
    """Renders cyber-styled alert callouts."""
    if level == "critical":
        bg = "#1F0A0E"
        fg = "#FF3366"
        border = "#FF3366"
    elif level == "warning":
        bg = "#1A1406"
        fg = "#FFB800"
        border = "#FFB800"
    elif level == "success":
        bg = "#0A1F13"
        fg = "#00FF66"
        border = "#00FF66"
    else:  # info
        bg = "#0A171F"
        fg = "#00E5FF"
        border = "#00E5FF"

    st.markdown(f"""
        <div style="background-color: {bg}; border: 1.5px solid {border}; color: {fg}; border-radius: 8px; padding: 0.9rem 1.1rem; margin-bottom: 0.75rem; box-shadow: 0 0 12px {border}25;">
            <strong style="letter-spacing: 0.03em;">{title}</strong><br>
            <span style="font-size: 0.9rem; color: #E0E0E0; margin-top: 0.25rem; display: block;">{message}</span>
        </div>
    """, unsafe_allow_html=True)
