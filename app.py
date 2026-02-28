# ================================================================
#  MEDCORE AI  —  Diabetes Intelligence Platform
#  Clean architecture: targeted CSS only, no catch-alls,
#  pure Streamlit widgets for content, HTML only for decoration.
# ================================================================

import streamlit as st
import numpy as np
import joblib
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import base64, re, uuid, pytz, time
import pycountry, phonenumbers
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

# ─────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────
def b64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        # Fallback to empty string if image is not found during dev
        return ""

# ─────────────────────────────────────────────────────────────
#  MongoDB
# ─────────────────────────────────────────────────────────────
_URI      = "mongodb+srv://diabetes_user:Diabetes%40123@diabetescluster.oxegep6.mongodb.net/?retryWrites=true&w=majority"
try:
    _mc       = MongoClient(_URI, server_api=ServerApi("1"), serverSelectionTimeoutMS=5000)
    _db       = _mc["diabetes_app"]
    users_col = _db["registered_users"]
    preds_col = _db["predictions"]
except Exception as e:
    st.warning("Running in local mode. Database connection failed.")

# ─────────────────────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MEDCORE AI — Diabetes Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
#  Session state
# ─────────────────────────────────────────────────────────────
st.session_state.setdefault("registered",    False)
st.session_state.setdefault("patient_info",  {})
st.session_state.setdefault("show_success",  False)
st.session_state.setdefault("model_ran",     False)

# ─────────────────────────────────────────────────────────────
#  Hospital colour constants
# ─────────────────────────────────────────────────────────────
C_CYAN   = "#00b4db"
C_BLUE   = "#1565c0"
C_NAVY   = "#0a2342"
C_GREEN  = "#00c896"
C_AMBER  = "#f59e0b"
C_RED    = "#e53935"
C_TEXT   = "#e8f0fe"
C_MUTED  = "#8ba4c8"

CHART_PALETTE = [C_RED, C_AMBER, C_BLUE, "#7c3aed", C_GREEN]

# ═════════════════════════════════════════════════════════════
#  MASTER CSS
# ═════════════════════════════════════════════════════════════
def inject_css(img_b64: str, overlay: str = "rgba(4,10,26,0.85)"):
    bg_rule = f'background: linear-gradient({overlay}, {overlay}), url("data:image/png;base64,{img_b64}") center / cover fixed;' if img_b64 else f'background: {overlay};'
    
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&family=Space+Mono:wght@400;700&family=Manrope:wght@400;500;600;700&display=swap');

/* ── BACKGROUND ── */
.stApp {{
    {bg_rule}
    font-family: 'Manrope', sans-serif;
}}

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, header, .stDeployButton {{ display:none!important; }}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {{ width:5px; }}
::-webkit-scrollbar-thumb {{ background:rgba(0,180,219,.4); border-radius:99px; }}

/* ── ALL HEADINGS WHITE ── */
h1,h2,h3,h4,h5,h6 {{
    font-family:'Outfit',sans-serif!important;
    color:{C_TEXT}!important;
    letter-spacing:-.02em;
}}

/* ── SIDEBAR SHELL ── */
section[data-testid="stSidebar"] {{
    background:rgba(4,10,26,.95)!important;
    backdrop-filter:blur(24px)!important;
    border-right:1px solid rgba(0,180,219,.15)!important;
}}
section[data-testid="stSidebar"] > div {{ padding-top:12px!important; }}

/* Sidebar text / labels */
section[data-testid="stSidebar"] label {{
    color:{C_MUTED}!important;
    font-family:'Space Mono',monospace!important;
    font-size:10px!important;
    letter-spacing:.13em!important;
    text-transform:uppercase!important;
    font-weight:700!important;
}}
section[data-testid="stSidebar"] p {{
    color:{C_MUTED}!important;
    font-size:13px;
}}

/* Sidebar inputs — light so text always dark & readable */
section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    background:#ddeeff!important;
    border:1.5px solid #8ba4c8!important;
    border-radius:10px!important;
}}
section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {{
    border-color:{C_CYAN}!important;
    box-shadow:0 0 0 3px rgba(0,180,219,.18)!important;
}}
section[data-testid="stSidebar"] div[data-baseweb="input"] input {{
    color:#061020!important;
    -webkit-text-fill-color:#061020!important;
    font-family:'Space Mono',monospace!important;
    font-weight:700!important;
    font-size:14px!important;
}}
section[data-testid="stSidebar"] div[data-baseweb="select"] span {{
    color:#061020!important;
    font-weight:700!important;
}}

/* Spinner buttons — hide */
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button {{ -webkit-appearance:none; }}
input[type=number] {{ -moz-appearance:textfield; }}

/* Slider handle */
div[data-baseweb="slider"] [role="slider"] {{
    background:{C_CYAN}!important;
    border:2px solid #fff!important;
    box-shadow:0 0 10px rgba(0,180,219,.7)!important;
}}
div[data-testid="stTickBar"] {{ display:none!important; }}

/* ── SIDEBAR BUTTONS ── */
section[data-testid="stSidebar"] button {{
    background:linear-gradient(135deg,{C_CYAN},{C_BLUE})!important;
    border:none!important;
    color:#ffffff!important;
    font-family:'Outfit',sans-serif!important;
    font-weight:800!important;
    font-size:13px!important;
    letter-spacing:.06em!important;
    text-transform:uppercase!important;
    border-radius:12px!important;
    height:46px!important;
    box-shadow:0 4px 16px rgba(0,180,219,.3)!important;
    transition:all .25s ease!important;
}}
section[data-testid="stSidebar"] button:hover {{
    transform:translateY(-2px)!important;
    box-shadow:0 8px 24px rgba(0,180,219,.45)!important;
}}

/* ── MAIN AREA BUTTONS (form submit) ── */
div[data-testid="stForm"] button {{
    background:linear-gradient(135deg,{C_CYAN},{C_BLUE})!important;
    border:none!important;
    color:#ffffff!important;
    font-family:'Outfit',sans-serif!important;
    font-weight:800!important;
    font-size:14px!important;
    text-transform:uppercase!important;
    letter-spacing:.06em!important;
    border-radius:12px!important;
    height:52px!important;
    box-shadow:0 4px 20px rgba(0,180,219,.32)!important;
    transition:all .25s ease!important;
}}
div[data-testid="stForm"] button:hover {{
    transform:translateY(-2px) scale(1.01)!important;
    box-shadow:0 8px 28px rgba(0,180,219,.5)!important;
}}

