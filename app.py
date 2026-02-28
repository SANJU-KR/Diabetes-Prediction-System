# ============================================================
# MEDCORE AI — Diabetes Intelligence Platform
# Full-stack Streamlit App with Elite Hospital-Grade UI
# ============================================================

import streamlit as st
import numpy as np
import joblib
import plotly.graph_objects as go
import base64
import re
import pycountry
import phonenumbers
import time
from io import BytesIO
from datetime import datetime
import uuid
import pytz

from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 ListFlowable, ListItem, Table, TableStyle,
                                 Image as RLImage)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def get_base64_image(image_file):
    with open(image_file, "rb") as f:
        return base64.b64encode(f.read()).decode()

def country_to_flag(cc):
    return "".join(chr(127397 + ord(c)) for c in cc.upper())

# ─────────────────────────────────────────
# MONGO
# ─────────────────────────────────────────
uri       = "mongodb+srv://diabetes_user:Diabetes%40123@diabetescluster.oxegep6.mongodb.net/?retryWrites=true&w=majority"
client    = MongoClient(uri, server_api=ServerApi('1'))
db        = client["diabetes_app"]
users_col = db["registered_users"]
preds_col = db["predictions"]

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="MEDCORE AI — Diabetes Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.write("App Loaded Successfully")

# ─────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────
for key, val in [("registered", False), ("patient_info", {}), ("show_success", False)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────────────────────────────────────────────────────
# MASTER CSS
# ─────────────────────────────────────────────────────────────────────────────
def inject_css(img_b64, overlay="rgba(3,6,18,0.83)"):
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Space+Mono:wght@400;700&family=Manrope:wght@300;400;500;600;700;800&display=swap');

    :root {{
        --c-bg:         #03060e;
        --c-surface:    rgba(255,255,255,0.035);
        --c-surface2:   rgba(255,255,255,0.07);
        --c-border:     rgba(255,255,255,0.07);
        --c-border-lit: rgba(0,210,255,0.35);
        --c-cyan:       #00d2ff;
        --c-cyan-dim:   rgba(0,210,255,0.12);
        --c-indigo:     #635bff;
        --c-indigo-dim: rgba(99,91,255,0.12);
        --c-green:      #00e5a0;
        --c-green-dim:  rgba(0,229,160,0.12);
        --c-amber:      #fbbf24;
        --c-amber-dim:  rgba(251,191,36,0.12);
        --c-red:        #f43f5e;
        --c-red-dim:    rgba(244,63,94,0.12);
        --c-text:       #e8eeff;
        --c-muted:      #7580a0;
        --c-dim:        #3a4060;
        --r-sm: 10px; --r-md: 16px; --r-lg: 22px; --r-xl: 30px;
        --shadow-card:  0 4px 24px rgba(0,0,0,0.45), 0 1px 4px rgba(0,0,0,0.3);
        --shadow-glow:  0 0 40px rgba(0,210,255,0.1);
    }}

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; }}

    .stApp {{
        background: linear-gradient({overlay}, {overlay}),
                    url("data:image/png;base64,{img_b64}") center/cover fixed;
        font-family: 'Manrope', sans-serif;
        color: var(--c-text);
        min-height: 100vh;
    }}

    #MainMenu, footer, header, .stDeployButton {{ visibility: hidden !important; display: none !important; }}

    ::-webkit-scrollbar {{ width: 5px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: var(--c-border-lit); border-radius: 99px; }}

    h1, h2, h3, h4, h5 {{
        font-family: 'Outfit', sans-serif !important;
        color: var(--c-text) !important;
        letter-spacing: -0.03em; line-height: 1.15;
    }}
    p, li, span {{ font-family: 'Manrope', sans-serif; color: var(--c-muted); }}

    .gradient-text {{
        background: linear-gradient(110deg, #ffffff 10%, var(--c-cyan) 55%, var(--c-indigo) 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }}

    /* ── CARDS ── */
    .card {{
        background: var(--c-surface);
        backdrop-filter: blur(24px) saturate(1.4);
        -webkit-backdrop-filter: blur(24px) saturate(1.4);
        border: 1px solid var(--c-border);
        border-radius: var(--r-lg);
        padding: 28px 26px;
        box-shadow: var(--shadow-card);
        position: relative;
        transition: border-color .3s, box-shadow .3s, transform .3s;
        overflow: hidden;
    }}
    .card::after {{
        content: ''; position: absolute; inset: 0; border-radius: inherit;
        background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 60%);
        pointer-events: none;
    }}
    .card:hover {{
        border-color: rgba(0,210,255,0.2);
        box-shadow: var(--shadow-card), var(--shadow-glow);
        transform: translateY(-3px);
    }}
    .card-top-glow::before {{
        content: ''; position: absolute; top: 0; left: 15%; right: 15%; height: 1px;
        background: linear-gradient(90deg, transparent, var(--c-cyan), transparent);
    }}
    .card-low  {{ background: linear-gradient(135deg, rgba(0,229,160,0.07), rgba(0,229,160,0.02)); border-color: rgba(0,229,160,0.3); }}
    .card-mod  {{ background: linear-gradient(135deg, rgba(251,191,36,0.07), rgba(251,191,36,0.02)); border-color: rgba(251,191,36,0.3); }}
    .card-high {{ background: linear-gradient(135deg, rgba(244,63,94,0.07), rgba(244,63,94,0.02)); border-color: rgba(244,63,94,0.3); }}

    /* ── PILLS ── */
    .pill {{
        display: inline-flex; align-items: center; gap: 6px;
        background: var(--c-cyan-dim); border: 1px solid rgba(0,210,255,0.25);
        border-radius: 99px; padding: 5px 14px;
        font-family: 'Space Mono', monospace; font-size: 11px;
        color: var(--c-cyan); letter-spacing: 0.06em; white-space: nowrap;
    }}
    .pill-indigo {{ background: var(--c-indigo-dim); border-color: rgba(99,91,255,0.25); color: #a5a0ff; }}
    .pill-green  {{ background: var(--c-green-dim);  border-color: rgba(0,229,160,0.25); color: var(--c-green); }}
    .pill-amber  {{ background: var(--c-amber-dim);  border-color: rgba(251,191,36,0.25); color: var(--c-amber); }}
    .pill-red    {{ background: var(--c-red-dim);    border-color: rgba(244,63,94,0.25); color: var(--c-red); }}

    /* ── RISK BADGES ── */
    .risk-badge {{
        background: rgba(244,63,94,0.07); border-left: 3px solid var(--c-red);
        border-radius: 0 8px 8px 0; padding: 11px 16px; margin-bottom: 8px;
        font-size: 13.5px; color: #fda4b2; font-family: 'Manrope', sans-serif;
    }}
    .safe-badge {{
        background: rgba(0,229,160,0.07); border-left: 3px solid var(--c-green);
        border-radius: 0 8px 8px 0; padding: 11px 16px; margin-bottom: 8px;
        font-size: 13.5px; color: #7cf5cc; font-family: 'Manrope', sans-serif;
    }}

    /* ── SECTION LABEL ── */
    .section-label {{
        display: flex; align-items: center; gap: 10px;
        font-family: 'Space Mono', monospace; font-size: 10px;
        letter-spacing: 0.14em; text-transform: uppercase; color: var(--c-cyan);
        margin: 22px 0 12px;
    }}
    .section-label::after {{
        content: ''; flex: 1; height: 1px;
        background: linear-gradient(90deg, rgba(0,210,255,0.3), transparent);
    }}

    /* ── SIDEBAR ── */
    section[data-testid="stSidebar"] {{
        background: rgba(3,7,20,0.92) !important;
        backdrop-filter: blur(32px) !important;
        -webkit-backdrop-filter: blur(32px) !important;
        border-right: 1px solid var(--c-border) !important;
        box-shadow: 6px 0 40px rgba(0,0,0,0.6) !important;
    }}
    section[data-testid="stSidebar"] > div {{ padding-top: 16px !important; }}
    section[data-testid="stSidebar"] label {{
        color: var(--c-muted) !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 10px !important; letter-spacing: 0.12em !important;
        text-transform: uppercase !important; font-weight: 700 !important;
    }}
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {{
        color: var(--c-muted) !important; font-size: 13px;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background: #f0f4ff !important; border: 1.5px solid #d1d9f0 !important;
        border-radius: var(--r-sm) !important;
        transition: border-color .25s, box-shadow .25s;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {{
        border-color: var(--c-cyan) !important;
        box-shadow: 0 0 0 3px rgba(0,210,255,0.15) !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="input"] input {{
        color: #0d1226 !important; -webkit-text-fill-color: #0d1226 !important;
        font-family: 'Space Mono', monospace !important; font-size: 14px !important; font-weight: 700 !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="select"] span {{
        color: #0d1226 !important; font-weight: 700 !important; font-size: 13px !important;
    }}
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {{ -webkit-appearance: none; }}
    input[type="number"] {{ -moz-appearance: textfield; }}
    div[data-baseweb="slider"] [role="slider"] {{
        background: var(--c-cyan) !important; border: 2px solid white !important;
        box-shadow: 0 0 12px rgba(0,210,255,0.6) !important;
    }}
    div[data-testid="stTickBar"] {{ display: none !important; }}

    /* ── BUTTONS ── */
    section[data-testid="stSidebar"] button {{
        background: linear-gradient(135deg, var(--c-cyan) 0%, var(--c-indigo) 100%) !important;
        border: none !important; color: #030612 !important;
        font-family: 'Outfit', sans-serif !important; font-weight: 800 !important;
        font-size: 13px !important; letter-spacing: 0.05em !important;
        border-radius: var(--r-md) !important; height: 46px !important;
        text-transform: uppercase !important; transition: all .3s ease !important;
        box-shadow: 0 4px 20px rgba(0,210,255,0.25) !important;
    }}
    section[data-testid="stSidebar"] button:hover {{
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 30px rgba(0,210,255,0.4) !important;
    }}
    div.stDownloadButton > button {{
        background: linear-gradient(135deg, #00e5a0, #00a86b) !important;
        border: none !important; color: #011a0d !important;
        font-family: 'Outfit', sans-serif !important; font-weight: 800 !important;
        font-size: 15px !important; border-radius: var(--r-md) !important;
        padding: 14px 32px !important; box-shadow: 0 4px 20px rgba(0,229,160,0.3) !important;
        transition: all .3s ease !important; width: 100% !important;
    }}
    div.stDownloadButton > button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 40px rgba(0,229,160,0.5) !important;
    }}
    div[data-testid="stForm"] button {{
        background: linear-gradient(135deg, var(--c-cyan), var(--c-indigo)) !important;
        border: none !important; color: #030612 !important;
        font-family: 'Outfit', sans-serif !important; font-weight: 800 !important;
        font-size: 14px !important; letter-spacing: 0.06em !important;
        text-transform: uppercase !important; border-radius: var(--r-md) !important;
        height: 52px !important; box-shadow: 0 4px 24px rgba(0,210,255,0.3) !important;
        transition: all .3s ease !important;
    }}
    div[data-testid="stForm"] button:hover {{
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 10px 36px rgba(0,210,255,0.45) !important;
    }}

    /* ── STREAMLIT ALERTS ── */
    div[data-testid="stSuccess"] {{
        background: rgba(0,229,160,0.08) !important; border: 1px solid rgba(0,229,160,0.3) !important;
        border-radius: var(--r-md) !important; color: #7cf5cc !important;
    }}
    div[data-testid="stWarning"] {{
        background: rgba(251,191,36,0.08) !important; border: 1px solid rgba(251,191,36,0.3) !important;
        border-radius: var(--r-md) !important; color: #fde68a !important;
    }}
    div[data-testid="stError"] {{
        background: rgba(244,63,94,0.08) !important; border: 1px solid rgba(244,63,94,0.3) !important;
        border-radius: var(--r-md) !important; color: #fda4b2 !important;
    }}

    /* ── METRICS ── */
    div[data-testid="metric-container"] {{
        background: var(--c-surface2) !important; border: 1px solid var(--c-border) !important;
        border-radius: var(--r-md) !important; padding: 20px !important;
    }}
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
        font-family: 'Space Mono', monospace !important; font-size: 1.9rem !important;
        color: var(--c-cyan) !important;
    }}
    div[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
        font-family: 'Space Mono', monospace !important; font-size: 10px !important;
        letter-spacing: 0.1em !important; text-transform: uppercase !important;
        color: var(--c-muted) !important;
    }}

    /* ── REGISTRATION FORM ── */
    div[data-testid="stForm"] {{
        background: rgba(5,9,24,0.80) !important;
        backdrop-filter: blur(36px) saturate(1.2);
        -webkit-backdrop-filter: blur(36px) saturate(1.2);
        border-radius: var(--r-xl) !important; padding: 50px 44px !important;
        max-width: 600px; margin: 3vh auto;
        border: 1px solid rgba(0,210,255,0.14) !important;
        box-shadow: 0 30px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.04) !important;
        position: relative;
    }}
    div[data-testid="stForm"]::before {{
        content: ''; position: absolute; top: 0; left: 20%; right: 20%; height: 1px;
        background: linear-gradient(90deg, transparent, var(--c-cyan), transparent);
    }}
    div[data-testid="stForm"] label {{
        color: var(--c-muted) !important; font-family: 'Space Mono', monospace !important;
        font-size: 10px !important; letter-spacing: 0.12em !important;
        text-transform: uppercase !important; font-weight: 700 !important;
    }}
    div[data-testid="stForm"] div[data-baseweb="input"] > div,
    div[data-testid="stForm"] div[data-baseweb="textarea"] > div {{
        background: rgba(255,255,255,0.06) !important;
        border: 1.5px solid rgba(255,255,255,0.1) !important;
        border-radius: var(--r-sm) !important; transition: all .3s;
    }}
    div[data-testid="stForm"] div[data-baseweb="input"] > div:focus-within,
    div[data-testid="stForm"] div[data-baseweb="textarea"] > div:focus-within {{
        border-color: var(--c-cyan) !important;
        box-shadow: 0 0 0 3px rgba(0,210,255,0.12), 0 0 20px rgba(0,210,255,0.1) !important;
        background: rgba(255,255,255,0.09) !important;
    }}
    div[data-testid="stForm"] input, div[data-testid="stForm"] textarea {{
        color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
        font-family: 'Manrope', sans-serif !important; font-size: 15px !important; font-weight: 500 !important;
    }}
    div[data-testid="stForm"] input::placeholder, div[data-testid="stForm"] textarea::placeholder {{
        color: var(--c-dim) !important;
    }}
    div[data-testid="stForm"] div[data-baseweb="select"] > div {{
        background: rgba(255,255,255,0.06) !important;
        border: 1.5px solid rgba(255,255,255,0.1) !important;
        border-radius: var(--r-sm) !important;
    }}
    div[data-testid="stForm"] div[data-baseweb="select"] span {{
        color: #ffffff !important; font-weight: 500 !important;
    }}
    div[data-baseweb="popover"] {{ background: #0a0f24 !important; border: 1px solid rgba(0,210,255,0.18); border-radius: var(--r-md); }}
    ul[role="listbox"] {{ background: #0a0f24 !important; }}
    li[role="option"] {{ color: var(--c-muted) !important; font-size: 14px; }}
    li[role="option"]:hover {{ background: var(--c-cyan-dim) !important; color: var(--c-cyan) !important; }}

    /* ── ANIMATIONS ── */
    @keyframes fadeUp {{ from {{ opacity:0; transform:translateY(20px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes orb {{
        0%,100% {{ transform: translate(0,0) scale(1); }}
        33%      {{ transform: translate(30px,-20px) scale(1.05); }}
        66%      {{ transform: translate(-20px,15px) scale(0.95); }}
    }}
    .a0 {{ animation: fadeUp .6s ease both; }}
    .a1 {{ animation: fadeUp .6s .1s ease both; }}
    .a2 {{ animation: fadeUp .6s .2s ease both; }}
    .a3 {{ animation: fadeUp .6s .3s ease both; }}

    @media (max-width: 768px) {{
        div[data-testid="stForm"] {{ padding: 28px 20px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)


def render_orbs():
    st.markdown("""
    <style>
    .orb {{ position:fixed; border-radius:50%; pointer-events:none; z-index:0; animation:orb 12s ease-in-out infinite; }}
    .o1 {{ width:520px;height:520px;top:-120px;left:-100px;background:radial-gradient(circle,rgba(0,210,255,0.055) 0%,transparent 70%);animation-delay:0s; }}
    .o2 {{ width:380px;height:380px;bottom:-80px;right:-60px;background:radial-gradient(circle,rgba(99,91,255,0.06) 0%,transparent 70%);animation-delay:4s; }}
    .o3 {{ width:260px;height:260px;top:45%;left:55%;background:radial-gradient(circle,rgba(0,229,160,0.04) 0%,transparent 70%);animation-delay:8s; }}
    </style>
    <div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  REGISTRATION PAGE
# ═════════════════════════════════════════════════════════════════════════════
def registration_page():
    inject_css(get_base64_image("health.png"), overlay="rgba(3,6,18,0.80)")
    render_orbs()

    st.markdown("""
    <div class="a0" style="text-align:center;padding:44px 0 20px;">
        <div style="display:inline-flex;align-items:center;gap:8px;margin-bottom:22px;">
            <span class="pill">🧬 MEDCORE AI</span>
            <span class="pill pill-indigo">Clinical Intelligence v2.0</span>
        </div>
        <h1 style="
            font-family:'Outfit',sans-serif;
            font-size:clamp(2.6rem,6vw,4.2rem);font-weight:900;
            letter-spacing:-0.05em;line-height:1.05;margin-bottom:14px;
            background:linear-gradient(110deg,#ffffff 10%,#00d2ff 55%,#635bff 100%);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        ">Diabetes Risk<br>Intelligence Platform</h1>
        <p style="font-size:1rem;color:#7580a0;letter-spacing:0.07em;text-transform:uppercase;margin-bottom:0;">
            Precision · Clinical Grade · AI-Powered · Real-Time
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="a1" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:14px;max-width:700px;margin:0 auto 36px;">
        <div class="card" style="text-align:center;padding:20px 14px;">
            <div style="font-size:28px;margin-bottom:8px;">🤖</div>
            <div style="font-family:'Outfit',sans-serif;font-weight:700;color:#00d2ff;font-size:13px;">SVM Engine</div>
            <div style="font-size:11px;color:#7580a0;margin-top:3px;">Support Vector Machine</div>
        </div>
        <div class="card" style="text-align:center;padding:20px 14px;">
            <div style="font-size:28px;margin-bottom:8px;">📊</div>
            <div style="font-family:'Outfit',sans-serif;font-weight:700;color:#635bff;font-size:13px;">8 Biomarkers</div>
            <div style="font-size:11px;color:#7580a0;margin-top:3px;">Clinical Parameters</div>
        </div>
        <div class="card" style="text-align:center;padding:20px 14px;">
            <div style="font-size:28px;margin-bottom:8px;">⚡</div>
            <div style="font-family:'Outfit',sans-serif;font-weight:700;color:#00e5a0;font-size:13px;">Real-Time</div>
            <div style="font-size:11px;color:#7580a0;margin-top:3px;">Instant Analysis</div>
        </div>
        <div class="card" style="text-align:center;padding:20px 14px;">
            <div style="font-size:28px;margin-bottom:8px;">🔒</div>
            <div style="font-family:'Outfit',sans-serif;font-weight:700;color:#fbbf24;font-size:13px;">Secure DB</div>
            <div style="font-size:11px;color:#7580a0;margin-top:3px;">MongoDB Atlas</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        with st.form("registration_form"):
            st.markdown("""
            <div style="text-align:center;margin-bottom:30px;">
                <div style="width:56px;height:56px;background:linear-gradient(135deg,#00d2ff,#635bff);
                    border-radius:16px;display:inline-flex;align-items:center;justify-content:center;
                    font-size:26px;margin-bottom:14px;box-shadow:0 8px 24px rgba(0,210,255,0.3);">🏥</div>
                <h3 style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:800;color:#e8eeff;margin:0 0 5px;">
                    Patient Registration</h3>
                <p style="font-size:12px;color:#7580a0;margin:0;letter-spacing:0.05em;">
                    Secure · Encrypted · Confidential</p>
            </div>
            """, unsafe_allow_html=True)

            name             = st.text_input("Full Name", placeholder="Enter your full legal name")
            country_list     = [c.name for c in pycountry.countries]
            selected_country = st.selectbox("Country of Residence", country_list)
            country_obj      = pycountry.countries.get(name=selected_country)
            phone            = st.text_input("Mobile Number", placeholder="Local format — no country code")
            email            = st.text_input("Email Address", placeholder="your@hospital.com")
            address          = st.text_area("Residential Address", placeholder="Street, City, State, ZIP Code", height=90)

            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("▶  Register & Access Clinical System", use_container_width=True)

            if submit:
                name    = name.strip()
                phone   = phone.strip()
                email   = email.strip()
                address = address.strip()

                if not all([name, phone, email, address]):
                    st.error("❌ All fields are required. Please complete the form.")
                    return

                if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
                    st.error("❌ Invalid email address format.")
                    return

                try:
                    parsed = phonenumbers.parse(phone, country_obj.alpha_2)
                    if not phonenumbers.is_valid_number(parsed):
                        st.error("❌ Phone number does not match the selected country.")
                        return
                    formatted_phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                except Exception:
                    st.error("❌ Could not parse phone number. Check format and country.")
                    return

                ist        = pytz.timezone("Asia/Kolkata")
                now        = datetime.now(ist)
                patient_id = "PAT-" + str(uuid.uuid4().int)[:6]

                user_data = {
                    "_id": patient_id, "name": name, "phone": formatted_phone,
                    "country": selected_country, "email": email, "address": address,
                    "gender": "Not Selected",
                    "created_at": now.strftime("%d-%m-%Y %I:%M:%S %p")
                }
                users_col.insert_one(user_data)
                st.session_state.patient_info = user_data
                st.session_state.registered   = True
                st.session_state.show_success = True
                st.success("✅ Registration successful!")
                st.rerun()

    st.markdown("""
    <div class="a3" style="text-align:center;margin:30px 0 0;">
        <span class="pill" style="margin:4px;">🔐 256-bit TLS Encryption</span>
        <span class="pill pill-indigo" style="margin:4px;">🏥 HIPAA-Aligned Architecture</span>
        <span class="pill pill-green" style="margin:4px;">⚡ Sub-second Inference</span>
        <span class="pill" style="margin:4px;">📦 MongoDB Atlas Secured</span>
        <span class="pill pill-amber" style="margin:4px;">🩺 Clinical-Grade AI</span>
    </div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  MODEL LOADER
# ═════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def load_model():
    try:
        return joblib.load("diabetes_model.pkl"), joblib.load("scaler_svm.pkl")
    except Exception as e:
        st.error(f"⚠️ Model Loading Error: {e}")
        st.stop()


# ═════════════════════════════════════════════════════════════════════════════
#  PREDICTION PAGE
# ═════════════════════════════════════════════════════════════════════════════
def prediction_page():
    model, scaler = load_model()
    if not st.session_state.patient_info:
        st.session_state.registered = False
        st.stop()

    inject_css(get_base64_image("health22.png"))
    render_orbs()
    info = st.session_state.patient_info

    # ═══════════════ SIDEBAR ═══════════════
    with st.sidebar:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(0,210,255,0.08),rgba(99,91,255,0.06));
            border:1px solid rgba(0,210,255,0.15);border-radius:18px;padding:20px 18px;margin-bottom:6px;">
            <div style="display:flex;align-items:center;gap:13px;margin-bottom:12px;">
                <div style="width:44px;height:44px;flex-shrink:0;
                    background:linear-gradient(135deg,#00d2ff,#635bff);border-radius:12px;
                    display:flex;align-items:center;justify-content:center;font-size:22px;
                    box-shadow:0 4px 16px rgba(0,210,255,0.3);">🩺</div>
                <div>
                    <div style="font-family:'Outfit',sans-serif;font-weight:800;font-size:15px;color:#e8eeff;line-height:1.2;">{info.get('name','')}</div>
                    <div style="font-family:'Space Mono',monospace;font-size:10px;color:#00d2ff;letter-spacing:0.06em;">{info.get('_id','')}</div>
                </div>
            </div>
            <div style="font-size:12px;color:#7580a0;margin-bottom:3px;">📧 {info.get('email','')}</div>
            <div style="font-size:12px;color:#7580a0;">📱 {info.get('phone','')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-label">Demographics</div>', unsafe_allow_html=True)
        age    = st.number_input("Age (Years)", 21, 100, 30)
        gender = st.selectbox("Biological Sex", ["Male", "Female"])
        pregnancies = (st.number_input("Prior Pregnancies", 0, 20, 0) if gender == "Female" else 0)

        st.markdown('<div class="section-label">Glycemic Markers</div>', unsafe_allow_html=True)
        glucose = st.slider("Fasting Glucose (mg/dL)", 0, 200, 120)
        insulin = st.slider("Serum Insulin (IU/mL)", 0, 900, 80)

        st.markdown('<div class="section-label">Cardiovascular</div>', unsafe_allow_html=True)
        bp   = st.slider("Diastolic BP (mmHg)", 0, 130, 70)
        skin = st.slider("Triceps Skin Fold (mm)", 0, 100, 20)

        st.markdown('<div class="section-label">Biometrics</div>', unsafe_allow_html=True)
        bmi = st.number_input("BMI (kg/m²)", 10.0, 70.0, 25.0)
        dpf = st.slider("Diabetes Pedigree Fn.", 0.0, 2.5, 0.5)

        st.markdown("<br>", unsafe_allow_html=True)
        predict_btn = st.button("⚡ Generate AI Assessment", use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔒 Secure Logout", use_container_width=True):
            st.session_state.registered   = False
            st.session_state.patient_info = {}
            st.session_state.show_success = False
            st.rerun()

        st.markdown("""
        <div style="margin-top:24px;padding-top:18px;border-top:1px solid rgba(255,255,255,0.06);">
            <div style="font-family:'Space Mono',monospace;font-size:9px;color:#3a4060;
                letter-spacing:0.1em;text-align:center;text-transform:uppercase;">
                MEDCORE AI · SVM Architecture<br>Clinical Intelligence v2.0
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ═══════════════ MAIN ═══════════════
    st.markdown("""
    <div class="a0" style="text-align:center;padding:30px 0 8px;">
        <div style="display:inline-flex;gap:8px;margin-bottom:18px;">
            <span class="pill">🧬 Diagnostic AI Engine</span>
            <span class="pill pill-indigo">SVM Architecture</span>
        </div>
        <h1 style="font-family:'Outfit',sans-serif;font-size:clamp(2rem,4.5vw,3.4rem);
            font-weight:900;letter-spacing:-0.04em;
            background:linear-gradient(110deg,#ffffff 10%,#00d2ff 55%,#635bff 100%);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px;">
            Diabetes Risk Intelligence</h1>
        <p style="color:#7580a0;font-size:.9rem;letter-spacing:.07em;text-transform:uppercase;">
            Multiparametric Clinical Analysis · Evidence-Based Assessment
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.show_success:
        st.success("✅ Registration Successful! Secure clinical session established.")
        st.session_state.show_success = False

    # About section
    st.markdown("""
    <div class="card card-top-glow a1" style="margin-bottom:28px;">
        <div style="display:flex;align-items:flex-start;gap:18px;">
            <div style="font-size:40px;flex-shrink:0;line-height:1;">📋</div>
            <div>
                <h3 style="font-size:1.1rem;margin-bottom:8px;">About This System</h3>
                <p style="font-size:14.5px;line-height:1.75;color:#7580a0;margin:0;">
                    This Diabetes Prediction System is an AI-powered medical risk assessment tool designed to estimate
                    the likelihood of diabetes based on key health parameters such as glucose level, BMI, blood pressure,
                    age, and family history.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Default idle state
    if not predict_btn:
        st.markdown("""
        <div class="card a2" style="text-align:center;padding:70px 40px;">
            <div style="width:80px;height:80px;
                background:linear-gradient(135deg,rgba(0,210,255,0.1),rgba(99,91,255,0.1));
                border:1px solid rgba(0,210,255,0.2);border-radius:22px;
                display:inline-flex;align-items:center;justify-content:center;
                font-size:40px;margin-bottom:22px;">🧬</div>
            <h2 style="font-size:1.3rem;color:#7580a0;font-weight:600;margin-bottom:10px;">System Awaiting Input</h2>
            <p style="color:#3a4060;font-size:14px;max-width:420px;margin:0 auto;">
                Configure the patient's clinical parameters in the sidebar and click
                <strong style="color:#00d2ff;">Generate AI Assessment</strong> to begin.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ═══════════════ PREDICTION ═══════════════
    if "_id" in info:
        users_col.update_one({"_id": info["_id"]}, {"$set": {"gender": gender}})

    inp     = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
    inp_std = scaler.transform(inp)
    prob    = model.predict_proba(inp_std)[0]
    prob_neg = prob[0] * 100
    prob_pos = prob[1] * 100

    if prob_pos < 30:
        risk_label, risk_hex, risk_class, risk_icon = "Low Risk",      "#00e5a0", "card-low",  "✅"
        risk_display = "LOW RISK — Diabetes Unlikely"
    elif prob_pos < 70:
        risk_label, risk_hex, risk_class, risk_icon = "Moderate Risk", "#fbbf24", "card-mod",  "⚠️"
        risk_display = "MODERATE RISK — Possible Diabetes"
    else:
        risk_label, risk_hex, risk_class, risk_icon = "High Risk",     "#f43f5e", "card-high", "🚨"
        risk_display = "HIGH RISK — Diabetes Likely"

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    preds_col.insert_one({
        "patient_id": info["_id"], "patient_name": info["name"],
        "age": age, "gender": gender, "glucose": glucose, "blood_pressure": bp,
        "bmi": bmi, "prediction": risk_label,
        "probability": round(prob_pos, 2),
        "created_at": now.strftime("%d-%m-%Y %H:%M:%S")
    })

    # Result banner
    st.markdown(f"""
    <div class="card {risk_class} a0" style="margin-bottom:24px;padding:30px 28px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:20px;">
            <div>
                <div style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:0.14em;
                    text-transform:uppercase;color:{risk_hex};margin-bottom:10px;">
                    {risk_icon} DIAGNOSTIC OUTPUT · {now.strftime('%d %b %Y %I:%M %p IST')}</div>
                <h1 style="font-family:'Outfit',sans-serif;font-size:clamp(1.6rem,3.5vw,2.6rem);
                    font-weight:900;letter-spacing:-0.03em;color:{risk_hex};margin:0 0 10px;">
                    {risk_display}</h1>
                <p style="font-size:15px;color:#7580a0;margin:0;">
                    AI Probability Score:&nbsp;
                    <span style="font-family:'Space Mono',monospace;font-size:20px;font-weight:700;color:{risk_hex};">
                    {prob_pos:.1f}%</span>&nbsp;diabetic likelihood
                </p>
            </div>
            <div style="text-align:right;flex-shrink:0;">
                <div style="font-family:'Space Mono',monospace;font-size:9px;color:#3a4060;
                    letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">Patient ID</div>
                <div style="font-family:'Space Mono',monospace;font-size:13px;color:{risk_hex};">{info.get('_id','')}</div>
                <div style="font-family:'Space Mono',monospace;font-size:9px;color:#3a4060;margin-top:8px;letter-spacing:0.08em;">
                    MEDCORE AI · SVM ENGINE</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Probability metrics
    c1, c2 = st.columns(2)
    with c1: st.metric("Non-Diabetic Probability", f"{prob_neg:.1f}%")
    with c2: st.metric("Diabetic Probability",     f"{prob_pos:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # Build cause data
    cause_labels, cause_values = [], []
    _pal = ["#f43f5e","#fbbf24","#00d2ff","#635bff","#00e5a0"]
    if glucose >= 126: cause_labels.append("Hyperglycemia");   cause_values.append(min(glucose/2, 100))
    if bmi > 30:       cause_labels.append("Obesity (BMI)");   cause_values.append(min(bmi*2, 100))
    if age > 45:       cause_labels.append("Age Factor");      cause_values.append(min(age, 100))
    if bp > 120:       cause_labels.append("Hypertension");    cause_values.append(min(bp, 100))
    if dpf > 0.5:      cause_labels.append("Genetics (DPF)");  cause_values.append(min(dpf*100, 100))
    if not cause_labels:
        cause_labels = ["Healthy Indicators"]; cause_values = [100]
    cause_colors = _pal[:len(cause_labels)]

    # Charts row
    cg1, cg2 = st.columns(2)
    with cg1:
        st.markdown('<div style="font-family:\'Space Mono\',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#7580a0;margin-bottom:6px;">Risk Gauge</div>', unsafe_allow_html=True)
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=prob_pos,
            number={"suffix":"%","font":{"family":"Space Mono","color":"white","size":28}},
            gauge={
                "axis":      {"range":[0,100],"tickcolor":"rgba(255,255,255,0.2)","tickwidth":1},
                "bar":       {"color":risk_hex,"thickness":0.22},
                "bgcolor":   "rgba(0,0,0,0)", "borderwidth":0,
                "steps":     [{"range":[0,30],"color":"rgba(0,229,160,0.12)"},
                              {"range":[30,70],"color":"rgba(251,191,36,0.12)"},
                              {"range":[70,100],"color":"rgba(244,63,94,0.12)"}],
                "threshold": {"line":{"color":risk_hex,"width":3},"thickness":0.78,"value":prob_pos}
            }
        ))
        gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)",font=dict(color="white"),
                            height=260,margin=dict(l=20,r=20,t=30,b=10))
        st.plotly_chart(gauge, use_container_width=True, config={"responsive":True})

    with cg2:
        st.markdown('<div style="font-family:\'Space Mono\',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#7580a0;margin-bottom:6px;">Etiology Breakdown</div>', unsafe_allow_html=True)
        pie = go.Figure(go.Pie(
            labels=cause_labels, values=cause_values, hole=0.58,
            marker=dict(colors=cause_colors,line=dict(color="rgba(0,0,0,0.5)",width=2)),
            textfont=dict(family="Space Mono",size=11,color="white"),
            textposition="inside",textinfo="percent+label",showlegend=False
        ))
        pie.update_layout(paper_bgcolor="rgba(0,0,0,0)",font=dict(color="white"),
                          height=260,margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(pie, use_container_width=True, config={"responsive":True})

    # Bar chart
    st.markdown('<div style="font-family:\'Space Mono\',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#7580a0;margin:4px 0 8px;">📊 Causes of Diabetes (Risk Contribution Analysis)</div>', unsafe_allow_html=True)
    bar = go.Figure(go.Bar(
        x=cause_labels, y=cause_values,
        text=[f"{v:.1f}" for v in cause_values], textposition="auto",
        textfont=dict(family="Space Mono",color="white",size=12),
        marker=dict(
            color=cause_values,
            colorscale=[[0,"rgba(0,229,160,0.85)"],[0.45,"rgba(251,191,36,0.9)"],[1,"rgba(244,63,94,0.95)"]],
            line=dict(color="rgba(255,255,255,0.08)",width=1)
        )
    ))
    bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#7580a0",family="Manrope"),
        xaxis=dict(tickfont=dict(color="#7580a0",size=12,family="Manrope"),
                   title="Risk Factors",title_font=dict(color="#7580a0"),
                   showline=True,linecolor="rgba(255,255,255,0.08)"),
        yaxis=dict(tickfont=dict(color="#7580a0",size=12,family="Manrope"),
                   title="Severity Score",title_font=dict(color="#7580a0"),
                   gridcolor="rgba(255,255,255,0.04)",zerolinecolor="rgba(255,255,255,0.08)"),
        margin=dict(l=20,r=20,t=20,b=20),autosize=True
    )
    st.plotly_chart(bar, use_container_width=True, config={"responsive":True})

    # Risk factor analysis
    st.markdown('<div style="font-family:\'Space Mono\',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#7580a0;margin:20px 0 14px;">🔬 Risk Factor Analysis</div>', unsafe_allow_html=True)

    risk_factors, positive_factors = [], []
    if glucose >= 126:           risk_factors.append("High Glucose Level (≥126 mg/dL)")
    elif 100 <= glucose < 126:   risk_factors.append("Prediabetic Glucose Level (100–125 mg/dL)")
    else:                        positive_factors.append("Normal Glucose Level (<100 mg/dL)")
    if bmi > 30:                 risk_factors.append("High BMI (Obesity)")
    elif 18.5 <= bmi <= 24.9:    positive_factors.append("Healthy BMI")
    if age > 45:                 risk_factors.append("Age above 45")
    if bp > 120:                 risk_factors.append("High Blood Pressure (>120 mmHg)")
    elif 90 <= bp <= 120:        positive_factors.append("Normal Blood Pressure")
    if dpf > 0.5:                risk_factors.append("Higher Genetic Risk (DPF > 0.5)")

    cr1, cr2 = st.columns(2)
    with cr1:
        st.markdown('<div class="card" style="min-height:180px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-family:\'Outfit\',sans-serif;font-weight:700;font-size:14px;color:#fda4b2;margin-bottom:14px;">⚠️ Identified Risk Factors</div>', unsafe_allow_html=True)
        if risk_factors:
            for f in risk_factors: st.markdown(f'<div class="risk-badge">🚨 {f}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#3a4060;font-size:13px;">No critical risk vectors detected.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with cr2:
        st.markdown('<div class="card" style="min-height:180px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-family:\'Outfit\',sans-serif;font-weight:700;font-size:14px;color:#7cf5cc;margin-bottom:14px;">🛡️ Positive Health Indicators</div>', unsafe_allow_html=True)
        if positive_factors:
            for f in positive_factors: st.markdown(f'<div class="safe-badge">✅ {f}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#3a4060;font-size:13px;">No protective factors highlighted.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Recommendations
    st.markdown('<div style="font-family:\'Space Mono\',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#7580a0;margin:20px 0 14px;">💊 Medical Recommendations</div>', unsafe_allow_html=True)

    if prob_pos >= 70:
        st.error("- Consult a healthcare professional immediately\n- Get complete diabetes screening\n- Monitor blood sugar regularly\n- Improve diet and physical activity")
        recs_for_pdf = ["Consult a healthcare professional immediately","Get complete diabetes screening","Monitor blood sugar regularly","Improve diet and physical activity"]
    elif prob_pos >= 30:
        st.warning("- Maintain healthy diet\n- Increase physical activity\n- Monitor glucose periodically")
        recs_for_pdf = ["Maintain healthy diet","Increase physical activity","Monitor glucose periodically"]
    else:
        st.success("- Continue healthy lifestyle\n- Exercise regularly\n- Routine health check-ups")
        recs_for_pdf = ["Continue healthy lifestyle","Exercise regularly","Routine health check-ups"]

    # PDF generation
    st.markdown("<br>", unsafe_allow_html=True)
    buf    = BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=letter,
                                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elems  = []
    styles = getSampleStyleSheet()

    t_title  = ParagraphStyle("T", parent=styles["Heading1"], fontSize=20,
                               textColor=colors.HexColor("#0f172a"), alignment=1,
                               spaceAfter=5, fontName="Helvetica-Bold")
    t_date   = ParagraphStyle("D", parent=styles["Normal"], fontSize=10,
                               textColor=colors.dimgrey, alignment=1,
                               spaceAfter=20, fontName="Helvetica-Oblique")
    t_head   = ParagraphStyle("H", parent=styles["Heading2"], fontSize=14,
                               textColor=colors.HexColor("#005bea"),
                               spaceBefore=15, spaceAfter=10,
                               fontName="Helvetica-Bold", borderPadding=6,
                               backColor=colors.HexColor("#f8fafc"))
    t_normal = ParagraphStyle("N", parent=styles["Normal"], fontSize=11, spaceAfter=6)
    t_addr   = ParagraphStyle("A", parent=styles["Normal"], fontSize=11, leading=14)

    elems.append(Paragraph("🩺 DIABETES RISK PREDICTION REPORT", t_title))
    elems.append(Paragraph(f"Report Generated On: {now.strftime('%d %B %Y | %I:%M %p (IST)')}", t_date))

    addr_p = Paragraph(info.get("address","N/A"), t_addr)
    pt = Table([
        ["Patient ID",    info.get("_id","N/A")],
        ["Full Name",     info.get("name","N/A")],
        ["Email Address", info.get("email","N/A")],
        ["Phone Number",  info.get("phone","N/A")],
        ["Country",       info.get("country","N/A")],
        ["Address",       addr_p],
    ], colWidths=[2.2*inch,4.3*inch])
    pt.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.5,colors.lightgrey),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#f1f5f9")),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("PADDING",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    elems += [Paragraph("Patient Profile", t_head), pt, Spacer(1, 0.2*inch)]

    med_rows = [
        ["Age",                   f"{age} Years"],
        ["Gender",                gender],
        ["Glucose Level",         f"{glucose} mg/dL"],
        ["Blood Pressure",        f"{bp} mmHg"],
        ["Skin Thickness",        f"{skin} mm"],
        ["Insulin Level",         f"{insulin} IU/mL"],
        ["BMI",                   str(bmi)],
        ["Diabetes Pedigree Fn.", str(dpf)],
    ]
    if gender == "Female":
        med_rows.insert(2, ["Pregnancies", str(pregnancies)])

    mt = Table(med_rows, colWidths=[2.2*inch,4.3*inch])
    mt.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.5,colors.lightgrey),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#f1f5f9")),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("PADDING",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    elems += [Paragraph("Clinical Inputs", t_head), mt, Spacer(1, 0.3*inch)]

    elems.append(Paragraph("Risk Assessment Result", t_head))
    col_map = {"Low Risk":"green","Moderate Risk":"#d97706","High Risk":"red"}
    lbl_map = {
        "Low Risk":      "LOW RISK - Diabetes Unlikely",
        "Moderate Risk": "MODERATE RISK - Possible Diabetes",
        "High Risk":     "HIGH RISK - Diabetes Likely"
    }
    elems.append(Paragraph(f"<b>Overall Risk Level:</b> <font color='{col_map[risk_label]}'><b>{lbl_map[risk_label]}</b></font>", t_normal))
    elems.append(Paragraph(f"<b>Risk Percentage:</b> {prob_pos:.1f}%", t_normal))
    elems.append(Spacer(1, 0.2*inch))

    try:
        time.sleep(1)
        pdf_bar = go.Figure(bar)
        pdf_bar.update_layout(font=dict(color="black"), paper_bgcolor="white", plot_bgcolor="white")
        pdf_bar.update_xaxes(tickfont=dict(color="black"), title_font=dict(color="black"), linecolor="black")
        pdf_bar.update_yaxes(tickfont=dict(color="black"), title_font=dict(color="black"),
                             gridcolor="lightgrey", zerolinecolor="black")
        pdf_pie = go.Figure(pie)
        pdf_pie.update_layout(font=dict(color="black"), paper_bgcolor="white", plot_bgcolor="white")

        bar_bytes = pdf_bar.to_image(format="png", engine="kaleido", width=350, height=280, scale=2)
        pie_bytes = pdf_pie.to_image(format="png", engine="kaleido", width=350, height=280, scale=2)

        ct = Table([[RLImage(BytesIO(bar_bytes),3.2*inch,2.5*inch),
                     RLImage(BytesIO(pie_bytes),3.2*inch,2.5*inch)]],
                   colWidths=[3.3*inch,3.3*inch])
        ct.setStyle(TableStyle([
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("BOX",(0,0),(-1,-1),1.5,colors.HexColor("#e2e8f0")),
            ("BOTTOMPADDING",(0,0),(-1,-1),15),
            ("TOPPADDING",(0,0),(-1,-1),10),
        ]))
        elems += [Paragraph("Data Visualization & Analysis", t_head), ct]
    except Exception:
        elems.append(Paragraph("<font color='red'><i>* Charts unavailable. Run: pip install -U kaleido</i></font>", t_normal))

    elems.append(Spacer(1, 0.2*inch))
    elems.append(Paragraph("Medical Recommendations", t_head))
    elems.append(ListFlowable([ListItem(Paragraph(r, t_normal)) for r in recs_for_pdf], bulletType="bullet"))
    elems.append(Spacer(1, 0.4*inch))
    elems.append(Paragraph("<b>Medical Disclaimer:</b> This report is AI-generated and does not replace professional medical advice.", styles["Italic"]))

    doc.build(elems)
    pdf_data = buf.getvalue()
    buf.close()

    st.download_button(
        label="📄 Download Professional Medical Report (PDF)",
        data=pdf_data,
        file_name=f"Diabetes_Report_{info.get('name','Patient')}.pdf",
        mime="application/pdf"
    )

    st.markdown("---")
    st.warning("⚠️ Medical Disclaimer: This tool does NOT replace professional medical advice.")


# ═════════════════════════════════════════════════════════════════════════════
#  NAVIGATION
# ═════════════════════════════════════════════════════════════════════════════
if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
