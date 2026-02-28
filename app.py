# ================================================================
# MEDCORE AI — Diabetes Intelligence Platform
# Hospital-Grade UI · All bugs fixed · PDF with charts
# ================================================================

import streamlit as st
import numpy as np
import joblib
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import base64, re, uuid, time
import pycountry, phonenumbers, pytz
from io import BytesIO
from datetime import datetime

from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 ListFlowable, ListItem, Table, TableStyle,
                                 Image as RLImage)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# ── helpers ──────────────────────────────────────────────────
def get_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ── mongo ─────────────────────────────────────────────────────
URI       = "mongodb+srv://diabetes_user:Diabetes%40123@diabetescluster.oxegep6.mongodb.net/?retryWrites=true&w=majority"
_client   = MongoClient(URI, server_api=ServerApi("1"))
_db       = _client["diabetes_app"]
users_col = _db["registered_users"]
preds_col = _db["predictions"]

# ── page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="MEDCORE AI — Diabetes Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.write("App Loaded Successfully")

# ── session ───────────────────────────────────────────────────
for k, v in [("registered", False), ("patient_info", {}), ("show_success", False)]:
    st.session_state.setdefault(k, v)

# ════════════════════════════════════════════════════════════════
#  MASTER CSS  — hospital palette, all text visible, no broken divs
# ════════════════════════════════════════════════════════════════
def inject_css(img_b64, dark_overlay="rgba(4,10,28,0.84)"):
    st.markdown(f"""
<style>
/* ── fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Space+Mono:wght@400;700&family=Manrope:wght@400;500;600;700;800&display=swap');

/* ── tokens ── */
:root {{
  --bg:          #040a1c;
  --surface:     rgba(255,255,255,0.045);
  --surface2:    rgba(255,255,255,0.08);
  --border:      rgba(255,255,255,0.09);
  --border-c:    rgba(0,180,219,0.40);

  /* Hospital palette */
  --cyan:        #00b4db;        /* primary teal/cyan */
  --cyan-dim:    rgba(0,180,219,0.14);
  --navy:        #0a2342;        /* deep hospital navy */
  --navy-mid:    #0d3060;
  --blue:        #1565c0;        /* medical blue */
  --blue-mid:    #1e88e5;
  --green:       #00c896;        /* vitals green */
  --green-dim:   rgba(0,200,150,0.14);
  --amber:       #f59e0b;        /* caution amber */
  --amber-dim:   rgba(245,158,11,0.14);
  --red:         #e53935;        /* alert red */
  --red-dim:     rgba(229,57,53,0.14);

  --text:        #e8f0fe;        /* primary text — always visible */
  --muted:       #90a4c8;        /* secondary text */
  --dim:         #4a5a80;        /* placeholder */

  --r-sm: 10px; --r-md: 14px; --r-lg: 20px; --r-xl: 28px;
  --shadow: 0 6px 28px rgba(0,0,0,0.5);
}}

/* ── global ── */
*, *::before, *::after {{ box-sizing: border-box; }}
.stApp {{
  background: linear-gradient({dark_overlay}, {dark_overlay}),
              url("data:image/png;base64,{img_b64}") center/cover fixed;
  font-family: 'Manrope', sans-serif;
  color: var(--text);
  min-height: 100vh;
}}
#MainMenu, footer, header, .stDeployButton {{ visibility:hidden!important; display:none!important; }}
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-thumb {{ background: var(--border-c); border-radius: 99px; }}

/* ── typography — force visible everywhere ── */
h1, h2, h3, h4, h5, h6 {{
  font-family: 'Outfit', sans-serif !important;
  color: var(--text) !important;
  letter-spacing: -0.02em;
}}
p, li, div, span, label {{
  color: var(--text) !important;   /* catch-all — overridden below where needed */
}}

/* ── streamlit container blocks ── */
/* Target Streamlit's column and block containers for card look */
div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
  backdrop-filter: blur(18px) !important;
}}

/* ── PILLS ── */
.pill {{
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--cyan-dim); border: 1px solid rgba(0,180,219,0.3);
  border-radius: 99px; padding: 5px 14px;
  font-family: 'Space Mono', monospace; font-size: 11px;
  color: var(--cyan) !important; letter-spacing: 0.07em; white-space: nowrap;
}}
.pill-navy   {{ background: rgba(10,35,66,0.6);   border-color: rgba(21,101,192,0.4); color: #64b5f6 !important; }}
.pill-green  {{ background: var(--green-dim);      border-color: rgba(0,200,150,0.3);  color: var(--green) !important; }}
.pill-amber  {{ background: var(--amber-dim);      border-color: rgba(245,158,11,0.3); color: var(--amber) !important; }}
.pill-red    {{ background: var(--red-dim);        border-color: rgba(229,57,53,0.3);  color: var(--red) !important; }}

/* ── SECTION LABEL ── */
.sec-lbl {{
  display: flex; align-items: center; gap: 10px;
  font-family: 'Space Mono', monospace; font-size: 10px;
  letter-spacing: 0.15em; text-transform: uppercase;
  color: var(--cyan) !important; margin: 20px 0 10px;
}}
.sec-lbl::after {{
  content:''; flex:1; height:1px;
  background: linear-gradient(90deg, rgba(0,180,219,0.35), transparent);
}}

/* ── RESULT CARDS ── */
.res-card {{
  border-radius: var(--r-lg); padding: 28px 26px;
  margin-bottom: 22px; position: relative; overflow: hidden;
}}
.res-low  {{ background: linear-gradient(135deg,rgba(0,200,150,0.10),rgba(0,200,150,0.03)); border: 1.5px solid rgba(0,200,150,0.35); }}
.res-mod  {{ background: linear-gradient(135deg,rgba(245,158,11,0.10),rgba(245,158,11,0.03)); border: 1.5px solid rgba(245,158,11,0.35); }}
.res-high {{ background: linear-gradient(135deg,rgba(229,57,53,0.10),rgba(229,57,53,0.03)); border: 1.5px solid rgba(229,57,53,0.35); }}

/* ── RISK / SAFE BADGES ── */
.risk-badge {{
  background: rgba(229,57,53,0.10); border-left: 3px solid var(--red);
  border-radius: 0 8px 8px 0; padding: 10px 16px; margin-bottom: 8px;
  font-size: 14px; color: #ef9a9a !important;
  font-family: 'Manrope', sans-serif; font-weight: 600;
}}
.safe-badge {{
  background: rgba(0,200,150,0.10); border-left: 3px solid var(--green);
  border-radius: 0 8px 8px 0; padding: 10px 16px; margin-bottom: 8px;
  font-size: 14px; color: #80cbc4 !important;
  font-family: 'Manrope', sans-serif; font-weight: 600;
}}
.empty-state {{
  font-size: 13px; color: var(--muted) !important;
  font-style: italic; padding: 6px 0;
}}

/* ── FEATURE MINI-CARDS ── */
.feat-card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 18px 14px; text-align: center;
  transition: border-color .3s, transform .3s;
}}
.feat-card:hover {{ border-color: var(--border-c); transform: translateY(-3px); }}
.feat-card .icon {{ font-size: 28px; margin-bottom: 8px; }}
.feat-card .title {{ font-family:'Outfit',sans-serif; font-weight:700; font-size:13px; }}
.feat-card .sub   {{ font-size:11px; color:var(--muted) !important; margin-top:3px; }}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {{
  background: rgba(4,10,28,0.94) !important;
  backdrop-filter: blur(28px) !important;
  border-right: 1px solid var(--border) !important;
  box-shadow: 6px 0 40px rgba(0,0,0,0.6) !important;
}}
section[data-testid="stSidebar"] > div {{ padding-top: 14px !important; }}
section[data-testid="stSidebar"] label {{
  color: var(--muted) !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 10px !important; letter-spacing: 0.13em !important;
  text-transform: uppercase !important; font-weight: 700 !important;
}}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {{
  color: var(--muted) !important; font-size: 13px;
}}

/* Sidebar inputs — white/light so text always readable */
section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
  background: #e8f0fe !important; border: 1.5px solid #90a4c8 !important;
  border-radius: var(--r-sm) !important; transition: border-color .25s;
}}
section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {{
  border-color: var(--cyan) !important;
  box-shadow: 0 0 0 3px rgba(0,180,219,0.18) !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="input"] input {{
  color: #0a1a3a !important; -webkit-text-fill-color: #0a1a3a !important;
  font-family: 'Space Mono', monospace !important; font-size:14px !important; font-weight:700 !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="select"] span {{
  color: #0a1a3a !important; font-weight: 700 !important;
}}
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {{ -webkit-appearance:none; }}
input[type="number"] {{ -moz-appearance:textfield; }}

/* Slider handle */
div[data-baseweb="slider"] [role="slider"] {{
  background: var(--cyan) !important; border: 2.5px solid #fff !important;
  box-shadow: 0 0 10px rgba(0,180,219,0.7) !important;
}}
div[data-testid="stTickBar"] {{ display:none !important; }}

/* Dropdown popup */
div[data-baseweb="popover"] {{ background: #071228 !important; border:1px solid rgba(0,180,219,0.2); border-radius:12px; }}
ul[role="listbox"] {{ background: #071228 !important; }}
li[role="option"] {{ color: var(--muted) !important; }}
li[role="option"]:hover {{ background: var(--cyan-dim) !important; color: var(--cyan) !important; }}

/* ── BUTTONS ── */
section[data-testid="stSidebar"] button {{
  background: linear-gradient(135deg, var(--cyan) 0%, var(--blue) 100%) !important;
  border: none !important; color: #ffffff !important;
  font-family: 'Outfit', sans-serif !important; font-weight: 800 !important;
  font-size: 13px !important; letter-spacing: 0.06em !important;
  border-radius: var(--r-md) !important; height: 46px !important;
  text-transform: uppercase !important;
  box-shadow: 0 4px 18px rgba(0,180,219,0.3) !important;
  transition: all .3s ease !important;
}}
section[data-testid="stSidebar"] button:hover {{
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 28px rgba(0,180,219,0.45) !important;
}}
div.stDownloadButton > button {{
  background: linear-gradient(135deg, #00c896, #007a5e) !important;
  border: none !important; color: #ffffff !important;
  font-family: 'Outfit', sans-serif !important; font-weight: 800 !important;
  font-size: 15px !important; border-radius: var(--r-md) !important;
  padding: 14px 32px !important; width: 100% !important;
  box-shadow: 0 4px 18px rgba(0,200,150,0.3) !important;
  transition: all .3s ease !important;
}}
div.stDownloadButton > button:hover {{
  transform: translateY(-3px) !important;
  box-shadow: 0 10px 36px rgba(0,200,150,0.5) !important;
}}
div[data-testid="stForm"] button {{
  background: linear-gradient(135deg, var(--cyan), var(--blue)) !important;
  border: none !important; color: #ffffff !important;
  font-family: 'Outfit', sans-serif !important; font-weight: 800 !important;
  font-size: 14px !important; letter-spacing: 0.06em !important;
  text-transform: uppercase !important; border-radius: var(--r-md) !important;
  height: 52px !important;
  box-shadow: 0 4px 22px rgba(0,180,219,0.32) !important;
  transition: all .3s ease !important;
}}
div[data-testid="stForm"] button:hover {{
  transform: translateY(-2px) scale(1.02) !important;
  box-shadow: 0 10px 32px rgba(0,180,219,0.5) !important;
}}

/* ── REGISTRATION FORM ── */
div[data-testid="stForm"] {{
  background: rgba(4,10,28,0.82) !important;
  backdrop-filter: blur(32px) saturate(1.2);
  border-radius: var(--r-xl) !important; padding: 48px 44px !important;
  max-width: 580px; margin: 3vh auto;
  border: 1px solid rgba(0,180,219,0.18) !important;
  box-shadow: 0 30px 80px rgba(0,0,0,0.7) !important;
  position: relative;
}}
div[data-testid="stForm"]::before {{
  content:''; position:absolute; top:0; left:20%; right:20%; height:1px;
  background: linear-gradient(90deg, transparent, var(--cyan), transparent);
}}
div[data-testid="stForm"] label {{
  color: var(--muted) !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 10px !important; letter-spacing: 0.13em !important;
  text-transform: uppercase !important; font-weight: 700 !important;
}}
div[data-testid="stForm"] div[data-baseweb="input"] > div,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div {{
  background: rgba(255,255,255,0.07) !important;
  border: 1.5px solid rgba(255,255,255,0.12) !important;
  border-radius: var(--r-sm) !important; transition: all .3s;
}}
div[data-testid="stForm"] div[data-baseweb="input"] > div:focus-within,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div:focus-within {{
  border-color: var(--cyan) !important;
  box-shadow: 0 0 0 3px rgba(0,180,219,0.14) !important;
}}
div[data-testid="stForm"] input, div[data-testid="stForm"] textarea {{
  color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
  font-family:'Manrope',sans-serif !important; font-size:15px !important; font-weight:500 !important;
}}
div[data-testid="stForm"] div[data-baseweb="select"] > div {{
  background: rgba(255,255,255,0.07) !important;
  border: 1.5px solid rgba(255,255,255,0.12) !important;
  border-radius: var(--r-sm) !important;
}}
div[data-testid="stForm"] div[data-baseweb="select"] span {{
  color: #ffffff !important; font-weight:500 !important;
}}

/* ── METRICS ── */
div[data-testid="metric-container"] {{
  background: rgba(10,35,66,0.6) !important;
  border: 1px solid rgba(0,180,219,0.2) !important;
  border-radius: var(--r-md) !important; padding: 18px !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
  font-family:'Space Mono',monospace !important;
  font-size:2rem !important; color: var(--cyan) !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
  font-family:'Space Mono',monospace !important; font-size:10px !important;
  letter-spacing:.1em !important; text-transform:uppercase !important;
  color: var(--muted) !important;
}}

/* ── STREAMLIT ALERTS (slightly restyled) ── */
div[data-testid="stSuccess"] {{
  background: rgba(0,200,150,0.10) !important;
  border: 1px solid rgba(0,200,150,0.35) !important;
  border-radius: var(--r-md) !important;
}}
div[data-testid="stSuccess"] p {{ color: #80cbc4 !important; }}
div[data-testid="stWarning"] {{
  background: rgba(245,158,11,0.10) !important;
  border: 1px solid rgba(245,158,11,0.35) !important;
  border-radius: var(--r-md) !important;
}}
div[data-testid="stWarning"] p {{ color: #ffd54f !important; }}
div[data-testid="stError"] {{
  background: rgba(229,57,53,0.10) !important;
  border: 1px solid rgba(229,57,53,0.35) !important;
  border-radius: var(--r-md) !important;
}}
div[data-testid="stError"] p {{ color: #ef9a9a !important; }}

/* ── ANIMATIONS ── */
@keyframes fadeUp {{ from{{opacity:0;transform:translateY(18px)}} to{{opacity:1;transform:translateY(0)}} }}
@keyframes orbFloat {{
  0%,100%{{transform:translate(0,0) scale(1)}}
  40%{{transform:translate(25px,-18px) scale(1.04)}}
  70%{{transform:translate(-18px,12px) scale(0.97)}}
}}
.a0 {{ animation: fadeUp .55s ease both; }}
.a1 {{ animation: fadeUp .55s .10s ease both; }}
.a2 {{ animation: fadeUp .55s .20s ease both; }}

@media(max-width:768px) {{
  div[data-testid="stForm"] {{ padding:28px 18px !important; }}
}}
</style>
""", unsafe_allow_html=True)