/* ── DOWNLOAD BUTTON ── */
div.stDownloadButton > button {{
    background:linear-gradient(135deg,{C_GREEN},#007a5e)!important;
    border:none!important;
    color:#ffffff!important;
    font-family:'Outfit',sans-serif!important;
    font-weight:800!important;
    font-size:15px!important;
    border-radius:12px!important;
    padding:14px 0!important;
    width:100%!important;
    box-shadow:0 4px 18px rgba(0,200,150,.3)!important;
    transition:all .25s ease!important;
}}
div.stDownloadButton > button:hover {{
    transform:translateY(-3px)!important;
    box-shadow:0 10px 32px rgba(0,200,150,.5)!important;
}}

/* ── REGISTRATION FORM CARD ── */
div[data-testid="stForm"] {{
    background:rgba(4,10,26,.85)!important;
    backdrop-filter:blur(28px)!important;
    border-radius:24px!important;
    padding:46px 42px!important;
    max-width:560px;
    margin:3vh auto;
    border:1px solid rgba(0,180,219,.2)!important;
    box-shadow:0 24px 64px rgba(0,0,0,.6)!important;
    position:relative;
}}
div[data-testid="stForm"]::before {{
    content:''; position:absolute; top:0; left:20%; right:20%; height:1px;
    background:linear-gradient(90deg,transparent,{C_CYAN},transparent);
    border-radius:0 0 99px 99px;
}}

div[data-testid="stForm"] label {{
    color:{C_MUTED}!important;
    font-family:'Space Mono',monospace!important;
    font-size:10px!important;
    letter-spacing:.13em!important;
    text-transform:uppercase!important;
    font-weight:700!important;
}}

div[data-testid="stForm"] div[data-baseweb="input"] > div,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div {{
    background:rgba(255,255,255,.07)!important;
    border:1.5px solid rgba(255,255,255,.12)!important;
    border-radius:10px!important;
    transition:all .25s;
}}
div[data-testid="stForm"] div[data-baseweb="input"] > div:focus-within,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div:focus-within {{
    border-color:{C_CYAN}!important;
    box-shadow:0 0 0 3px rgba(0,180,219,.14)!important;
    background:rgba(255,255,255,.10)!important;
}}
div[data-testid="stForm"] input,
div[data-testid="stForm"] textarea {{
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    font-family:'Manrope',sans-serif!important;
    font-size:15px!important;
    font-weight:500!important;
}}

div[data-testid="stForm"] div[data-baseweb="select"] > div {{
    background:rgba(255,255,255,.07)!important;
    border:1.5px solid rgba(255,255,255,.12)!important;
    border-radius:10px!important;
}}
div[data-testid="stForm"] div[data-baseweb="select"] span {{
    color:#ffffff!important;
    font-weight:500!important;
}}

/* ── METRICS ── */
div[data-testid="metric-container"] {{
    background:rgba(10,35,66,.7)!important;
    border:1px solid rgba(0,180,219,.22)!important;
    border-radius:14px!important;
    padding:18px!important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-family:'Space Mono',monospace!important;
    font-size:2rem!important;
    color:{C_CYAN}!important;
}}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    font-family:'Space Mono',monospace!important;
    font-size:10px!important;
    letter-spacing:.1em!important;
    text-transform:uppercase!important;
    color:{C_MUTED}!important;
}}

