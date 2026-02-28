# -----------------------------
# Import Required Libraries
# -----------------------------
import streamlit as st
import numpy as np
import joblib
import plotly.graph_objects as go
import base64
import re
import pycountry
import phonenumbers
import time

def get_base64_image(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def country_to_flag(country_code):
    return "".join(chr(127397 + ord(char)) for char in country_code.upper())

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from io import BytesIO

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import uuid
import pytz

uri = "mongodb+srv://diabetes_user:Diabetes%40123@diabetescluster.oxegep6.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["diabetes_app"]
users_collection = db["registered_users"]
predictions_collection = db["predictions"]

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="MedAI Diabetes Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.write("App Loaded Successfully")

# -----------------------------
# Session State
# -----------------------------
if "registered" not in st.session_state:
    st.session_state.registered = False
if "patient_info" not in st.session_state:
    st.session_state.patient_info = {}
if "show_success" not in st.session_state:
    st.session_state.show_success = False

# =====================================================
# MASTER CSS INJECTION
# =====================================================
def inject_master_css(img_b64, page="prediction"):
    overlay = "rgba(4, 8, 20, 0.82)" if page == "prediction" else "rgba(6, 12, 28, 0.78)"
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {{
        --primary: #00d4ff;
        --primary-dim: rgba(0, 212, 255, 0.15);
        --accent: #7c3aed;
        --accent-dim: rgba(124, 58, 237, 0.15);
        --success: #00e5a0;
        --warning: #ffb800;
        --danger: #ff4757;
        --surface: rgba(255, 255, 255, 0.04);
        --surface-hover: rgba(255, 255, 255, 0.08);
        --border: rgba(255, 255, 255, 0.08);
        --border-bright: rgba(0, 212, 255, 0.3);
        --text-primary: #f0f4ff;
        --text-secondary: #8892b0;
        --text-dim: #4a5568;
        --card-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        --glow-blue: 0 0 30px rgba(0, 212, 255, 0.15);
        --glow-purple: 0 0 30px rgba(124, 58, 237, 0.15);
    }}

    /* ============ GLOBAL RESET ============ */
    * {{ box-sizing: border-box; }}

    .stApp {{
        background: linear-gradient({overlay}, {overlay}),
                    url("data:image/png;base64,{img_b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'DM Sans', sans-serif;
        color: var(--text-primary);
        min-height: 100vh;
    }}

    /* Hide Streamlit chrome */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}

    /* ============ TYPOGRAPHY ============ */
    h1, h2, h3, h4, h5 {{
        font-family: 'Syne', sans-serif !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em;
    }}

    /* ============ GLASS CARD SYSTEM ============ */
    .glass-card {{
        background: var(--surface);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 28px;
        box-shadow: var(--card-shadow);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    .glass-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0,212,255,0.4), transparent);
    }}
    .glass-card:hover {{
        background: var(--surface-hover);
        border-color: rgba(0, 212, 255, 0.2);
        box-shadow: var(--card-shadow), var(--glow-blue);
        transform: translateY(-2px);
    }}

    /* ============ HERO TITLE ============ */
    .hero-title {{
        font-family: 'Syne', sans-serif;
        font-size: clamp(2.2rem, 4vw, 3.5rem);
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #00d4ff 50%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        line-height: 1.1;
        letter-spacing: -0.04em;
        margin-bottom: 6px;
    }}
    .hero-sub {{
        font-family: 'DM Sans', sans-serif;
        font-size: 1rem;
        color: var(--text-secondary);
        text-align: center;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 40px;
    }}

    /* ============ SIDEBAR ============ */
    section[data-testid="stSidebar"] {{
        background: rgba(4, 8, 20, 0.85) !important;
        backdrop-filter: blur(30px) !important;
        -webkit-backdrop-filter: blur(30px) !important;
        border-right: 1px solid var(--border) !important;
        box-shadow: 4px 0 40px rgba(0,0,0,0.5) !important;
    }}
    section[data-testid="stSidebar"] > div {{
        padding-top: 20px !important;
    }}
    section[data-testid="stSidebar"] label {{
        color: var(--text-secondary) !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
    }}
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: var(--text-primary) !important;
    }}
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {{
        color: var(--text-secondary) !important;
    }}

    /* Sidebar Inputs - Clean White Style */
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background: #f8fafc !important;
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        color: #0f172a !important;
        transition: all 0.25s ease;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {{
        border-color: #00d4ff !important;
        box-shadow: 0 0 0 3px rgba(0,212,255,0.2) !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="input"] input {{
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 600 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 14px !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="select"] span {{
        color: #0f172a !important;
        font-weight: 600 !important;
    }}

    /* Slider Track */
    div[data-baseweb="slider"] [data-testid="stTickBar"] {{ display: none; }}
    div[data-testid="stSlider"] > label {{
        color: var(--text-secondary) !important;
        font-size: 11px !important;
    }}

    /* Hide number spinners */
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {{ -webkit-appearance: none; margin: 0; }}
    input[type="number"] {{ -moz-appearance: textfield; }}

    /* ============ BUTTONS ============ */
    section[data-testid="stSidebar"] button,
    div[data-testid="stForm"] button {{
        background: linear-gradient(135deg, #00d4ff, #7c3aed) !important;
        border: none !important;
        color: white !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        letter-spacing: 0.05em !important;
        border-radius: 12px !important;
        padding: 12px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        text-transform: uppercase !important;
    }}
    section[data-testid="stSidebar"] button:hover,
    div[data-testid="stForm"] button:hover {{
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 30px rgba(0, 212, 255, 0.4) !important;
    }}

    /* Download Button */
    div.stDownloadButton > button {{
        background: linear-gradient(135deg, #00e5a0, #00a86b) !important;
        color: #001a0a !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        border-radius: 14px !important;
        padding: 14px 28px !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(0, 229, 160, 0.3) !important;
        letter-spacing: 0.03em !important;
        text-transform: none !important;
        width: 100% !important;
    }}
    div.stDownloadButton > button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 40px rgba(0, 229, 160, 0.5) !important;
    }}

    /* ============ METRICS ============ */
    div[data-testid="metric-container"] {{
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        padding: 20px !important;
    }}
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.8rem !important;
        color: var(--primary) !important;
    }}
    div[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
        color: var(--text-secondary) !important;
        font-size: 11px !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }}

    /* ============ STREAMLIT ALERTS ============ */
    div[data-testid="stSuccess"] {{
        background: rgba(0, 229, 160, 0.1) !important;
        border: 1px solid rgba(0, 229, 160, 0.3) !important;
        border-radius: 12px !important;
        color: #00e5a0 !important;
    }}
    div[data-testid="stWarning"] {{
        background: rgba(255, 184, 0, 0.1) !important;
        border: 1px solid rgba(255, 184, 0, 0.3) !important;
        border-radius: 12px !important;
        color: #ffb800 !important;
    }}
    div[data-testid="stError"] {{
        background: rgba(255, 71, 87, 0.1) !important;
        border: 1px solid rgba(255, 71, 87, 0.3) !important;
        border-radius: 12px !important;
        color: #ff4757 !important;
    }}

    /* ============ CUSTOM BADGE SYSTEM ============ */
    .risk-badge {{
        background: rgba(255, 71, 87, 0.08);
        border: 1px solid rgba(255, 71, 87, 0.25);
        border-left: 3px solid #ff4757;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-size: 14px;
        color: #ffa0aa;
        font-family: 'DM Sans', sans-serif;
        letter-spacing: 0.01em;
    }}
    .safe-badge {{
        background: rgba(0, 229, 160, 0.08);
        border: 1px solid rgba(0, 229, 160, 0.25);
        border-left: 3px solid #00e5a0;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-size: 14px;
        color: #80f7cf;
        font-family: 'DM Sans', sans-serif;
        letter-spacing: 0.01em;
    }}

    /* ============ STAT PILL ============ */
    .stat-pill {{
        display: inline-block;
        background: var(--primary-dim);
        border: 1px solid var(--border-bright);
        border-radius: 100px;
        padding: 4px 14px;
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
        color: var(--primary);
        letter-spacing: 0.05em;
        margin: 3px;
    }}

    /* ============ SECTION DIVIDER ============ */
    .section-label {{
        font-family: 'Syne', sans-serif;
        font-size: 11px;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--primary);
        margin-bottom: 6px;
        margin-top: 24px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .section-label::after {{
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, var(--border-bright), transparent);
    }}

    /* ============ RESULT BANNER ============ */
    .result-low {{
        background: linear-gradient(135deg, rgba(0,229,160,0.12), rgba(0,229,160,0.03));
        border: 1px solid rgba(0,229,160,0.3);
        border-radius: 20px;
        padding: 32px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }}
    .result-moderate {{
        background: linear-gradient(135deg, rgba(255,184,0,0.12), rgba(255,184,0,0.03));
        border: 1px solid rgba(255,184,0,0.3);
        border-radius: 20px;
        padding: 32px;
        margin-bottom: 24px;
    }}
    .result-high {{
        background: linear-gradient(135deg, rgba(255,71,87,0.12), rgba(255,71,87,0.03));
        border: 1px solid rgba(255,71,87,0.3);
        border-radius: 20px;
        padding: 32px;
        margin-bottom: 24px;
    }}

    /* ============ REGISTRATION PAGE FORM ============ */
    div[data-testid="stForm"] {{
        background: rgba(4, 8, 20, 0.75);
        backdrop-filter: blur(30px);
        -webkit-backdrop-filter: blur(30px);
        border-radius: 28px;
        padding: 48px 44px;
        max-width: 580px;
        margin: 4vh auto;
        border: 1px solid rgba(0, 212, 255, 0.15);
        box-shadow: 0 30px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05);
    }}
    div[data-testid="stForm"]::before {{
        content: '';
        position: absolute;
        top: 0; left: 20%; right: 20%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0,212,255,0.5), transparent);
    }}
    div[data-testid="stForm"] label {{
        color: var(--text-secondary) !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
    }}
    div[data-testid="stForm"] div[data-baseweb="input"] > div,
    div[data-testid="stForm"] div[data-baseweb="textarea"] > div {{
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }}
    div[data-testid="stForm"] div[data-baseweb="input"] > div:focus-within,
    div[data-testid="stForm"] div[data-baseweb="textarea"] > div:focus-within {{
        border-color: rgba(0, 212, 255, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1), 0 0 20px rgba(0, 212, 255, 0.15) !important;
        background: rgba(255,255,255,0.1) !important;
    }}
    div[data-testid="stForm"] input,
    div[data-testid="stForm"] textarea {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 15px !important;
        font-weight: 500 !important;
    }}
    div[data-testid="stForm"] input::placeholder,
    div[data-testid="stForm"] textarea::placeholder {{
        color: var(--text-dim) !important;
    }}
    div[data-testid="stForm"] div[data-baseweb="select"] > div {{
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 12px !important;
    }}
    div[data-testid="stForm"] div[data-baseweb="select"] span {{
        color: #ffffff !important;
        font-weight: 500 !important;
    }}

    /* Dropdown popup */
    div[data-baseweb="popover"] {{
        background: #0d1224 !important;
        border: 1px solid rgba(0,212,255,0.2);
        border-radius: 12px;
    }}
    ul[role="listbox"] {{ background: #0d1224 !important; }}
    li[role="option"] {{ color: var(--text-secondary) !important; font-weight: 500 !important; }}
    li[role="option"]:hover {{ background: var(--primary-dim) !important; color: var(--primary) !important; }}

    /* Mobile responsive */
    @media (max-width: 768px) {{
        div[data-testid="stForm"] {{ padding: 28px 20px !important; margin-top: 20px !important; }}
        .hero-title {{ font-size: 1.8rem !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)


# =====================================================
# REGISTRATION PAGE
# =====================================================
def registration_page():
    img = get_base64_image("health.png")
    inject_master_css(img, page="registration")

    # Animated background glow orbs
    st.markdown("""
    <style>
    .orb1 {
        position: fixed; top: 10%; left: 10%; width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(0,212,255,0.08) 0%, transparent 70%);
        border-radius: 50%; pointer-events: none; animation: float1 8s ease-in-out infinite;
    }
    .orb2 {
        position: fixed; bottom: 15%; right: 10%; width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(124,58,237,0.08) 0%, transparent 70%);
        border-radius: 50%; pointer-events: none; animation: float2 10s ease-in-out infinite;
    }
    @keyframes float1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(20px,-20px)} }
    @keyframes float2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-15px,15px)} }
    </style>
    <div class="orb1"></div>
    <div class="orb2"></div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; padding: 40px 0 10px;">
        <div style="display:inline-flex; align-items:center; gap:12px; background:rgba(0,212,255,0.08); border:1px solid rgba(0,212,255,0.2); border-radius:100px; padding:8px 20px; margin-bottom:24px;">
            <span style="color:#00d4ff; font-size:12px; font-family:'DM Sans',sans-serif; letter-spacing:0.1em; text-transform:uppercase; font-weight:600;">🧬 AI-Powered Clinical System</span>
        </div>
        <h1 class="hero-title">MedAI Diabetes<br>Intelligence</h1>
        <p class="hero-sub">Precision Risk Assessment · Multiparametric Analysis · Clinical Grade</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("registration_form"):
            st.markdown("""
            <div style="text-align:center; margin-bottom:28px;">
                <div style="font-size:36px; margin-bottom:8px;">🏥</div>
                <h3 style="margin:0; font-family:'Syne',sans-serif; font-size:1.3rem; color:#ffffff;">Patient Registration</h3>
                <p style="color:#8892b0; font-size:13px; margin-top:4px;">Secure · Encrypted · HIPAA-Compliant</p>
            </div>
            """, unsafe_allow_html=True)

            name = st.text_input("Full Name", placeholder="Enter full legal name")

            country_list = [country.name for country in pycountry.countries]
            selected_country = st.selectbox("Country of Residence", country_list)

            country_obj = pycountry.countries.get(name=selected_country)
            country_code = phonenumbers.country_code_for_region(country_obj.alpha_2)

            phone = st.text_input("Mobile Number", placeholder="Without country code")
            email = st.text_input("Email Address", placeholder="your@email.com")
            address = st.text_area("Residential Address", placeholder="Street, City, State, ZIP")

            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("▶ Register & Access System", use_container_width=True)

            if submit:
                name = name.strip()
                phone = phone.strip()
                email = email.strip()
                address = address.strip()

                if not name or not phone or not email or not address:
                    st.error("❌ Please fill all fields properly")
                    return

                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(email_pattern, email):
                    st.error("❌ Please enter a valid email address")
                    return

                region_code = country_obj.alpha_2
                try:
                    parsed_number = phonenumbers.parse(phone, region_code)
                    if not phonenumbers.is_valid_number(parsed_number):
                        st.error("❌ Invalid phone number for selected country")
                        return
                    formatted_phone = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
                except:
                    st.error("❌ Invalid phone number format")
                    return

                ist = pytz.timezone("Asia/Kolkata")
                current_time = datetime.now(ist)
                patient_id = "PAT" + str(uuid.uuid4().int)[:6]

                user_data = {
                    "_id": patient_id, "name": name, "phone": formatted_phone,
                    "country": selected_country, "email": email, "address": address,
                    "gender": "Not Selected",
                    "created_at": current_time.strftime("%d-%m-%Y %I:%M:%S %p")
                }

                users_collection.insert_one(user_data)
                st.session_state.patient_info = user_data
                st.session_state.registered = True
                st.session_state.show_success = True
                st.success("Registered Successfully")
                st.rerun()

    # Bottom trust indicators
    st.markdown("""
    <div style="display:flex; justify-content:center; gap:30px; margin-top:30px; flex-wrap:wrap;">
        <span class="stat-pill">🔒 256-bit SSL</span>
        <span class="stat-pill">🏥 Clinical Grade AI</span>
        <span class="stat-pill">⚡ Real-time Analysis</span>
        <span class="stat-pill">📊 MongoDB Secured</span>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# MAIN PREDICTION PAGE
# =====================================================
@st.cache_resource
def load_model():
    try:
        model = joblib.load("diabetes_model.pkl")
        scaler = joblib.load("scaler_svm.pkl")
        return model, scaler
    except Exception as e:
        st.error(f"⚠️ Model Loading Error: {e}")
        st.stop()

def prediction_page():
    model, scaler = load_model()

    if not st.session_state.patient_info:
        st.session_state.registered = False
        st.stop()

    img = get_base64_image("health22.png")
    inject_master_css(img, page="prediction")
    info = st.session_state.patient_info

    # ============ SIDEBAR ============
    with st.sidebar:
        # Patient Header
        st.markdown(f"""
        <div style="padding:20px 0 16px; border-bottom:1px solid rgba(0,212,255,0.15); margin-bottom:16px;">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:10px;">
                <div style="width:42px; height:42px; background:linear-gradient(135deg,#00d4ff,#7c3aed); border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:20px; flex-shrink:0;">🩺</div>
                <div>
                    <div style="font-family:'Syne',sans-serif; font-weight:700; font-size:15px; color:#f0f4ff;">{info.get('name','')}</div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:10px; color:#00d4ff; letter-spacing:0.05em;">{info.get('_id','')}</div>
                </div>
            </div>
            <div style="font-size:12px; color:#8892b0;">{info.get('email','')}</div>
            <div style="font-size:12px; color:#8892b0;">{info.get('phone','')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-label">Demographics</div>', unsafe_allow_html=True)
        age = st.number_input("Age (Years)", 21, 100, 30)
        gender = st.selectbox("Biological Sex", ["Male", "Female"])
        if gender == "Female":
            pregnancies = st.number_input("Prior Pregnancies", min_value=0, max_value=20, value=0)
        else:
            pregnancies = 0

        st.markdown('<div class="section-label">Glycemic Markers</div>', unsafe_allow_html=True)
        glucose = st.slider("Fasting Glucose (mg/dL)", 0, 200, 120)
        insulin = st.slider("Serum Insulin (IU/mL)", 0, 900, 80)

        st.markdown('<div class="section-label">Cardiovascular</div>', unsafe_allow_html=True)
        bp = st.slider("Diastolic BP (mmHg)", 0, 130, 70)
        skin = st.slider("Triceps Skin Fold (mm)", 0, 100, 20)

        st.markdown('<div class="section-label">Biometrics</div>', unsafe_allow_html=True)
        bmi = st.number_input("BMI (kg/m²)", 10.0, 70.0, 25.0)
        dpf = st.slider("Diabetes Pedigree Function", 0.0, 2.5, 0.5)

        st.markdown("<br>", unsafe_allow_html=True)
        predict_btn = st.button("⚡ Generate Assessment", use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state.registered = False
            st.session_state.patient_info = {}
            st.session_state.show_success = False
            st.rerun()

    # ============ MAIN AREA HEADER ============
    st.markdown("""
    <div style="text-align:center; padding:30px 0 10px;">
        <div style="display:inline-flex; align-items:center; gap:10px; background:rgba(0,212,255,0.08); border:1px solid rgba(0,212,255,0.2); border-radius:100px; padding:6px 18px; margin-bottom:20px;">
            <span style="color:#00d4ff; font-size:11px; font-family:'DM Sans',sans-serif; letter-spacing:0.1em; text-transform:uppercase; font-weight:600;">🧬 Diagnostic AI Engine · SVM Architecture</span>
        </div>
        <h1 class="hero-title">Diabetes Risk<br>Intelligence</h1>
        <p class="hero-sub">Multiparametric Analysis · Evidence-Based Assessment · Clinical Grade</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.show_success:
        st.success("✅ Registration Successful! Secure session established.")
        st.session_state.show_success = False

    # About section
    if not predict_btn:
        st.markdown("""
        <div class="glass-card" style="margin-bottom:30px;">
            <div style="display:flex; align-items:flex-start; gap:20px;">
                <div style="font-size:48px; flex-shrink:0;">📋</div>
                <div>
                    <h3 style="margin:0 0 8px; font-size:1.2rem;">About This System</h3>
                    <p style="color:#8892b0; line-height:1.7; margin:0; font-size:15px;">
                        This Diabetes Prediction System is an AI-powered medical risk assessment tool designed to estimate the likelihood of diabetes based on key health parameters such as glucose level, BMI, blood pressure, age, and family history.
                    </p>
                </div>
            </div>
        </div>

        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px,1fr)); gap:16px; margin-bottom:30px;">
            <div class="glass-card" style="text-align:center; padding:24px 16px;">
                <div style="font-size:32px; margin-bottom:8px;">🤖</div>
                <div style="font-family:'Syne',sans-serif; font-weight:700; color:#00d4ff; font-size:14px;">SVM Algorithm</div>
                <div style="font-size:12px; color:#8892b0; margin-top:4px;">Support Vector Machine</div>
            </div>
            <div class="glass-card" style="text-align:center; padding:24px 16px;">
                <div style="font-size:32px; margin-bottom:8px;">📊</div>
                <div style="font-family:'Syne',sans-serif; font-weight:700; color:#7c3aed; font-size:14px;">8 Parameters</div>
                <div style="font-size:12px; color:#8892b0; margin-top:4px;">Clinical Biomarkers</div>
            </div>
            <div class="glass-card" style="text-align:center; padding:24px 16px;">
                <div style="font-size:32px; margin-bottom:8px;">⚡</div>
                <div style="font-family:'Syne',sans-serif; font-weight:700; color:#00e5a0; font-size:14px;">Real-Time</div>
                <div style="font-size:12px; color:#8892b0; margin-top:4px;">Instant Analysis</div>
            </div>
            <div class="glass-card" style="text-align:center; padding:24px 16px;">
                <div style="font-size:32px; margin-bottom:8px;">🔒</div>
                <div style="font-family:'Syne',sans-serif; font-weight:700; color:#ffb800; font-size:14px;">Secure DB</div>
                <div style="font-size:12px; color:#8892b0; margin-top:4px;">MongoDB Atlas</div>
            </div>
        </div>

        <div class="glass-card" style="text-align:center; padding:60px 20px;">
            <div style="font-size:64px; margin-bottom:16px; opacity:0.6;">🧬</div>
            <h2 style="margin:0 0 10px; color:#8892b0; font-size:1.2rem; font-weight:500;">System Ready</h2>
            <p style="color:#4a5568; margin:0; font-size:14px;">Configure clinical parameters in the sidebar panel and initiate AI assessment</p>
        </div>
        """, unsafe_allow_html=True)

    # ============ PREDICTION LOGIC ============
    if predict_btn:
        if "_id" in info:
            users_collection.update_one({"_id": info["_id"]}, {"$set": {"gender": gender}})

        input_data = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
        input_std = scaler.transform(input_data)
        prediction = model.predict(input_std)[0]
        probability = model.predict_proba(input_std)[0]

        prob_negative = probability[0] * 100
        prob_positive = probability[1] * 100

        if prob_positive < 30:
            risk_label = "Low Risk"
            risk_display = "LOW RISK — Diabetes Unlikely"
            risk_class = "result-low"
            risk_hex = "#00e5a0"
            risk_icon = "✅"
        elif prob_positive < 70:
            risk_label = "Moderate Risk"
            risk_display = "MODERATE RISK — Possible Diabetes"
            risk_class = "result-moderate"
            risk_hex = "#ffb800"
            risk_icon = "⚠️"
        else:
            risk_label = "High Risk"
            risk_display = "HIGH RISK — Diabetes Likely"
            risk_class = "result-high"
            risk_hex = "#ff4757"
            risk_icon = "❌"

        # Save to MongoDB
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        prediction_data = {
            "patient_id": info["_id"], "patient_name": info["name"], "age": age,
            "gender": gender, "glucose": glucose, "blood_pressure": bp, "bmi": bmi,
            "prediction": risk_label, "probability": round(prob_positive, 2),
            "created_at": current_time.strftime("%d-%m-%Y %H:%M:%S")
        }
        predictions_collection.insert_one(prediction_data)

        # ---- RESULT BANNER ----
        st.markdown(f"""
        <div class="{risk_class}">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
                <div>
                    <div style="font-size:11px; letter-spacing:0.15em; text-transform:uppercase; color:{risk_hex}; font-family:'DM Sans',sans-serif; font-weight:600; margin-bottom:8px;">
                        {risk_icon} DIAGNOSTIC OUTPUT
                    </div>
                    <h1 style="font-family:'Syne',sans-serif; font-size:clamp(1.5rem,3vw,2.5rem); font-weight:800; margin:0 0 8px; color:{risk_hex};">{risk_display}</h1>
                    <p style="margin:0; color:#8892b0; font-size:15px;">
                        Computed AI Probability: <span style="font-family:'JetBrains Mono',monospace; color:{risk_hex}; font-size:18px; font-weight:700;">{prob_positive:.1f}%</span> diabetic
                    </p>
                </div>
                <div style="text-align:right;">
                    <div style="font-family:'JetBrains Mono',monospace; font-size:11px; color:#8892b0;">{current_time.strftime('%d %b %Y · %I:%M %p IST')}</div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:11px; color:#8892b0; margin-top:4px;">ID: {info.get('_id','')}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---- PROBABILITY METRICS ----
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Non-Diabetic Probability", f"{prob_negative:.1f}%")
        with col2:
            st.metric("Diabetic Probability", f"{prob_positive:.1f}%")

        # ---- CHARTS ROW ----
        st.markdown("<br>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns([1, 1])

        cause_labels, cause_values = [], []
        if glucose >= 126:
            cause_labels.append("Hyperglycemia")
            cause_values.append(min(glucose / 2, 100))
        if bmi > 30:
            cause_labels.append("Obesity (BMI)")
            cause_values.append(min(bmi * 2, 100))
        if age > 45:
            cause_labels.append("Age Factor")
            cause_values.append(min(age, 100))
        if bp > 120:
            cause_labels.append("Hypertension")
            cause_values.append(min(bp, 100))
        if dpf > 0.5:
            cause_labels.append("Genetics (DPF)")
            cause_values.append(min(dpf * 100, 100))
        if not cause_labels:
            cause_labels = ["Healthy Indicators"]
            cause_values = [100]

        with col_g1:
            gauge_fig = go.Figure(go.Indicator(
                mode="gauge+number", value=prob_positive,
                number={"suffix": "%", "font": {"color": "white", "family": "JetBrains Mono"}},
                title={"text": "Risk Level", "font": {"color": "#8892b0", "size": 14}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "rgba(255,255,255,0.3)"},
                    "bar": {"color": risk_hex, "thickness": 0.25},
                    "bgcolor": "rgba(0,0,0,0)",
                    "bordercolor": "rgba(0,0,0,0)",
                    "steps": [
                        {"range": [0, 30], "color": "rgba(0,229,160,0.15)"},
                        {"range": [30, 70], "color": "rgba(255,184,0,0.15)"},
                        {"range": [70, 100], "color": "rgba(255,71,87,0.15)"}
                    ],
                    "threshold": {"line": {"color": risk_hex, "width": 4}, "thickness": 0.75, "value": prob_positive}
                }
            ))
            gauge_fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
                height=260, margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(gauge_fig, use_container_width=True, config={"responsive": True})

        with col_g2:
            pie_colors = ['#ff4757', '#ffb800', '#00e5a0', '#00d4ff', '#7c3aed']
            pie_fig = go.Figure(data=[go.Pie(
                labels=cause_labels, values=cause_values, hole=0.55,
                marker_colors=pie_colors[:len(cause_labels)],
                textfont=dict(family="DM Sans", size=12, color="white"),
                textposition='inside', textinfo='percent+label'
            )])
            pie_fig.update_layout(
                title=dict(text="Risk Contribution", font=dict(color="#8892b0", size=14)),
                paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
                height=260, margin=dict(l=20, r=20, t=40, b=20), showlegend=False
            )
            st.plotly_chart(pie_fig, use_container_width=True, config={"responsive": True})

        # ---- BAR CHART ----
        st.markdown('<h2 style="font-size:1.1rem; margin:4px 0 16px; color:#8892b0; font-weight:500; letter-spacing:0.05em; text-transform:uppercase;">📊 Causes of Diabetes (Risk Contribution Analysis)</h2>', unsafe_allow_html=True)
        
        bar_fig = go.Figure(go.Bar(
            x=cause_labels, y=cause_values,
            text=[f"{v:.1f}" for v in cause_values], textposition='auto',
            marker=dict(
                color=cause_values, colorscale=[
                    [0, "rgba(0,229,160,0.8)"], [0.4, "rgba(255,184,0,0.8)"], [1, "rgba(255,71,87,0.9)"]
                ],
                line=dict(color="rgba(255,255,255,0.1)", width=1)
            ),
            textfont=dict(color="white", size=13, family="JetBrains Mono")
        ))
        bar_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8892b0", family="DM Sans"),
            xaxis=dict(tickfont=dict(color="#8892b0", size=12), title="Risk Factors", title_font=dict(color="#8892b0"), showline=True, linecolor="rgba(255,255,255,0.1)"),
            yaxis=dict(tickfont=dict(color="#8892b0", size=12), title="Severity Score", title_font=dict(color="#8892b0"), gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.1)"),
            margin=dict(l=20, r=20, t=20, b=20), autosize=True
        )
        st.plotly_chart(bar_fig, use_container_width=True, config={"responsive": True})

        # ---- CLINICAL INSIGHTS ----
        st.markdown('<h2 style="font-size:1.1rem; margin:20px 0 16px; color:#8892b0; font-weight:500; letter-spacing:0.05em; text-transform:uppercase;">🔬 Risk Factor Analysis</h2>', unsafe_allow_html=True)
        
        risk_factors, positive_factors = [], []
        if glucose >= 126:
            risk_factors.append("High Glucose Level (≥126 mg/dL)")
        elif 100 <= glucose < 126:
            risk_factors.append("Prediabetic Glucose Level (100–125 mg/dL)")
        else:
            positive_factors.append("Normal Glucose Level (<100 mg/dL)")
        if bmi > 30:
            risk_factors.append("High BMI (Obesity)")
        elif 18.5 <= bmi <= 24.9:
            positive_factors.append("Healthy BMI")
        if age > 45:
            risk_factors.append("Age above 45")
        if bp > 120:
            risk_factors.append("High Blood Pressure (>120 mmHg)")
        elif 90 <= bp <= 120:
            positive_factors.append("Normal Blood Pressure")
        if dpf > 0.5:
            risk_factors.append("Higher Genetic Risk")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<h3 style="font-size:0.95rem; color:#ffa0aa; margin-bottom:14px;">⚠️ Identified Risk Factors</h3>', unsafe_allow_html=True)
            if risk_factors:
                for f in risk_factors:
                    st.markdown(f'<div class="risk-badge">🚨 {f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8892b0; font-size:13px;">No critical risk vectors detected.</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_r2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<h3 style="font-size:0.95rem; color:#80f7cf; margin-bottom:14px;">🛡️ Positive Health Indicators</h3>', unsafe_allow_html=True)
            if positive_factors:
                for f in positive_factors:
                    st.markdown(f'<div class="safe-badge">✅ {f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8892b0; font-size:13px;">No optimal protective factors highlighted.</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ---- RECOMMENDATIONS ----
        st.markdown('<h2 style="font-size:1.1rem; margin:20px 0 16px; color:#8892b0; font-weight:500; letter-spacing:0.05em; text-transform:uppercase;">💊 Recommendations</h2>', unsafe_allow_html=True)
        if prob_positive >= 70:
            st.error("- Consult a healthcare professional immediately\n- Get complete diabetes screening\n- Monitor blood sugar regularly\n- Improve diet and physical activity")
            recs_for_pdf = ["Consult a healthcare professional immediately", "Get complete diabetes screening", "Monitor blood sugar regularly", "Improve diet and physical activity"]
        elif prob_positive >= 30:
            st.warning("- Maintain healthy diet\n- Increase physical activity\n- Monitor glucose periodically")
            recs_for_pdf = ["Maintain healthy diet", "Increase physical activity", "Monitor glucose periodically"]
        else:
            st.success("- Continue healthy lifestyle\n- Exercise regularly\n- Routine health check-ups")
            recs_for_pdf = ["Continue healthy lifestyle", "Exercise regularly", "Routine health check-ups"]

        # ---- PDF GENERATION ----
        st.markdown("<br>", unsafe_allow_html=True)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#0f172a"), alignment=1, spaceAfter=5, fontName="Helvetica-Bold")
        date_style = ParagraphStyle("DateStyle", parent=styles["Normal"], fontSize=10, textColor=colors.dimgrey, alignment=1, spaceAfter=20, fontName="Helvetica-Oblique")
        heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#005bea"), spaceBefore=15, spaceAfter=10, fontName="Helvetica-Bold", borderPadding=6, backColor=colors.HexColor("#f8fafc"))
        normal_style = styles["Normal"]
        normal_style.fontSize = 11
        normal_style.spaceAfter = 6
        address_style = ParagraphStyle("AddressStyle", parent=styles["Normal"], fontSize=11, leading=14)

        elements.append(Paragraph("🩺 DIABETES RISK PREDICTION REPORT", title_style))
        report_date = current_time.strftime("%d %B %Y | %I:%M %p (IST)")
        elements.append(Paragraph(f"Report Generated On: {report_date}", date_style))

        address_paragraph = Paragraph(info.get("address", "N/A"), address_style)
        patient_table = [
            ["Patient ID", info.get("_id", "N/A")], ["Full Name", info.get("name", "N/A")],
            ["Email Address", info.get("email", "N/A")], ["Phone Number", info.get("phone", "N/A")],
            ["Country", info.get("country", "N/A")], ["Address", address_paragraph]
        ]
        table = Table(patient_table, colWidths=[2.2*inch, 4.3*inch])
        table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f1f5f9")),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
            ("PADDING", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE")
        ]))
        elements.append(Paragraph("Patient Profile", heading_style))
        elements.append(table)
        elements.append(Spacer(1, 0.2 * inch))

        medical_inputs = [
            ["Age", f"{age} Years"], ["Gender", gender], ["Glucose Level", f"{glucose} mg/dL"],
            ["Blood Pressure", f"{bp} mmHg"], ["Skin Thickness", f"{skin} mm"],
            ["Insulin Level", f"{insulin} IU/mL"], ["BMI", str(bmi)],
            ["Diabetes Pedigree Function", str(dpf)]
        ]
        if gender == "Female":
            medical_inputs.insert(2, ["Number of Pregnancies", str(pregnancies)])

        med_table = Table(medical_inputs, colWidths=[2.2*inch, 4.3*inch])
        med_table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f1f5f9")),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
            ("PADDING", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE")
        ]))
        elements.append(Paragraph("Clinical Inputs", heading_style))
        elements.append(med_table)
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph("Risk Assessment Result", heading_style))
        if prob_positive < 30:
            risk_level_str = "<font color='green'><b>LOW RISK - Diabetes Unlikely</b></font>"
        elif prob_positive < 70:
            risk_level_str = "<font color='#d97706'><b>MODERATE RISK - Possible Diabetes</b></font>"
        else:
            risk_level_str = "<font color='red'><b>HIGH RISK - Diabetes Likely</b></font>"

        elements.append(Paragraph(f"<b>Overall Risk Level:</b> {risk_level_str}", normal_style))
        elements.append(Paragraph(f"<b>Risk Percentage:</b> {prob_positive:.1f}%", normal_style))
        elements.append(Spacer(1, 0.2 * inch))

        try:
            time.sleep(1)
            pdf_bar = go.Figure(bar_fig)
            pdf_bar.update_layout(font=dict(color="black"), paper_bgcolor="white", plot_bgcolor="white", title="Risk Severity")
            pdf_bar.update_xaxes(tickfont=dict(color="black"), title_font=dict(color="black"), linecolor="black")
            pdf_bar.update_yaxes(tickfont=dict(color="black"), title_font=dict(color="black"), gridcolor="lightgrey", zerolinecolor="black")

            pdf_pie = go.Figure(pie_fig)
            pdf_pie.update_layout(font=dict(color="black"), paper_bgcolor="white", plot_bgcolor="white", title="Risk Contribution")

            bar_img_bytes = pdf_bar.to_image(format="png", engine="kaleido", width=350, height=280, scale=2)
            pie_img_bytes = pdf_pie.to_image(format="png", engine="kaleido", width=350, height=280, scale=2)

            bar_rl = RLImage(BytesIO(bar_img_bytes), width=3.2*inch, height=2.5*inch)
            pie_rl = RLImage(BytesIO(pie_img_bytes), width=3.2*inch, height=2.5*inch)

            elements.append(Paragraph("Data Visualization & Analysis", heading_style))
            chart_table = Table([[bar_rl, pie_rl]], colWidths=[3.3*inch, 3.3*inch])
            chart_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#e2e8f0")),
                ('BOTTOMPADDING', (0,0), (-1,-1), 15),
                ('TOPPADDING', (0,0), (-1,-1), 10)
            ]))
            elements.append(chart_table)
        except Exception as e:
            elements.append(Paragraph("<font color='red'><i>* Charts could not be generated. Run 'pip install -U kaleido'.</i></font>", normal_style))

        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph("Medical Recommendations", heading_style))
        rec_list = [ListItem(Paragraph(r, normal_style)) for r in recs_for_pdf]
        elements.append(ListFlowable(rec_list, bulletType='bullet'))
        elements.append(Spacer(1, 0.4 * inch))
        elements.append(Paragraph("<b>Medical Disclaimer:</b> This report is AI-generated and does not replace professional medical advice.", styles["Italic"]))

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        st.download_button(
            label="📄 Download Professional Medical Report (PDF)",
            data=pdf,
            file_name=f"Diabetes_Report_{info.get('name', 'Patient')}.pdf",
            mime="application/pdf"
        )

        st.markdown("---")
        st.warning("⚠️ Medical Disclaimer:\nThis tool does NOT replace professional medical advice.")


# =====================================================
# Navigation
# =====================================================
if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
        