def render_orbs():
    st.markdown("""
<style>
.orb{{ position:fixed; border-radius:50%; pointer-events:none; z-index:0; animation:orbFloat 14s ease-in-out infinite; }}
.orb1{{ width:480px;height:480px;top:-140px;left:-100px;
        background:radial-gradient(circle,rgba(0,180,219,0.07) 0%,transparent 70%); animation-delay:0s; }}
.orb2{{ width:360px;height:360px;bottom:-80px;right:-60px;
        background:radial-gradient(circle,rgba(21,101,192,0.08) 0%,transparent 70%); animation-delay:5s; }}
.orb3{{ width:240px;height:240px;top:50%;left:58%;
        background:radial-gradient(circle,rgba(0,200,150,0.05) 0%,transparent 70%); animation-delay:9s; }}
</style>
<div class="orb orb1"></div><div class="orb orb2"></div><div class="orb orb3"></div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  MATPLOTLIB CHART HELPERS  (for PDF — white background)
# ════════════════════════════════════════════════════════════════
HOSP_COLORS = ["#e53935", "#f59e0b", "#1e88e5", "#1565c0", "#00c896"]

def make_bar_png(labels, values):
    """Return PNG bytes of a clean white-background bar chart."""
    fig, ax = plt.subplots(figsize=(5, 3.2), dpi=150)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8f9fa")

    bar_colors = [HOSP_COLORS[i % len(HOSP_COLORS)] for i in range(len(labels))]
    bars = ax.bar(labels, values, color=bar_colors, width=0.55,
                  edgecolor="white", linewidth=1.2)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                f"{val:.1f}", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color="#1a2340")

    ax.set_ylim(0, max(values) * 1.25 if values else 110)
    ax.set_xlabel("Risk Factors", fontsize=9, color="#3a4a6a", labelpad=6)
    ax.set_ylabel("Severity Score", fontsize=9, color="#3a4a6a", labelpad=6)
    ax.set_title("Risk Factor Severity", fontsize=11, fontweight="bold",
                 color="#0a1a3a", pad=10)
    ax.tick_params(axis="x", labelsize=8, colors="#3a4a6a")
    ax.tick_params(axis="y", labelsize=8, colors="#3a4a6a")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#c8d0e0")
    ax.yaxis.grid(True, color="#e0e6f0", linewidth=0.7, linestyle="--")
    ax.set_axisbelow(True)
    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#ffffff")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def make_pie_png(labels, values):
    """Return PNG bytes of a clean white-background donut chart."""
    fig, ax = plt.subplots(figsize=(4.8, 3.4), dpi=150)
    fig.patch.set_facecolor("#ffffff")

    pie_colors = [HOSP_COLORS[i % len(HOSP_COLORS)] for i in range(len(labels))]
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=pie_colors,
        autopct="%1.1f%%", startangle=140,
        wedgeprops=dict(width=0.6, edgecolor="white", linewidth=1.5),
        pctdistance=0.78,
    )
    for t in texts:
        t.set_fontsize(8); t.set_color("#1a2340")
    for at in autotexts:
        at.set_fontsize(7.5); at.set_fontweight("bold"); at.set_color("#1a2340")
    ax.set_title("Risk Contribution (%)", fontsize=11, fontweight="bold",
                 color="#0a1a3a", pad=10)
    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#ffffff")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ════════════════════════════════════════════════════════════════
#  REGISTRATION PAGE
# ════════════════════════════════════════════════════════════════
def registration_page():
    inject_css(get_b64("health.png"), dark_overlay="rgba(4,10,28,0.80)")
    render_orbs()

    # ── hero ─────────────────────────────────────────────────
    st.markdown("""
<div class="a0" style="text-align:center;padding:42px 0 18px;">
  <div style="display:inline-flex;align-items:center;gap:8px;margin-bottom:20px;">
    <span class="pill">🧬 MEDCORE AI</span>
    <span class="pill pill-navy">Clinical Intelligence v2.0</span>
  </div>
  <h1 style="
    font-family:'Outfit',sans-serif;
    font-size:clamp(2.4rem,5.5vw,3.8rem);
    font-weight:900; letter-spacing:-0.05em; line-height:1.08;
    margin-bottom:12px;
    background:linear-gradient(110deg,#ffffff 5%,#00b4db 50%,#1565c0 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  ">Diabetes Risk<br>Intelligence Platform</h1>
  <p style="font-size:.95rem;color:#90a4c8 !important;letter-spacing:.07em;text-transform:uppercase;">
    Precision · Clinical Grade · AI-Powered · Real-Time
  </p>
</div>
""", unsafe_allow_html=True)

    # ── feature cards ─────────────────────────────────────────
    st.markdown("""
<div class="a1" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));
     gap:13px;max-width:680px;margin:0 auto 32px;">
  <div class="feat-card">
    <div class="icon">🤖</div>
    <div class="title" style="color:#00b4db!important;">SVM Engine</div>
    <div class="sub">Support Vector Machine</div>
  </div>
  <div class="feat-card">
    <div class="icon">📊</div>
    <div class="title" style="color:#1e88e5!important;">8 Biomarkers</div>
    <div class="sub">Clinical Parameters</div>
  </div>
  <div class="feat-card">
    <div class="icon">⚡</div>
    <div class="title" style="color:#00c896!important;">Real-Time</div>
    <div class="sub">Instant Analysis</div>
  </div>
  <div class="feat-card">
    <div class="icon">🔒</div>
    <div class="title" style="color:#f59e0b!important;">Secure DB</div>
    <div class="sub">MongoDB Atlas</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── form ──────────────────────────────────────────────────
    c1, c2, c3 = st.columns([1, 2.2, 1])
    with c2:
        with st.form("reg_form"):
            st.markdown("""
<div style="text-align:center;margin-bottom:28px;">
  <div style="width:54px;height:54px;background:linear-gradient(135deg,#00b4db,#1565c0);
       border-radius:14px;display:inline-flex;align-items:center;justify-content:center;
       font-size:26px;margin-bottom:12px;box-shadow:0 6px 20px rgba(0,180,219,0.35);">🏥</div>
  <h3 style="font-family:'Outfit',sans-serif;font-size:1.35rem;font-weight:800;
       color:#e8f0fe!important;margin:0 0 4px;">Patient Registration</h3>
  <p style="font-size:12px;color:#90a4c8!important;margin:0;letter-spacing:.05em;">
    Secure · Encrypted · Confidential</p>
</div>
""", unsafe_allow_html=True)
            name             = st.text_input("Full Name", placeholder="Enter your full legal name")
            country_list     = [c.name for c in pycountry.countries]
            selected_country = st.selectbox("Country of Residence", country_list)
            country_obj      = pycountry.countries.get(name=selected_country)
            phone            = st.text_input("Mobile Number", placeholder="Local format — no country code")
            email            = st.text_input("Email Address", placeholder="you@hospital.com")
            address          = st.text_area("Residential Address", placeholder="Street, City, State, ZIP", height=88)
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("▶  Register & Access Clinical System", use_container_width=True)

            if submit:
                name    = name.strip(); phone = phone.strip()
                email   = email.strip(); address = address.strip()
                if not all([name, phone, email, address]):
                    st.error("❌ All fields are required."); return
                if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
                    st.error("❌ Invalid email address."); return
                try:
                    parsed = phonenumbers.parse(phone, country_obj.alpha_2)
                    if not phonenumbers.is_valid_number(parsed):
                        st.error("❌ Phone number doesn't match selected country."); return
                    fmt_phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                except Exception:
                    st.error("❌ Could not parse phone number."); return

                ist = pytz.timezone("Asia/Kolkata"); now = datetime.now(ist)
                pid = "PAT-" + str(uuid.uuid4().int)[:6]
                rec = {"_id": pid, "name": name, "phone": fmt_phone,
                       "country": selected_country, "email": email, "address": address,
                       "gender": "Not Selected", "created_at": now.strftime("%d-%m-%Y %I:%M:%S %p")}
                users_col.insert_one(rec)
                st.session_state.patient_info = rec
                st.session_state.registered   = True
                st.session_state.show_success  = True
                st.success("✅ Registration successful!")
                st.rerun()

    # ── trust strip ───────────────────────────────────────────
    st.markdown("""
<div class="a2" style="text-align:center;margin:28px 0 0;">
  <span class="pill" style="margin:4px;">🔐 256-bit TLS</span>
  <span class="pill pill-navy" style="margin:4px;">🏥 HIPAA-Aligned</span>
  <span class="pill pill-green" style="margin:4px;">⚡ Sub-second Inference</span>
  <span class="pill" style="margin:4px;">📦 MongoDB Atlas</span>
  <span class="pill pill-amber" style="margin:4px;">🩺 Clinical-Grade AI</span>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  MODEL
# ════════════════════════════════════════════════════════════════
@st.cache_resource
def load_model():
    try:
        return joblib.load("diabetes_model.pkl"), joblib.load("scaler_svm.pkl")
    except Exception as e:
        st.error(f"⚠️ Model load error: {e}"); st.stop()


# ════════════════════════════════════════════════════════════════
#  PREDICTION PAGE
# ════════════════════════════════════════════════════════════════
def prediction_page():
    model, scaler = load_model()
    if not st.session_state.patient_info:
        st.session_state.registered = False; st.stop()

    inject_css(get_b64("health22.png"))
    render_orbs()
    info = st.session_state.patient_info

    # ══ SIDEBAR ══════════════════════════════════════════════
    with st.sidebar:
        st.markdown(f"""
<div style="background:linear-gradient(135deg,rgba(0,180,219,0.10),rgba(21,101,192,0.08));
     border:1px solid rgba(0,180,219,0.18);border-radius:16px;padding:18px 16px;margin-bottom:8px;">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
    <div style="width:42px;height:42px;flex-shrink:0;
         background:linear-gradient(135deg,#00b4db,#1565c0);border-radius:11px;
         display:flex;align-items:center;justify-content:center;font-size:20px;
         box-shadow:0 4px 14px rgba(0,180,219,0.35);">🩺</div>
    <div>
      <div style="font-family:'Outfit',sans-serif;font-weight:800;font-size:14px;
           color:#e8f0fe!important;line-height:1.2;">{info.get('name','')}</div>
      <div style="font-family:'Space Mono',monospace;font-size:10px;
           color:#00b4db!important;letter-spacing:.06em;">{info.get('_id','')}</div>
    </div>
  </div>
  <div style="font-size:12px;color:#90a4c8!important;margin-bottom:2px;">📧 {info.get('email','')}</div>
  <div style="font-size:12px;color:#90a4c8!important;">📱 {info.get('phone','')}</div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="sec-lbl">Demographics</div>', unsafe_allow_html=True)
        age    = st.number_input("Age (Years)", 21, 100, 30)
        gender = st.selectbox("Biological Sex", ["Male", "Female"])
        pregnancies = st.number_input("Prior Pregnancies", 0, 20, 0) if gender == "Female" else 0

        st.markdown('<div class="sec-lbl">Glycemic Markers</div>', unsafe_allow_html=True)
        glucose = st.slider("Fasting Glucose (mg/dL)", 0, 200, 120)
        insulin = st.slider("Serum Insulin (IU/mL)", 0, 900, 80)

        st.markdown('<div class="sec-lbl">Cardiovascular</div>', unsafe_allow_html=True)
        bp   = st.slider("Diastolic BP (mmHg)", 0, 130, 70)
        skin = st.slider("Triceps Skin Fold (mm)", 0, 100, 20)

        st.markdown('<div class="sec-lbl">Biometrics</div>', unsafe_allow_html=True)
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
<div style="margin-top:22px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.06);">
  <div style="font-family:'Space Mono',monospace;font-size:9px;color:#4a5a80!important;
       letter-spacing:.1em;text-align:center;text-transform:uppercase;">
    MEDCORE AI · SVM Engine<br>Clinical Intelligence v2.0
  </div>
</div>
""", unsafe_allow_html=True)

    # ══ MAIN HEADER ═════════════════════════════════════════
    st.markdown("""
<div class="a0" style="text-align:center;padding:28px 0 6px;">
  <div style="display:inline-flex;gap:8px;margin-bottom:16px;">
    <span class="pill">🧬 Diagnostic AI Engine</span>
    <span class="pill pill-navy">SVM Architecture</span>
  </div>
  <h1 style="font-family:'Outfit',sans-serif;
      font-size:clamp(1.9rem,4.2vw,3.2rem);font-weight:900;letter-spacing:-0.04em;
      background:linear-gradient(110deg,#ffffff 8%,#00b4db 52%,#1565c0 100%);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
      margin-bottom:8px;">Diabetes Risk Intelligence</h1>
  <p style="color:#90a4c8!important;font-size:.88rem;letter-spacing:.07em;text-transform:uppercase;">
    Multiparametric Clinical Analysis · Evidence-Based Assessment
  </p>
</div>
""", unsafe_allow_html=True)

    if st.session_state.show_success:
        st.success("✅ Registration Successful! Secure clinical session established.")
        st.session_state.show_success = False

    # About This System
    st.markdown("""
<div class="a1" style="background:rgba(10,35,66,0.55);border:1px solid rgba(0,180,219,0.18);
     border-radius:18px;padding:24px 26px;margin-bottom:24px;position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;left:15%;right:15%;height:1px;
       background:linear-gradient(90deg,transparent,rgba(0,180,219,0.45),transparent);"></div>
  <div style="display:flex;align-items:flex-start;gap:16px;">
    <div style="font-size:38px;flex-shrink:0;line-height:1;">📋</div>
    <div>
      <h3 style="font-size:1.05rem;margin-bottom:7px;color:#e8f0fe!important;">About This System</h3>
      <p style="font-size:14px;line-height:1.75;color:#90a4c8!important;margin:0;">
        This Diabetes Prediction System is an AI-powered medical risk assessment tool designed to estimate
        the likelihood of diabetes based on key health parameters such as glucose level, BMI, blood pressure,
        age, and family history.
      </p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Idle state
    if not predict_btn:
        st.markdown("""
<div class="a2" style="background:rgba(10,35,66,0.45);border:1px solid rgba(0,180,219,0.14);
     border-radius:18px;padding:64px 32px;text-align:center;">
  <div style="width:72px;height:72px;
       background:linear-gradient(135deg,rgba(0,180,219,0.12),rgba(21,101,192,0.12));
       border:1px solid rgba(0,180,219,0.22);border-radius:20px;
       display:inline-flex;align-items:center;justify-content:center;
       font-size:36px;margin-bottom:20px;">🧬</div>
  <h2 style="font-size:1.2rem;color:#90a4c8!important;font-weight:600;margin-bottom:9px;">
    System Awaiting Input</h2>
  <p style="color:#4a5a80!important;font-size:13.5px;max-width:400px;margin:0 auto;">
    Configure clinical parameters in the sidebar and click
    <strong style="color:#00b4db!important;">Generate AI Assessment</strong> to begin.
  </p>
</div>
""", unsafe_allow_html=True)
        return

    # ══ PREDICTION LOGIC ════════════════════════════════════
    if "_id" in info:
        users_col.update_one({"_id": info["_id"]}, {"$set": {"gender": gender}})

    inp     = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
    prob    = model.predict_proba(scaler.transform(inp))[0]
    prob_neg = prob[0] * 100
    prob_pos = prob[1] * 100

    if prob_pos < 30:
        risk_label, risk_hex, r_cls, r_icon = "Low Risk",      "#00c896", "res-low",  "✅"
        risk_display = "LOW RISK — Diabetes Unlikely"
    elif prob_pos < 70:
        risk_label, risk_hex, r_cls, r_icon = "Moderate Risk", "#f59e0b", "res-mod",  "⚠️"
        risk_display = "MODERATE RISK — Possible Diabetes"
    else:
        risk_label, risk_hex, r_cls, r_icon = "High Risk",     "#e53935", "res-high", "🚨"
        risk_display = "HIGH RISK — Diabetes Likely"

    ist = pytz.timezone("Asia/Kolkata"); now = datetime.now(ist)
    preds_col.insert_one({
        "patient_id": info["_id"], "patient_name": info["name"],
        "age": age, "gender": gender, "glucose": glucose, "blood_pressure": bp,
        "bmi": bmi, "prediction": risk_label,
        "probability": round(prob_pos, 2),
        "created_at": now.strftime("%d-%m-%Y %H:%M:%S")
    })

    # ── Result banner ─────────────────────────────────────────
    st.markdown(f"""
<div class="res-card {r_cls} a0">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:18px;">
    <div>
      <div style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.14em;
           text-transform:uppercase;color:{risk_hex}!important;margin-bottom:9px;">
        {r_icon} DIAGNOSTIC OUTPUT · {now.strftime('%d %b %Y %I:%M %p IST')}
      </div>
      <h1 style="font-family:'Outfit',sans-serif;font-size:clamp(1.5rem,3.2vw,2.4rem);
           font-weight:900;letter-spacing:-.03em;color:{risk_hex}!important;margin:0 0 9px;">
        {risk_display}
      </h1>
      <p style="font-size:15px;color:#90a4c8!important;margin:0;">
        AI Probability Score:&nbsp;
        <span style="font-family:'Space Mono',monospace;font-size:19px;
             font-weight:700;color:{risk_hex}!important;">{prob_pos:.1f}%</span>
        &nbsp;diabetic likelihood
      </p>
    </div>
    <div style="text-align:right;flex-shrink:0;">
      <div style="font-family:'Space Mono',monospace;font-size:9px;
           color:#4a5a80!important;letter-spacing:.08em;text-transform:uppercase;margin-bottom:5px;">
        Patient ID</div>
      <div style="font-family:'Space Mono',monospace;font-size:13px;color:{risk_hex}!important;">
        {info.get('_id','')}</div>
      <div style="font-family:'Space Mono',monospace;font-size:9px;
           color:#4a5a80!important;margin-top:7px;letter-spacing:.08em;">
        MEDCORE AI · SVM ENGINE</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Probability metrics ────────────────────────────────────
    m1, m2 = st.columns(2)
    with m1: st.metric("Non-Diabetic Probability", f"{prob_neg:.1f}%")
    with m2: st.metric("Diabetic Probability",     f"{prob_pos:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Build cause data ──────────────────────────────────────
    cause_labels, cause_values = [], []
    if glucose >= 126: cause_labels.append("Hyperglycemia");  cause_values.append(min(glucose/2, 100))
    if bmi > 30:       cause_labels.append("Obesity (BMI)");  cause_values.append(min(bmi*2, 100))
    if age > 45:       cause_labels.append("Age Factor");     cause_values.append(min(age, 100))
    if bp > 120:       cause_labels.append("Hypertension");   cause_values.append(min(bp, 100))
    if dpf > 0.5:      cause_labels.append("Genetics (DPF)"); cause_values.append(min(dpf*100, 100))
    if not cause_labels:
        cause_labels = ["Healthy Indicators"]; cause_values = [100]

    # ── Plotly gauge + donut (dark, for screen) ───────────────
    st.markdown(f"""
<div style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em;
     text-transform:uppercase;color:#90a4c8!important;margin-bottom:6px;">
  Prediction Results
</div>""", unsafe_allow_html=True)

    cg1, cg2 = st.columns(2)
    with cg1:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=prob_pos,
            number={"suffix":"%","font":{"family":"Space Mono","color":"white","size":26}},
            title={"text":"Risk Level","font":{"color":"#90a4c8","size":13}},
            gauge={
                "axis":      {"range":[0,100],"tickcolor":"rgba(255,255,255,0.2)","tickwidth":1},
                "bar":       {"color":risk_hex,"thickness":0.22},
                "bgcolor":   "rgba(0,0,0,0)", "borderwidth":0,
                "steps":     [{"range":[0,30],"color":"rgba(0,200,150,0.14)"},
                              {"range":[30,70],"color":"rgba(245,158,11,0.14)"},
                              {"range":[70,100],"color":"rgba(229,57,53,0.14)"}],
                "threshold": {"line":{"color":risk_hex,"width":3},"thickness":0.78,"value":prob_pos}
            }
        ))
        gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)",font=dict(color="white"),
                            height=255,margin=dict(l=18,r=18,t=28,b=10))
        st.plotly_chart(gauge, use_container_width=True, config={"responsive":True})

    pie_colors_screen = [HOSP_COLORS[i % len(HOSP_COLORS)] for i in range(len(cause_labels))]
    with cg2:
        pie_screen = go.Figure(go.Pie(
            labels=cause_labels, values=cause_values, hole=0.55,
            marker=dict(colors=pie_colors_screen, line=dict(color="rgba(0,0,0,0.4)", width=2)),
            textfont=dict(family="Space Mono", size=11, color="white"),
            textposition="inside", textinfo="percent+label", showlegend=False
        ))
        pie_screen.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
            height=255, margin=dict(l=8,r=8,t=28,b=8),
            title=dict(text="Etiology Breakdown",font=dict(color="#90a4c8",size=13))
        )
        st.plotly_chart(pie_screen, use_container_width=True, config={"responsive":True})

    # ── Plotly bar (dark, for screen) ──────────────────────────
    st.markdown("""
<div style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em;
     text-transform:uppercase;color:#90a4c8!important;margin:6px 0 8px;">
  📊 Causes of Diabetes (Risk Contribution Analysis)
</div>""", unsafe_allow_html=True)

    bar_screen = go.Figure(go.Bar(
        x=cause_labels, y=cause_values,
        text=[f"{v:.1f}" for v in cause_values], textposition="auto",
        textfont=dict(family="Space Mono", color="white", size=12),
        marker=dict(
            color=[HOSP_COLORS[i % len(HOSP_COLORS)] for i in range(len(cause_labels))],
            line=dict(color="rgba(255,255,255,0.1)", width=1)
        )
    ))
    bar_screen.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#90a4c8", family="Manrope"),
        xaxis=dict(tickfont=dict(color="#90a4c8",size=12),title="Risk Factors",
                   title_font=dict(color="#90a4c8"),showline=True,linecolor="rgba(255,255,255,0.1)"),
        yaxis=dict(tickfont=dict(color="#90a4c8",size=12),title="Severity Score",
                   title_font=dict(color="#90a4c8"),gridcolor="rgba(255,255,255,0.05)",
                   zerolinecolor="rgba(255,255,255,0.1)"),
        margin=dict(l=18,r=18,t=16,b=18), autosize=True
    )
    st.plotly_chart(bar_screen, use_container_width=True, config={"responsive":True})

    # ── Risk Factor Analysis ───────────────────────────────────
    st.markdown("""
<div style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em;
     text-transform:uppercase;color:#90a4c8!important;margin:18px 0 12px;">
  🔬 Risk Factor Analysis
</div>""", unsafe_allow_html=True)

    risk_factors, positive_factors = [], []
    if glucose >= 126:         risk_factors.append("High Glucose Level (≥126 mg/dL)")
    elif 100 <= glucose < 126: risk_factors.append("Prediabetic Glucose Level (100–125 mg/dL)")
    else:                      positive_factors.append("Normal Glucose Level (<100 mg/dL)")
    if bmi > 30:               risk_factors.append("High BMI (Obesity)")
    elif 18.5 <= bmi <= 24.9:  positive_factors.append("Healthy BMI")
    if age > 45:               risk_factors.append("Age above 45")
    if bp > 120:               risk_factors.append("High Blood Pressure (>120 mmHg)")
    elif 90 <= bp <= 120:      positive_factors.append("Normal Blood Pressure")
    if dpf > 0.5:              risk_factors.append("Higher Genetic Risk (DPF > 0.5)")

    # ── KEY FIX: use st.container() so widgets render INSIDE the styled area ──
    rf_col, pf_col = st.columns(2)

    with rf_col:
        # styled header + badges rendered as pure HTML (no nested widgets)
        risk_html = '<div style="background:rgba(10,35,66,0.6);border:1px solid rgba(229,57,53,0.22);border-radius:16px;padding:22px 20px;min-height:160px;">'
        risk_html += '<div style="font-family:\'Outfit\',sans-serif;font-weight:700;font-size:14px;color:#ef9a9a!important;margin-bottom:14px;">⚠️ Identified Risk Factors</div>'
        if risk_factors:
            for f in risk_factors:
                risk_html += f'<div class="risk-badge">🚨 {f}</div>'
        else:
            risk_html += '<p class="empty-state">No critical risk vectors detected.</p>'
        risk_html += '</div>'
        st.markdown(risk_html, unsafe_allow_html=True)

    with pf_col:
        safe_html = '<div style="background:rgba(10,35,66,0.6);border:1px solid rgba(0,200,150,0.22);border-radius:16px;padding:22px 20px;min-height:160px;">'
        safe_html += '<div style="font-family:\'Outfit\',sans-serif;font-weight:700;font-size:14px;color:#80cbc4!important;margin-bottom:14px;">🛡️ Positive Health Indicators</div>'
        if positive_factors:
            for f in positive_factors:
                safe_html += f'<div class="safe-badge">✅ {f}</div>'
        else:
            safe_html += '<p class="empty-state">No protective factors highlighted.</p>'
        safe_html += '</div>'
        st.markdown(safe_html, unsafe_allow_html=True)

    # ── Recommendations ────────────────────────────────────────
    st.markdown("""
<div style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em;
     text-transform:uppercase;color:#90a4c8!important;margin:20px 0 12px;">
  💊 Medical Recommendations
</div>""", unsafe_allow_html=True)

    if prob_pos >= 70:
        st.error("- Consult a healthcare professional immediately\n- Get complete diabetes screening\n- Monitor blood sugar regularly\n- Improve diet and physical activity")
        recs_for_pdf = ["Consult a healthcare professional immediately",
                        "Get complete diabetes screening",
                        "Monitor blood sugar regularly",
                        "Improve diet and physical activity"]
    elif prob_pos >= 30:
        st.warning("- Maintain healthy diet\n- Increase physical activity\n- Monitor glucose periodically")
        recs_for_pdf = ["Maintain healthy diet", "Increase physical activity", "Monitor glucose periodically"]
    else:
        st.success("- Continue healthy lifestyle\n- Exercise regularly\n- Routine health check-ups")
        recs_for_pdf = ["Continue healthy lifestyle", "Exercise regularly", "Routine health check-ups"]

    # ══ PDF GENERATION ══════════════════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)

    # Generate matplotlib chart PNGs (white background — perfect for PDF)
    bar_png_bytes = make_bar_png(cause_labels, cause_values)
    pie_png_bytes = make_pie_png(cause_labels, cause_values)

    buf    = BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=letter,
                                rightMargin=40, leftMargin=40,
                                topMargin=40, bottomMargin=40)
    elems  = []
    styles = getSampleStyleSheet()

    # PDF styles
    t_title  = ParagraphStyle("TT", parent=styles["Heading1"], fontSize=20,
                               textColor=colors.HexColor("#0a2342"), alignment=1,
                               spaceAfter=5, fontName="Helvetica-Bold")
    t_date   = ParagraphStyle("TD", parent=styles["Normal"], fontSize=10,
                               textColor=colors.dimgrey, alignment=1,
                               spaceAfter=18, fontName="Helvetica-Oblique")
    t_head   = ParagraphStyle("TH", parent=styles["Heading2"], fontSize=13,
                               textColor=colors.HexColor("#0d3060"),
                               spaceBefore=14, spaceAfter=9,
                               fontName="Helvetica-Bold", borderPadding=5,
                               backColor=colors.HexColor("#e8f0fe"))
    t_norm   = ParagraphStyle("TN", parent=styles["Normal"], fontSize=11, spaceAfter=5)
    t_addr   = ParagraphStyle("TA", parent=styles["Normal"], fontSize=11, leading=14)

    # Title
    elems.append(Paragraph("🩺 DIABETES RISK PREDICTION REPORT", t_title))
    elems.append(Paragraph(f"Report Generated: {now.strftime('%d %B %Y | %I:%M %p (IST)')}", t_date))

    # Patient profile table
    addr_p = Paragraph(info.get("address","N/A"), t_addr)
    pt = Table([
        ["Patient ID",    info.get("_id","N/A")],
        ["Full Name",     info.get("name","N/A")],
        ["Email",         info.get("email","N/A")],
        ["Phone",         info.get("phone","N/A")],
        ["Country",       info.get("country","N/A")],
        ["Address",       addr_p],
    ], colWidths=[2.2*inch, 4.3*inch])
    pt.setStyle(TableStyle([
        ("GRID",       (0,0),(-1,-1), 0.5, colors.HexColor("#c8d0e0")),
        ("BACKGROUND", (0,0),(0,-1),  colors.HexColor("#e8f0fe")),
        ("FONTNAME",   (0,0),(0,-1),  "Helvetica-Bold"),
        ("TEXTCOLOR",  (0,0),(0,-1),  colors.HexColor("#0a2342")),
        ("PADDING",    (0,0),(-1,-1), 8),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
    ]))
    elems += [Paragraph("Patient Profile", t_head), pt, Spacer(1, 0.18*inch)]

    # Clinical inputs table
    med = [
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
        med.insert(2, ["Pregnancies", str(pregnancies)])
    mt = Table(med, colWidths=[2.2*inch, 4.3*inch])
    mt.setStyle(TableStyle([
        ("GRID",       (0,0),(-1,-1), 0.5, colors.HexColor("#c8d0e0")),
        ("BACKGROUND", (0,0),(0,-1),  colors.HexColor("#e8f0fe")),
        ("FONTNAME",   (0,0),(0,-1),  "Helvetica-Bold"),
        ("TEXTCOLOR",  (0,0),(0,-1),  colors.HexColor("#0a2342")),
        ("PADDING",    (0,0),(-1,-1), 8),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
    ]))
    elems += [Paragraph("Clinical Inputs", t_head), mt, Spacer(1, 0.25*inch)]

    # Risk result
    col_map = {"Low Risk":"#007a5e", "Moderate Risk":"#b45309", "High Risk":"#b91c1c"}
    lbl_map = {
        "Low Risk":      "LOW RISK — Diabetes Unlikely",
        "Moderate Risk": "MODERATE RISK — Possible Diabetes",
        "High Risk":     "HIGH RISK — Diabetes Likely",
    }
    elems.append(Paragraph("Risk Assessment Result", t_head))
    elems.append(Paragraph(
        f"<b>Overall Risk Level:</b> <font color='{col_map[risk_label]}'>"
        f"<b>{lbl_map[risk_label]}</b></font>", t_norm))
    elems.append(Paragraph(f"<b>Risk Percentage:</b> {prob_pos:.1f}%", t_norm))
    elems.append(Spacer(1, 0.18*inch))

    # ── CHARTS in PDF (matplotlib, white bg) ──────────────────
    elems.append(Paragraph("Data Visualization & Analysis", t_head))

    bar_img = RLImage(BytesIO(bar_png_bytes), width=3.3*inch, height=2.2*inch)
    pie_img = RLImage(BytesIO(pie_png_bytes), width=3.3*inch, height=2.2*inch)

    chart_tbl = Table([[bar_img, pie_img]], colWidths=[3.4*inch, 3.4*inch])
    chart_tbl.setStyle(TableStyle([
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("BOX",           (0,0),(-1,-1), 1.0, colors.HexColor("#c8d0e0")),
        ("INNERGRID",     (0,0),(-1,-1), 0.5, colors.HexColor("#e0e6f0")),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#f8faff")),
    ]))
    elems.append(chart_tbl)
    elems.append(Spacer(1, 0.18*inch))

    # Recommendations
    elems.append(Paragraph("Medical Recommendations", t_head))
    elems.append(ListFlowable(
        [ListItem(Paragraph(r, t_norm)) for r in recs_for_pdf],
        bulletType="bullet"
    ))
    elems.append(Spacer(1, 0.35*inch))
    elems.append(Paragraph(
        "<b>Medical Disclaimer:</b> This report is AI-generated and does "
        "not replace professional medical advice. Please consult a qualified "
        "healthcare professional for diagnosis and treatment.",
        styles["Italic"]
    ))

    doc.build(elems)
    pdf_bytes = buf.getvalue(); buf.close()

    st.download_button(
        label="📄 Download Professional Medical Report (PDF)",
        data=pdf_bytes,
        file_name=f"Diabetes_Report_{info.get('name','Patient')}.pdf",
        mime="application/pdf",
    )

    st.markdown("---")
    st.warning("⚠️ Medical Disclaimer: This tool does NOT replace professional medical advice.")


# ════════════════════════════════════════════════════════════════
#  NAVIGATION
# ════════════════════════════════════════════════════════════════
if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