/* ── ALERT BOXES ── */
div[data-testid="stSuccess"] {{ background:rgba(0,200,150,.09)!important; border:1px solid rgba(0,200,150,.35)!important; border-radius:12px!important; }}
div[data-testid="stSuccess"] p  {{ color:#80cbc4!important; font-weight:600; }}
div[data-testid="stWarning"] {{ background:rgba(245,158,11,.09)!important; border:1px solid rgba(245,158,11,.35)!important; border-radius:12px!important; }}
div[data-testid="stWarning"] p  {{ color:#ffd54f!important; font-weight:600; }}
div[data-testid="stError"] {{ background:rgba(229,57,53,.09)!important; border:1px solid rgba(229,57,53,.35)!important; border-radius:12px!important; }}
div[data-testid="stError"] p  {{ color:#ef9a9a!important; font-weight:600; }}

hr {{ border-color:rgba(0,180,219,.15)!important; }}

/* ── ANIMATIONS ── */
@keyframes fadeUp {{ from {{ opacity:0; transform:translateY(16px); }} to {{ opacity:1; transform:translateY(0); }} }}
.fadeA {{ animation:fadeUp .5s ease both; }}
.fadeB {{ animation:fadeUp .5s .12s ease both; }}
.fadeC {{ animation:fadeUp .5s .24s ease both; }}

@keyframes orbDrift {{ 0%,100% {{ transform:translate(0,0); }} 45% {{ transform:translate(28px,-22px); }} 70% {{ transform:translate(-18px,14px); }} }}
.orb {{ position:fixed; border-radius:50%; pointer-events:none; z-index:0; animation:orbDrift 15s ease-in-out infinite; }}

@media(max-width:768px) {{ div[data-testid="stForm"] {{ padding:26px 18px!important; }} }}
</style>
""", unsafe_allow_html=True)


def render_orbs():
    st.markdown("""
<div class="orb" style="width:500px;height:500px;top:-130px;left:-90px; background:radial-gradient(circle,rgba(0,180,219,.065) 0%,transparent 70%); animation-delay:0s;"></div>
<div class="orb" style="width:340px;height:340px;bottom:-70px;right:-50px; background:radial-gradient(circle,rgba(21,101,192,.07) 0%,transparent 70%); animation-delay:5s;"></div>
<div class="orb" style="width:220px;height:220px;top:42%;left:60%; background:radial-gradient(circle,rgba(0,200,150,.05) 0%,transparent 70%); animation-delay:9s;"></div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  MATPLOTLIB chart helpers
# ═════════════════════════════════════════════════════════════
def _bar_png(labels, values):
    fig, ax = plt.subplots(figsize=(5.2, 3.2), dpi=140)
    fig.patch.set_facecolor("#f4f8ff")
    ax.set_facecolor("#f4f8ff")

    cols = [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(len(labels))]
    bars = ax.bar(labels, values, color=cols, width=0.52, edgecolor="#ccd6f0", linewidth=.8)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{v:.1f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0a1a3a")

    ax.set_ylim(0, max(values)*1.28 if values else 110)
    ax.set_xlabel("Risk Factors", fontsize=9, color="#3a4a6a", labelpad=5)
    ax.set_ylabel("Severity Score", fontsize=9, color="#3a4a6a", labelpad=5)
    ax.set_title("Risk Factor Severity", fontsize=11, fontweight="bold", color="#0a1a3a", pad=8)
    ax.tick_params(axis="x", labelsize=8, colors="#3a4a6a")
    ax.tick_params(axis="y", labelsize=8, colors="#3a4a6a")
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#bcc8e0")
    ax.yaxis.grid(True, color="#dce6f5", linewidth=.6, linestyle="--")
    ax.set_axisbelow(True)
    plt.tight_layout(pad=1.1)

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#f4f8ff")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _pie_png(labels, values):
    fig, ax = plt.subplots(figsize=(4.8, 3.4), dpi=140)
    fig.patch.set_facecolor("#f4f8ff")
    cols = [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(len(labels))]
    wedges, texts, autos = ax.pie(
        values, labels=labels, colors=cols, autopct="%1.1f%%", startangle=130,
        wedgeprops=dict(width=0.58, edgecolor="#f4f8ff", linewidth=1.8), pctdistance=0.78,
    )
    for t  in texts: t.set_fontsize(8);  t.set_color("#1a2340")
    for at in autos: at.set_fontsize(7.5); at.set_fontweight("bold"); at.set_color("#1a2340")
    ax.set_title("Risk Contribution (%)", fontsize=11, fontweight="bold", color="#0a1a3a", pad=8)
    plt.tight_layout(pad=1.1)

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#f4f8ff")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ═════════════════════════════════════════════════════════════
#  REPORTLAB PAGE TEMPLATE (Header/Footer)
# ═════════════════════════════════════════════════════════════
def report_header_footer(canvas, doc):
    canvas.saveState()
    
    # Header Area
    canvas.setFillColorRGB(0.04, 0.14, 0.26)
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(40, letter[1] - 45, "MEDCORE AI CLINICAL SYSTEMS")
    
    canvas.setFillColorRGB(0.4, 0.5, 0.6)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(40, letter[1] - 60, "123 Innovation Drive, Medical Technology Park, NY 10001")
    canvas.drawString(40, letter[1] - 72, "Phone: +1 (800) 555-0199  |  Email: records@medcore.ai")
    
    # Aesthetic Line
    canvas.setLineWidth(1.5)
    canvas.setStrokeColorRGB(0.0, 0.70, 0.86)
    canvas.line(40, letter[1] - 85, letter[0] - 40, letter[1] - 85)
    
    # Footer Area
    canvas.setLineWidth(0.5)
    canvas.setStrokeColorRGB(0.8, 0.8, 0.8)
    canvas.line(40, 50, letter[0] - 40, 50)
    
    canvas.setFont("Helvetica", 8)
    canvas.setFillColorRGB(0.5, 0.5, 0.5)
    canvas.drawString(40, 35, "CONFIDENTIAL MEDICAL DOCUMENT - DO NOT DISTRIBUTE WITHOUT AUTHORIZATION")
    canvas.drawRightString(letter[0] - 40, 35, f"Page {doc.page}")
    
    canvas.restoreState()


# ═════════════════════════════════════════════════════════════
#  REGISTRATION PAGE
# ═════════════════════════════════════════════════════════════
def registration_page():
    inject_css(b64("health.png"), overlay="rgba(4,10,26,.80)")
    render_orbs()

    st.markdown(f"""
<div class="fadeA" style="text-align:center;padding:44px 0 16px;">
  <div style="display:inline-flex;align-items:center;gap:8px; background:rgba(0,180,219,.1); border:1px solid rgba(0,180,219,.28); border-radius:99px;padding:6px 18px;margin-bottom:20px;">
    <span style="font-family:'Space Mono',monospace;font-size:11px; color:{C_CYAN};letter-spacing:.08em;">🧬 MEDCORE AI · CLINICAL INTELLIGENCE v2.0</span>
  </div>
  <h1 style="font-family:'Outfit',sans-serif!important; font-size:clamp(2.4rem,5.5vw,3.8rem); font-weight:900;letter-spacing:-.05em;line-height:1.05; background:linear-gradient(110deg,#ffffff 5%,{C_CYAN} 50%,{C_BLUE} 100%); -webkit-background-clip:text;-webkit-text-fill-color:transparent; background-clip:text;margin:0 0 14px;">Diabetes Risk<br>Intelligence Platform</h1>
  <p style="font-family:'Manrope',sans-serif;font-size:.95rem; color:{C_MUTED};letter-spacing:.07em;text-transform:uppercase;margin:0;">Precision · Clinical Grade · AI-Powered · Real-Time</p>
</div>
""", unsafe_allow_html=True)

    fc1, fc2, fc3, fc4 = st.columns(4)
    def feat(col, icon, title, sub, col_hex):
        with col:
            st.markdown(f"""<div class="fadeB" style="background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08); border-radius:16px;padding:18px 12px; text-align:center; transition:border-color .3s,transform .3s;"> <div style="font-size:28px;margin-bottom:8px;">{icon}</div> <div style="font-family:'Outfit',sans-serif;font-weight:700; font-size:13px;color:{col_hex};">{title}</div> <div style="font-size:11px;color:{C_MUTED};margin-top:3px;">{sub}</div></div>""", unsafe_allow_html=True)

    feat(fc1, "🤖", "SVM Engine",    "Support Vector Machine", C_CYAN)
    feat(fc2, "📊", "8 Biomarkers",  "Clinical Parameters",    C_BLUE)
    feat(fc3, "⚡", "Real-Time",     "Instant Analysis",       C_GREEN)
    feat(fc4, "🔒", "Secure DB",     "MongoDB Atlas",          C_AMBER)

    st.markdown("<br>", unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2.1, 1])
    with mid:
        st.markdown(f"""<div style="text-align:center;margin-bottom:24px;"> <div style="width:52px;height:52px; background:linear-gradient(135deg,{C_CYAN},{C_BLUE}); border-radius:14px; display:inline-flex;align-items:center;justify-content:center; font-size:24px;margin-bottom:12px; box-shadow:0 6px 20px rgba(0,180,219,.35);">🏥</div> <h3 style="font-family:'Outfit',sans-serif!important; font-size:1.3rem;font-weight:800;color:{C_TEXT}!important;margin:0 0 4px;">Patient Registration</h3> <p style="font-family:'Manrope',sans-serif;font-size:12px; color:{C_MUTED};letter-spacing:.05em;margin:0;">Secure · Encrypted · Confidential</p></div>""", unsafe_allow_html=True)

        with st.form("reg_form"):
            name             = st.text_input("Full Name",             placeholder="Enter your full legal name")
            country_list     = [c.name for c in pycountry.countries]
            selected_country = st.selectbox("Country of Residence",  country_list)
            country_obj      = pycountry.countries.get(name=selected_country)
            phone            = st.text_input("Mobile Number",        placeholder="Local format — no country code")
            email            = st.text_input("Email Address",        placeholder="you@hospital.com")
            address          = st.text_area( "Residential Address",  placeholder="Street, City, State, ZIP", height=86)
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("▶  Register & Access Clinical System", use_container_width=True)

            if submit:
                name    = name.strip();   phone   = phone.strip()
                email   = email.strip();  address = address.strip()

                if not all([name, phone, email, address]):
                    st.error("❌ All fields are required."); st.stop()

                if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
                    st.error("❌ Invalid email address."); st.stop()

                try:
                    parsed = phonenumbers.parse(phone, country_obj.alpha_2)
                    if not phonenumbers.is_valid_number(parsed):
                        st.error("❌ Phone doesn't match country."); st.stop()
                    fmt_ph = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                except Exception:
                    st.error("❌ Cannot parse phone number."); st.stop()

                ist = pytz.timezone("Asia/Kolkata"); now = datetime.now(ist)
                pid = "PAT-" + str(uuid.uuid4().int)[:6]
                rec = {
                    "_id": pid, "name": name, "phone": fmt_ph,
                    "country": selected_country, "email": email,
                    "address": address, "gender": "Not Selected",
                    "created_at": now.strftime("%d-%m-%Y %I:%M:%S %p"),
                }
                try:
                    users_col.insert_one(rec)
                except Exception:
                    pass # Ignore if DB not connected
                
                st.session_state.patient_info = rec
                st.session_state.registered   = True
                st.session_state.show_success  = True
                st.rerun()

    st.markdown(f"""<div class="fadeC" style="text-align:center;margin:24px 0 0;"> {''.join(f'<span style="display:inline-flex;align-items:center;gap:5px;background:rgba(0,180,219,.1);border:1px solid rgba(0,180,219,.22);border-radius:99px;padding:5px 13px;margin:4px;font-family:Space Mono,monospace;font-size:10.5px;color:{C_CYAN};letter-spacing:.06em;">{t}</span>' for t in ["🔐 256-bit TLS","🏥 HIPAA-Aligned","⚡ Sub-second AI","📦 MongoDB Atlas","🩺 Clinical-Grade"])}</div>""", unsafe_allow_html=True)


@st.cache_resource
def load_model():
    try:
        return joblib.load("diabetes_model.pkl"), joblib.load("scaler_svm.pkl")
    except Exception as e:
        st.error(f"⚠️ Model load error: {e}"); st.stop()


def prediction_page():
    model, scaler = load_model()
    if not st.session_state.patient_info:
        st.session_state.registered = False; st.stop()

    inject_css(b64("health22.png"))
    render_orbs()
    info = st.session_state.patient_info

    # ══ SIDEBAR ═══════════════════════════════════════════════
    with st.sidebar:
        st.markdown(f"""<div style="background:linear-gradient(135deg,rgba(0,180,219,.10),rgba(21,101,192,.08)); border:1px solid rgba(0,180,219,.20); border-radius:14px;padding:16px 14px;margin-bottom:10px;"> <div style="display:flex;align-items:center;gap:11px;margin-bottom:10px;"> <div style="width:40px;height:40px;flex-shrink:0; background:linear-gradient(135deg,{C_CYAN},{C_BLUE}); border-radius:10px; display:flex;align-items:center;justify-content:center; font-size:19px;box-shadow:0 4px 12px rgba(0,180,219,.35);">🩺</div> <div> <div style="font-family:'Outfit',sans-serif;font-weight:800; font-size:14px;color:{C_TEXT};">{info.get('name','')}</div> <div style="font-family:'Space Mono',monospace;font-size:10px; color:{C_CYAN};letter-spacing:.05em;">{info.get('_id','')}</div> </div> </div> <div style="font-size:12px;color:{C_MUTED};margin-bottom:2px;"> 📧 {info.get('email','')}</div> <div style="font-size:12px;color:{C_MUTED};"> 📱 {info.get('phone','')}</div></div>""", unsafe_allow_html=True)

        def sec(label):
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px; font-family:'Space Mono',monospace;font-size:10px; letter-spacing:.14em;text-transform:uppercase; color:{C_CYAN};margin:18px 0 10px;"> {label} <div style="flex:1;height:1px; background:linear-gradient(90deg,rgba(0,180,219,.35),transparent);"></div></div>""", unsafe_allow_html=True)

        sec("Demographics")
        age    = st.number_input("Age (Years)", 21, 100, 30, help="Age significantly impacts diabetes risk. Risk generally increases over age 45.")
        gender = st.selectbox("Biological Sex", ["Male","Female"])
        pregnancies = st.number_input("Prior Pregnancies", 0, 20, 0, help="Gestational history can impact insulin resistance long-term.") if gender=="Female" else 0

        sec("Glycemic Markers")
        glucose = st.slider("Fasting Glucose (mg/dL)", 0, 200, 120, help="Normal: <100 mg/dL. Prediabetes: 100-125 mg/dL. Diabetes: ≥126 mg/dL.")
        insulin = st.slider("Serum Insulin (IU/mL)",  0, 900, 80, help="Measures the level of insulin hormone in blood.")

        sec("Cardiovascular")
        bp   = st.slider("Diastolic BP (mmHg)",     0, 130, 70, help="Normal Diastolic: <80 mmHg. Hypertension stage 1: 80-89 mmHg.")
        skin = st.slider("Triceps Skin Fold (mm)",  0, 100, 20, help="Proxy measure for body fat percentage.")

        sec("Biometrics")
        bmi = st.number_input("BMI (kg/m²)", 10.0, 70.0, 25.0, help="Normal: 18.5 - 24.9. Overweight: 25.0 - 29.9. Obese: ≥30.0.")
        dpf = st.slider("Diabetes Pedigree Fn.", 0.0, 2.5, 0.5, help="Function scoring likelihood of diabetes based on family history.")

        st.markdown("<br>", unsafe_allow_html=True)
        predict_btn = st.button("⚡ Generate AI Assessment", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🔒 Secure Logout", use_container_width=True):
            st.session_state.registered   = False
            st.session_state.patient_info = {}
            st.session_state.show_success = False
            st.session_state.model_ran    = False
            st.rerun()

        st.markdown(f"""<div style="margin-top:20px;padding-top:14px; border-top:1px solid rgba(255,255,255,.06); font-family:'Space Mono',monospace;font-size:9px; color:rgba(139,164,200,.4); text-align:center;letter-spacing:.1em;text-transform:uppercase;"> MEDCORE AI · SVM Engine<br>Clinical Intelligence v2.0</div>""", unsafe_allow_html=True)

    # ══ MAIN HEADER ═══════════════════════════════════════════
    st.markdown(f"""
<div class="fadeA" style="text-align:center;padding:28px 0 6px;">
  <div style="display:inline-flex;gap:8px;margin-bottom:16px;">
    <span style="background:rgba(0,180,219,.1);border:1px solid rgba(0,180,219,.28); border-radius:99px;padding:5px 14px;font-family:'Space Mono',monospace; font-size:11px;color:{C_CYAN};letter-spacing:.07em;">🧬 Diagnostic AI Engine</span>
    <span style="background:rgba(21,101,192,.1);border:1px solid rgba(21,101,192,.28); border-radius:99px;padding:5px 14px;font-family:'Space Mono',monospace; font-size:11px;color:#64b5f6;letter-spacing:.07em;">SVM Architecture</span>
  </div>
  <h1 style="font-family:'Outfit',sans-serif!important; font-size:clamp(1.9rem,4vw,3.1rem); font-weight:900;letter-spacing:-.04em; background:linear-gradient(110deg,#ffffff 8%,{C_CYAN} 50%,{C_BLUE} 100%); -webkit-background-clip:text;-webkit-text-fill-color:transparent; background-clip:text;margin-bottom:8px;">Diabetes Risk Intelligence</h1>
  <p style="font-family:'Manrope',sans-serif;color:{C_MUTED}; font-size:.88rem;letter-spacing:.07em;text-transform:uppercase;">Multiparametric Clinical Analysis · Evidence-Based Assessment</p>
</div>
""", unsafe_allow_html=True)

    if st.session_state.show_success:
        st.toast("✅ Registration Successful! Secure clinical session established.", icon="🏥")
        st.session_state.show_success = False

    with st.expander("ℹ️ About This Clinical System", expanded=not st.session_state.model_ran):
        st.markdown(f"""
        <div style="color:{C_MUTED}; font-size:14px; line-height:1.6; padding:10px;">
        This Diabetes Prediction System is an AI-powered medical risk assessment tool utilizing a Support Vector Machine (SVM) algorithm. 
        It evaluates standard clinical biomarkers to map multidimensional physiological inputs into a definitive risk probability.
        Ensure all entered data is accurate for optimal algorithmic performance.
        </div>
        """, unsafe_allow_html=True)

    if predict_btn:
        st.session_state.model_ran = True

    if not st.session_state.model_ran:
        st.markdown(f"""<div class="fadeC" style="background:rgba(10,35,66,.45); border:1px solid rgba(0,180,219,.14); border-radius:18px;padding:60px 28px;text-align:center;"> <div style="width:68px;height:68px; background:linear-gradient(135deg,rgba(0,180,219,.12),rgba(21,101,192,.12)); border:1px solid rgba(0,180,219,.22);border-radius:18px; display:inline-flex;align-items:center;justify-content:center; font-size:34px;margin-bottom:18px;">🧬</div> <h2 style="font-size:1.15rem;color:{C_MUTED}!important; font-weight:600;margin-bottom:8px;">System Awaiting Input</h2> <p style="font-family:'Manrope',sans-serif; color:rgba(139,164,200,.6);font-size:13.5px; max-width:380px;margin:0 auto;"> Configure clinical parameters in the sidebar and click <strong style="color:{C_CYAN};">Generate AI Assessment</strong> to begin.</p></div>""", unsafe_allow_html=True)
        return

    # ══ RUN MODEL (Simulate processing for realism) ═════════════════
    if predict_btn:
        with st.spinner("Executing SVM Clinical Model Algorithm..."):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            progress_bar.empty()

    try:
        if "_id" in info:
            users_col.update_one({"_id":info["_id"]}, {"$set":{"gender":gender}})
    except Exception:
        pass

    inp      = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
    prob     = model.predict_proba(scaler.transform(inp))[0]
    prob_neg = prob[0] * 100
    prob_pos = prob[1] * 100

    if prob_pos < 30:
        risk_label = "Low Risk"; risk_hex = C_GREEN; r_border = "rgba(0,200,150,.35)"; r_bg = "rgba(0,200,150,.07)"; r_icon = "✅"; risk_text = "LOW RISK — Diabetes Unlikely"
    elif prob_pos < 70:
        risk_label = "Moderate Risk"; risk_hex = C_AMBER; r_border = "rgba(245,158,11,.35)"; r_bg = "rgba(245,158,11,.07)"; r_icon = "⚠️"; risk_text = "MODERATE RISK — Possible Diabetes"
    else:
        risk_label = "High Risk"; risk_hex = C_RED; r_border = "rgba(229,57,53,.35)"; r_bg = "rgba(229,57,53,.07)"; r_icon = "🚨"; risk_text = "HIGH RISK — Diabetes Likely"

    ist = pytz.timezone("Asia/Kolkata"); now = datetime.now(ist)
    
    try:
        preds_col.insert_one({
            "patient_id": info["_id"], "patient_name": info["name"],
            "age": age, "gender": gender, "glucose": glucose,
            "blood_pressure": bp, "bmi": bmi,
            "prediction": risk_label, "probability": round(prob_pos, 2),
            "created_at": now.strftime("%d-%m-%Y %H:%M:%S"),
        })
    except Exception:
        pass

    st.markdown(f"""
<div style="background:{r_bg}; border:1.5px solid {r_border}; border-radius:18px;padding:26px 26px; margin-bottom:20px;">
  <div style="display:flex;justify-content:space-between; align-items:flex-start;flex-wrap:wrap;gap:16px;">
    <div>
      <div style="font-family:'Space Mono',monospace;font-size:10px; letter-spacing:.14em;text-transform:uppercase; color:{risk_hex};margin-bottom:8px;"> {r_icon} DIAGNOSTIC OUTPUT · {now.strftime('%d %b %Y %I:%M %p IST')} </div>
      <h1 style="font-family:'Outfit',sans-serif!important; font-size:clamp(1.5rem,3vw,2.3rem); font-weight:900;letter-spacing:-.03em; color:{risk_hex}!important;margin:0 0 8px;"> {risk_text} </h1>
      <p style="font-family:'Manrope',sans-serif;font-size:15px; color:{C_MUTED};margin:0;"> AI Probability Score:&nbsp; <span style="font-family:'Space Mono',monospace;font-size:19px; font-weight:700;color:{risk_hex};">{prob_pos:.1f}%</span> &nbsp;diabetic likelihood </p>
    </div>
    <div style="text-align:right;flex-shrink:0;">
      <div style="font-family:'Space Mono',monospace;font-size:9px; color:rgba(139,164,200,.5);letter-spacing:.08em; text-transform:uppercase;margin-bottom:5px;">Patient ID</div>
      <div style="font-family:'Space Mono',monospace; font-size:13px;color:{risk_hex};">{info.get('_id','')}</div>
      <div style="font-family:'Space Mono',monospace;font-size:9px; color:rgba(139,164,200,.4);margin-top:6px;letter-spacing:.07em;"> MEDCORE AI · SVM ENGINE</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    mc1, mc2 = st.columns(2)
    with mc1: st.metric("Non-Diabetic Probability", f"{prob_neg:.1f}%")
    with mc2: st.metric("Diabetic Probability",     f"{prob_pos:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    c_labels, c_values = [], []
    if glucose >= 126: c_labels.append("Hyperglycemia");   c_values.append(min(glucose/2,100))
    if bmi > 30:       c_labels.append("Obesity (BMI)");   c_values.append(min(bmi*2,100))
    if age > 45:       c_labels.append("Age Factor");      c_values.append(min(age,100))
    if bp > 120:       c_labels.append("Hypertension");    c_values.append(min(bp,100))
    if dpf > 0.5:      c_labels.append("Genetics (DPF)");  c_values.append(min(dpf*100,100))
    if not c_labels:   c_labels, c_values = ["Healthy Indicators"], [100]
    scr_cols = [CHART_PALETTE[i%len(CHART_PALETTE)] for i in range(len(c_labels))]

    st.markdown(f"""<p style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em; text-transform:uppercase;color:{C_MUTED};margin-bottom:6px;"> Prediction Results</p>""", unsafe_allow_html=True)

    gc1, gc2 = st.columns(2)
    with gc1:
        gfig = go.Figure(go.Indicator(
            mode="gauge+number", value=prob_pos,
            number={"suffix":"%","font":{"family":"Space Mono","color":"white","size":26}},
            title={"text":"Risk Level","font":{"color":C_MUTED,"size":13}},
            gauge={
                "axis":      {"range":[0,100],"tickcolor":"rgba(255,255,255,.2)","tickwidth":1},
                "bar":       {"color":risk_hex,"thickness":.22},
                "bgcolor":   "rgba(0,0,0,0)", "borderwidth":0,
                "steps":     [{"range":[0,30],"color":"rgba(0,200,150,.14)"},
                              {"range":[30,70],"color":"rgba(245,158,11,.14)"},
                              {"range":[70,100],"color":"rgba(229,57,53,.14)"}],
                "threshold": {"line":{"color":risk_hex,"width":3},
                              "thickness":.78,"value":prob_pos},
            }
        ))
        gfig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), height=255, margin=dict(l=16,r=16,t=26,b=8))
        st.plotly_chart(gfig, use_container_width=True, config={"responsive":True})

    with gc2:
        pfig = go.Figure(go.Pie(
            labels=c_labels, values=c_values, hole=.55,
            marker=dict(colors=scr_cols, line=dict(color="rgba(0,0,0,.4)",width=2)),
            textfont=dict(family="Space Mono",size=11,color="white"),
            textposition="inside", textinfo="percent+label", showlegend=False,
        ))
        pfig.update_layout(
            title=dict(text="Etiology Breakdown", font=dict(color=C_MUTED,size=13)),
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), height=255, margin=dict(l=6,r=6,t=28,b=6),
        )
        st.plotly_chart(pfig, use_container_width=True, config={"responsive":True})

    st.markdown(f"""<p style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em; text-transform:uppercase;color:{C_MUTED};margin:4px 0 8px;"> 📊 Causes of Diabetes (Risk Contribution Analysis)</p>""", unsafe_allow_html=True)

    bfig = go.Figure(go.Bar(
        x=c_labels, y=c_values,
        text=[f"{v:.1f}" for v in c_values], textposition="auto",
        textfont=dict(family="Space Mono",color="white",size=12),
        marker=dict(color=scr_cols, line=dict(color="rgba(255,255,255,.1)",width=1)),
    ))
    bfig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=C_MUTED, family="Manrope"),
        xaxis=dict(tickfont=dict(color=C_MUTED,size=12), title="Risk Factors", title_font=dict(color=C_MUTED), showline=True, linecolor="rgba(255,255,255,.1)"),
        yaxis=dict(tickfont=dict(color=C_MUTED,size=12), title="Severity Score", title_font=dict(color=C_MUTED), gridcolor="rgba(255,255,255,.05)", zerolinecolor="rgba(255,255,255,.1)"),
        margin=dict(l=16,r=16,t=14,b=16), autosize=True,
    )
    st.plotly_chart(bfig, use_container_width=True, config={"responsive":True})

    st.markdown(f"""<p style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em; text-transform:uppercase;color:{C_MUTED};margin:18px 0 10px;"> 🔬 Risk Factor Analysis</p>""", unsafe_allow_html=True)

    risks, positives = [], []
    if glucose >= 126:          risks.append("🚨 High Fasting Glucose Level (≥126 mg/dL)")
    elif 100 <= glucose < 126:  risks.append("⚠️ Prediabetic Glucose Level (100–125 mg/dL)")
    else:                       positives.append("✅ Normal Glucose Level (<100 mg/dL)")
    if bmi > 30:                risks.append("🚨 High BMI — Obesity Detected")
    elif 18.5 <= bmi <= 24.9:   positives.append("✅ Healthy Baseline BMI (18.5 – 24.9)")
    if age > 45:                risks.append("⚠️ Age above 45 — Elevated Risk Cohort")
    if bp > 120:                risks.append("🚨 Elevated Blood Pressure (>120 mmHg)")
    elif 90 <= bp <= 120:       positives.append("✅ Normal Blood Pressure Metrics")
    if dpf > 0.5:               risks.append("⚠️ Higher Genetic Pedigree Risk (DPF > 0.5)")

    rfc, pfc = st.columns(2)
    with rfc:
        st.markdown(f"**⚠️ Identified Risk Factors**")
        if risks:
            for item in risks:
                st.markdown(f"""<div style="background:rgba(229,57,53,.09); border-left:3px solid {C_RED}; border-radius:0 8px 8px 0; padding:10px 14px;margin-bottom:7px; font-family:'Manrope',sans-serif; font-size:14px;font-weight:600; color:#ef9a9a;">{item}</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f'<p style="font-family:Manrope,sans-serif; font-size:13px;font-style:italic;color:{C_MUTED};">No critical risk vectors detected.</p>', unsafe_allow_html=True)

    with pfc:
        st.markdown(f"**🛡️ Positive Health Indicators**")
        if positives:
            for item in positives:
                st.markdown(f"""<div style="background:rgba(0,200,150,.09); border-left:3px solid {C_GREEN}; border-radius:0 8px 8px 0; padding:10px 14px;margin-bottom:7px; font-family:'Manrope',sans-serif; font-size:14px;font-weight:600; color:#80cbc4;">{item}</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f'<p style="font-family:Manrope,sans-serif; font-size:13px;font-style:italic;color:{C_MUTED};">No protective factors highlighted.</p>', unsafe_allow_html=True)

    st.markdown(f"""<p style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em; text-transform:uppercase;color:{C_MUTED};margin:20px 0 10px;"> 💊 Medical Recommendations</p>""", unsafe_allow_html=True)

    if prob_pos >= 70:
        st.error("- Consult a healthcare professional or endocrinologist immediately\n- Get complete HbA1c diabetes screening\n- Monitor blood sugar routinely\n- Institute strict diet and physical activity protocols")
        recs_pdf = ["Consult an endocrinologist immediately", "Acquire complete HbA1c screening", "Monitor blood sugar routinely", "Institute strict dietary protocols"]
    elif prob_pos >= 30:
        st.warning("- Maintain healthy, low-glycemic index diet\n- Increase cardiovascular physical activity\n- Monitor fasting glucose periodically")
        recs_pdf = ["Maintain a low-glycemic index diet", "Increase cardiovascular activity", "Monitor fasting glucose periodically"]
    else:
        st.success("- Continue healthy lifestyle and baseline BMI\n- Exercise regularly (150 mins/week)\n- Maintain routine annual health check-ups")
        recs_pdf = ["Continue healthy lifestyle habits", "Exercise regularly (150 mins/week)", "Maintain routine annual check-ups"]

    # ══ ENTERPRISE PDF GENERATION ══════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)

    bar_png = _bar_png(c_labels, c_values)
    pie_png = _pie_png(c_labels, c_values)

    buf  = BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=letter,
                              rightMargin=40, leftMargin=40,
                              topMargin=100, bottomMargin=70) # Increased margins for realistic header/footer
    els  = []
    sty  = getSampleStyleSheet()

    T = lambda name, **kw: ParagraphStyle(name, parent=sty["Normal"], **kw)
    t_title = T("TT", fontName="Helvetica-Bold", fontSize=18, textColor=colors.HexColor("#0a1a3a"), alignment=1, spaceAfter=4)
    t_date  = T("TD", fontName="Helvetica-Oblique", fontSize=10, textColor=colors.HexColor("#5a6a8a"), alignment=1, spaceAfter=20)
    t_head  = T("TH", fontName="Helvetica-Bold", fontSize=12, textColor=colors.HexColor("#ffffff"), backColor=colors.HexColor("#0d3060"), spaceBefore=14, spaceAfter=8, borderPadding=6)
    t_norm  = T("TN", fontSize=10, spaceAfter=5, textColor=colors.HexColor("#1a2340"))
    t_addr  = T("TA", fontSize=10, leading=14, textColor=colors.HexColor("#1a2340"))

    def hosp_table(rows):
        t = Table(rows, colWidths=[2.2*inch, 4.3*inch])
        t.setStyle(TableStyle([
            ("GRID",        (0,0),(-1,-1), 0.5, colors.HexColor("#e0e6ed")),
            ("BACKGROUND",  (0,0),(0,-1),  colors.HexColor("#f0f4f8")),
            ("FONTNAME",    (0,0),(0,-1),  "Helvetica-Bold"),
            ("TEXTCOLOR",   (0,0),(0,-1),  colors.HexColor("#0a1a3a")),
            ("TEXTCOLOR",   (1,0),(1,-1),  colors.HexColor("#1a2340")),
            ("PADDING",     (0,0),(-1,-1), 8),
            ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
        ]))
        
        # Apply alternating row colors for realism
        for i in range(1, len(rows)):
            if i % 2 == 0:
                t.setStyle(TableStyle([("BACKGROUND", (1, i), (1, i), colors.HexColor("#f8fafc"))]))
        return t

    els.append(Paragraph("CLINICAL DIABETES RISK ASSESSMENT REPORT", t_title))
    els.append(Paragraph(f"Generated: {now.strftime('%d %b %Y | %I:%M %p (IST)')}", t_date))

    els.append(Paragraph("PATIENT DEMOGRAPHICS", t_head))
    els.append(hosp_table([
        ["Patient ID",   Paragraph(f"<font name='Courier-Bold'>{info.get('_id','N/A')}</font>", t_norm)],
        ["Full Name",    info.get("name","N/A").upper()],
        ["Email",        info.get("email","N/A")],
        ["Phone",        info.get("phone","N/A")],
        ["Country",      info.get("country","N/A")],
        ["Address",      Paragraph(info.get("address","N/A"), t_addr)],
    ]))
    els.append(Spacer(1, .16*inch))

    med = [
        ["Age",                 f"{age} Years"],
        ["Biological Sex",      gender],
        ["Fasting Glucose",     f"{glucose} mg/dL"],
        ["Diastolic BP",        f"{bp} mmHg"],
        ["Skin Thickness",      f"{skin} mm"],
        ["Serum Insulin",       f"{insulin} IU/mL"],
        ["Body Mass Index",     str(bmi)],
        ["Diabetes Pedigree",   str(dpf)],
    ]
    if gender == "Female":
        med.insert(2, ["Prior Pregnancies", str(pregnancies)])
    els.append(Paragraph("CLINICAL BIOMARKERS", t_head))
    els.append(hosp_table(med))
    els.append(Spacer(1, .22*inch))

    risk_pdf_col = {"Low Risk":"#007a5e","Moderate Risk":"#b45309","High Risk":"#b91c1c"}
    risk_pdf_lbl = {"Low Risk":"LOW RISK — Diabetes Unlikely", "Moderate Risk":"MODERATE RISK — Possible Diabetes", "High Risk":"HIGH RISK — Diabetes Likely"}
    
    els.append(Paragraph("DIAGNOSTIC ALGORITHM OUTPUT", t_head))
    els.append(Paragraph(f"<b>Overall Clinical Risk Level:</b>  <font color='{risk_pdf_col[risk_label]}'><b>{risk_pdf_lbl[risk_label]}</b></font>", t_norm))
    els.append(Paragraph(f"<b>AI Probability Index:</b>  {prob_pos:.1f}% positive likelihood", t_norm))
    els.append(Spacer(1, .16*inch))

    els.append(Paragraph("DATA VISUALIZATION & ETIOLOGY", t_head))
    chart_row = Table([[RLImage(BytesIO(bar_png), 3.3*inch, 2.2*inch), RLImage(BytesIO(pie_png), 3.3*inch, 2.2*inch)]], colWidths=[3.45*inch, 3.45*inch])
    chart_row.setStyle(TableStyle([
        ("ALIGN",         (0,0),(-1,-1), "CENTER"), ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("BOX",           (0,0),(-1,-1), 0.5, colors.HexColor("#c8d4f0")), ("INNERGRID",     (0,0),(-1,-1), .5, colors.HexColor("#dde8f8")),
        ("TOPPADDING",    (0,0),(-1,-1), 8), ("BOTTOMPADDING", (0,0),(-1,-1), 8), ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#f4f8ff")),
    ]))
    els.append(chart_row)
    els.append(Spacer(1, .16*inch))

    els.append(Paragraph("RECOMMENDATIONS", t_head))
    els.append(ListFlowable([ListItem(Paragraph(r, t_norm)) for r in recs_pdf], bulletType="bullet"))
    els.append(Spacer(1, .4*inch))
    
    # Official Signature Block
    sig_data = [
        ["", "___________________________________"],
        ["", "Authorized Medical Practitioner"],
        ["", "MedCore AI Clinical Systems Board"]
    ]
    sig_table = Table(sig_data, colWidths=[3.5*inch, 3*inch])
    sig_table.setStyle([
        ("ALIGN", (1,0), (1,-1), "CENTER"),
        ("FONTNAME", (1,1), (1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (1,1), (1,-1), 9),
        ("TEXTCOLOR", (1,1), (1,-1), colors.HexColor("#0a1a3a")),
    ])
    els.append(sig_table)
    
    els.append(Spacer(1, .3*inch))
    els.append(Paragraph("<b>Medical Disclaimer:</b> This report was generated autonomously by MEDCORE AI SVM Systems. It is intended for preliminary screening and does not replace certified clinical diagnosis. Always consult a licensed physician.", T("DI", fontName="Helvetica-Oblique", fontSize=8, textColor=colors.HexColor("#7a8a9a"))))

    # Build PDF with Header/Footer callback
    doc.build(els, onFirstPage=report_header_footer, onLaterPages=report_header_footer)
    pdf_data = buf.getvalue(); buf.close()

    st.download_button(
        label="📄 Download Official Medical Report (PDF)",
        data=pdf_data,
        file_name=f"Clinical_Report_{info.get('name','Patient').replace(' ','_')}_{now.strftime('%d%m%Y')}.pdf",
        mime="application/pdf",
    )

    st.markdown("---")
    st.warning("⚠️ Medical Disclaimer: This tool evaluates statistical biomarker risks. It does NOT replace professional medical diagnosis.")


# ═════════════════════════════════════════════════════════════
#  NAVIGATION
# ═════════════════════════════════════════════════════════════
if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
