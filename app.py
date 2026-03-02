# -----------------------------
# Import Required Libraries
# -----------------------------
import streamlit as st
import numpy as np
import joblib
import base64
import re
import pycountry
import phonenumbers
import time
import io

def get_base64_image(image_file):
    try:
        with open(image_file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

def country_to_flag(country_code):
    return "".join(chr(127397 + ord(char)) for char in country_code.upper())

# ✅ PDF Generation
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
    ListFlowable, ListItem, Table, TableStyle, Image as RLImage, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm, cm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# -----------------------------
# MongoDB Connection
# -----------------------------
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
    page_title="Diabetes Prediction System",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# GLOBAL PREMIUM CSS
# =====================================================
def inject_premium_css(page_type="registration"):

    if page_type == "registration":
        bg_gradient = "linear-gradient(135deg, #0a0f2e 0%, #0d2137 40%, #0a2744 70%, #061428 100%)"
        accent = "#38bdf8"
        accent2 = "#818cf8"
    else:
        bg_gradient = "linear-gradient(135deg, #020c1b 0%, #0d2137 35%, #0a3352 65%, #031525 100%)"
        accent = "#0ea5e9"
        accent2 = "#06b6d4"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Poppins:wght@400;600;700;800&display=swap');

    /* ── BASE ── */
    .stApp {{
        background: {bg_gradient} !important;
        background-attachment: fixed !important;
        font-family: 'Inter', sans-serif !important;
        color: #f1f5f9 !important;
        min-height: 100vh;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background-image:
            radial-gradient(circle at 15% 20%, rgba(56,189,248,0.08) 0%, transparent 45%),
            radial-gradient(circle at 85% 80%, rgba(129,140,248,0.08) 0%, transparent 45%),
            radial-gradient(circle at 50% 50%, rgba(6,182,212,0.04) 0%, transparent 55%);
        pointer-events: none;
        z-index: 0;
    }}

    /* ── HIDE STREAMLIT CHROME ── */
    #MainMenu, footer, header {{ visibility: hidden !important; }}
    .stDeployButton {{ display: none !important; }}

    /* ── RESPONSIVE ── */
    @media (max-width: 768px) {{
        .block-container {{ padding: 1rem 0.7rem !important; }}
        .main-title {{ font-size: 1.7rem !important; }}
        .stat-grid {{ grid-template-columns: repeat(2, 1fr) !important; }}
    }}
    @media (min-width: 769px) and (max-width: 1200px) {{
        .block-container {{ padding: 1.5rem 2rem !important; }}
    }}
    @media (min-width: 1201px) {{
        .block-container {{ padding: 2rem 3rem !important; max-width: 1380px; margin: auto; }}
    }}

    /* ── MEDICAL CROSS PATTERN BACKGROUND ── */
    .med-pattern {{
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: -1;
        opacity: 0.025;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Crect x='26' y='10' width='8' height='40' rx='2' fill='%2338bdf8'/%3E%3Crect x='10' y='26' width='40' height='8' rx='2' fill='%2338bdf8'/%3E%3C/svg%3E");
    }}

    /* ── GLASS CARDS ── */
    .premium-card {{
        background: rgba(255,255,255,0.035) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: 18px !important;
        padding: clamp(16px, 3vw, 26px) !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.07) !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease !important;
        margin-bottom: 18px !important;
        position: relative;
        overflow: hidden;
    }}
    .premium-card::after {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent 10%, {accent} 50%, transparent 90%);
        opacity: 0.45;
    }}
    .premium-card:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 18px 50px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.12) !important;
        border-color: rgba(14,165,233,0.28) !important;
    }}

    /* ── RISK BADGES ── */
    .risk-badge {{
        background: linear-gradient(135deg, rgba(239,68,68,0.1), rgba(239,68,68,0.04));
        border-left: 4px solid #ef4444;
        padding: 9px 15px;
        border-radius: 10px;
        margin-bottom: 9px;
        font-weight: 600;
        color: #fca5a5;
        font-size: clamp(12px, 1.4vw, 14px);
    }}
    .safe-badge {{
        background: linear-gradient(135deg, rgba(16,185,129,0.1), rgba(16,185,129,0.04));
        border-left: 4px solid #10b981;
        padding: 9px 15px;
        border-radius: 10px;
        margin-bottom: 9px;
        font-weight: 600;
        color: #6ee7b7;
        font-size: clamp(12px, 1.4vw, 14px);
    }}

    /* ── TYPOGRAPHY ── */
    h1, h2, h3, h4 {{
        font-family: 'Poppins', sans-serif !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }}
    .main-title {{
        background: linear-gradient(135deg, {accent} 0%, {accent2} 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-size: clamp(1.8rem, 4vw, 2.9rem) !important;
        text-align: center;
        margin-bottom: 6px !important;
        font-weight: 900 !important;
        font-family: 'Poppins', sans-serif !important;
        line-height: 1.15;
        display: block;
    }}
    .subtitle {{
        text-align: center;
        color: rgba(203,213,225,0.75) !important;
        font-size: clamp(13px, 1.8vw, 17px) !important;
        margin-bottom: 1.8rem !important;
        letter-spacing: 0.4px;
    }}

    /* ── SIDEBAR ── */
    section[data-testid="stSidebar"] {{
        background: rgba(5,12,30,0.92) !important;
        backdrop-filter: blur(30px) !important;
        -webkit-backdrop-filter: blur(30px) !important;
        border-right: 1px solid rgba(14,165,233,0.15) !important;
        box-shadow: 4px 0 28px rgba(0,0,0,0.45) !important;
    }}
    section[data-testid="stSidebar"] > div {{ padding: 1.2rem 1rem !important; }}
    section[data-testid="stSidebar"] * {{ color: #f1f5f9 !important; }}
    section[data-testid="stSidebar"] h1 {{
        font-size: 1.15rem !important;
        background: linear-gradient(135deg, {accent}, {accent2}) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(14,165,233,0.2);
        margin-bottom: 14px !important;
    }}

    /* ── WHITE INPUTS ── */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div:first-child,
    div[data-baseweb="textarea"] > div {{
        background-color: #f8fafc !important;
        border-radius: 11px !important;
        border: 1.5px solid #cbd5e1 !important;
        color: #0f172a !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.07) !important;
        transition: all 0.22s ease !important;
    }}
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within {{
        border: 2px solid #0ea5e9 !important;
        box-shadow: 0 0 0 3px rgba(14,165,233,0.18) !important;
        background-color: #fff !important;
    }}
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }}
    div[data-baseweb="select"] span, div[data-baseweb="select"] div {{
        color: #0f172a !important;
        font-weight: 600 !important;
    }}
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {{ -webkit-appearance: none; margin: 0; }}
    input[type="number"] {{ -moz-appearance: textfield; }}

    /* ── SKY BLUE SLIDERS: filled=sky blue, unfilled=white ── */
    div[data-baseweb="slider"] [role="slider"] {{
        background-color: #0ea5e9 !important;
        border: 3px solid #ffffff !important;
        box-shadow: 0 0 0 3px rgba(14,165,233,0.45), 0 3px 10px rgba(14,165,233,0.5) !important;
        width: 20px !important;
        height: 20px !important;
        border-radius: 50% !important;
        transition: box-shadow 0.2s ease, transform 0.15s ease !important;
        cursor: grab !important;
    }}
    div[data-baseweb="slider"] [role="slider"]:hover {{
        box-shadow: 0 0 0 5px rgba(14,165,233,0.35), 0 5px 14px rgba(14,165,233,0.6) !important;
        transform: scale(1.12) !important;
    }}
    div[data-baseweb="slider"] div[data-testid="stTickBar"] {{ display: none !important; }}
    /* Filled track portion → sky blue */
    [data-baseweb="slider"] div[class*="inner"] > div:first-child,
    [data-baseweb="slider"] div[style*="rgb(0, 158, 255)"],
    div[data-baseweb="slider"] div[style*="background-color: rgb(0, 158, 255)"] {{
        background-color: #0ea5e9 !important;
        height: 6px !important;
        border-radius: 3px 0 0 3px !important;
    }}
    /* Unfilled track portion → white */
    [data-baseweb="slider"] div[class*="inner"] > div:last-child {{
        background-color: rgba(255,255,255,0.3) !important;
        height: 6px !important;
        border-radius: 0 3px 3px 0 !important;
    }}

    /* ── LABELS ── */
    label {{
        color: rgba(203,213,225,0.92) !important;
        font-size: clamp(12px, 1.4vw, 14px) !important;
        font-weight: 600 !important;
        letter-spacing: 0.15px;
    }}

    /* ── BUTTONS ── */
    button[kind="primary"],
    div[data-testid="stForm"] button[type="submit"],
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: clamp(13px, 1.4vw, 15px) !important;
        box-shadow: 0 4px 18px rgba(14,165,233,0.35) !important;
        transition: all 0.22s ease !important;
        height: 46px !important;
    }}
    button[kind="primary"]:hover {{
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 8px 28px rgba(14,165,233,0.55) !important;
    }}
    .stButton > button:not([kind="primary"]) {{
        background: rgba(255,255,255,0.06) !important;
        border: 1.5px solid rgba(255,255,255,0.18) !important;
        color: #f1f5f9 !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        height: 46px !important;
        transition: all 0.22s ease !important;
    }}
    .stButton > button:not([kind="primary"]):hover {{
        background: rgba(239,68,68,0.12) !important;
        border-color: rgba(239,68,68,0.5) !important;
        color: #fca5a5 !important;
    }}
    div.stDownloadButton > button {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 14px !important;
        border: none !important;
        box-shadow: 0 4px 18px rgba(16,185,129,0.35) !important;
        transition: all 0.22s ease !important;
        width: 100% !important;
        height: 54px !important;
        font-size: 15px !important;
    }}
    div.stDownloadButton > button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 32px rgba(16,185,129,0.55) !important;
    }}

    /* ── FORM ── */
    div[data-testid="stForm"] {{
        background: rgba(8,14,40,0.62) !important;
        backdrop-filter: blur(28px) !important;
        -webkit-backdrop-filter: blur(28px) !important;
        border-radius: 22px !important;
        padding: clamp(18px, 4vw, 38px) !important;
        border: 1px solid rgba(56,189,248,0.14) !important;
        box-shadow: 0 28px 64px rgba(0,0,0,0.52), inset 0 1px 0 rgba(255,255,255,0.055) !important;
        position: relative; overflow: hidden;
    }}
    div[data-testid="stForm"]::before {{
        content: "";
        position: absolute;
        top: 0; left: 8%; right: 8%;
        height: 1px;
        background: linear-gradient(90deg, transparent, #0ea5e9, transparent);
    }}

    /* ── METRICS ── */
    div[data-testid="stMetric"] {{
        background: rgba(14,165,233,0.06) !important;
        border-radius: 14px !important;
        padding: 14px !important;
        border: 1px solid rgba(14,165,233,0.15) !important;
        text-align: center;
    }}
    div[data-testid="stMetricValue"] {{
        color: #38bdf8 !important;
        font-size: clamp(1.3rem, 2.5vw, 1.9rem) !important;
        font-weight: 800 !important;
    }}
    div[data-testid="stMetricLabel"] {{
        color: #94a3b8 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}

    /* ── STAT GRID ── */
    .stat-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 10px; margin: 14px 0;
    }}
    .stat-card {{
        background: rgba(14,165,233,0.06);
        border: 1px solid rgba(14,165,233,0.18);
        border-radius: 12px;
        padding: 14px 10px; text-align: center;
        transition: transform 0.2s ease;
    }}
    .stat-card:hover {{ transform: translateY(-2px); }}
    .stat-card .sv {{ font-size: clamp(17px,2.2vw,21px); font-weight: 800; color: #38bdf8; }}
    .stat-card .sl {{ font-size: 10px; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; margin-top: 3px; }}

    /* ── PROFILE CHIP ── */
    .profile-chip {{
        background: rgba(14,165,233,0.08);
        border: 1px solid rgba(14,165,233,0.2);
        border-radius: 10px; padding: 8px 12px; margin-bottom: 7px; font-size: 13px;
    }}
    .profile-chip .chip-label {{
        color: #7dd3fc !important; font-weight: 700;
        font-size: 10px; text-transform: uppercase; letter-spacing: 0.6px;
        display: block; margin-bottom: 1px;
    }}
    .profile-chip .chip-value {{ color: #e2e8f0 !important; font-weight: 500; word-break: break-word; }}

    /* ── SECTION HEADING ── */
    .section-heading {{
        font-family: 'Poppins', sans-serif;
        font-size: clamp(15px, 1.8vw, 19px); font-weight: 700; color: #f1f5f9;
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 14px; padding-bottom: 9px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
    }}
    .section-heading::before {{
        content: ""; display: inline-block;
        width: 4px; height: 20px;
        background: linear-gradient(180deg, #0ea5e9, #818cf8);
        border-radius: 2px; flex-shrink: 0;
    }}

    /* ── FEATURE CARDS ── */
    .feature-card {{
        background: rgba(14,165,233,0.05);
        border: 1px solid rgba(14,165,233,0.15);
        border-radius: 16px; padding: 22px 16px; text-align: center;
        transition: all 0.25s ease; height: 100%;
    }}
    .feature-card:hover {{
        background: rgba(14,165,233,0.1); transform: translateY(-4px);
        border-color: rgba(14,165,233,0.35);
    }}
    .feature-card .fi {{ font-size: 2.2rem; margin-bottom: 10px; }}
    .feature-card .ft {{ font-weight: 700; font-size: 15px; color: #f1f5f9; margin-bottom: 6px; }}
    .feature-card .fd {{ font-size: 12px; color: #94a3b8; line-height: 1.5; }}

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
    ::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.03); }}
    ::-webkit-scrollbar-thumb {{ background: rgba(14,165,233,0.4); border-radius: 10px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: rgba(14,165,233,0.65); }}
    hr {{ border-color: rgba(255,255,255,0.08) !important; margin: 1.2rem 0 !important; }}
    div[data-testid="stAlert"] {{ border-radius: 13px !important; }}
    </style>
    <div class="med-pattern"></div>
    """, unsafe_allow_html=True)


# =====================================================
# REGISTRATION PAGE
# =====================================================
def registration_page():
    inject_premium_css("registration")

    st.markdown('<h1 class="main-title">📝 Patient Registration</h1>', unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Secure access to the AI-Powered Diabetes Risk Assessment System</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        with st.form("registration_form"):
            st.markdown('<div class="section-heading">Personal Information</div>', unsafe_allow_html=True)
            name = st.text_input("Full Name")
            country_list = [country.name for country in pycountry.countries]
            selected_country = st.selectbox("🌍 Select Country", country_list)
            country_obj = pycountry.countries.get(name=selected_country)
            country_code = phonenumbers.country_code_for_region(country_obj.alpha_2)
            phone = st.text_input("Enter Phone Number (without country code)")
            email = st.text_input("Email Address")
            address = st.text_area("Address")
            submit = st.form_submit_button("Register", use_container_width=True)

            if submit:
                name = name.strip(); phone = phone.strip()
                email = email.strip(); address = address.strip()
                if not name or not phone or not email or not address:
                    st.error("❌ Please fill all fields properly"); return
                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(email_pattern, email):
                    st.error("❌ Please enter a valid email address"); return
                region_code = country_obj.alpha_2
                try:
                    parsed_number = phonenumbers.parse(phone, region_code)
                    if not phonenumbers.is_valid_number(parsed_number):
                        st.error("❌ Invalid phone number for selected country"); return
                    formatted_phone = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
                except:
                    st.error("❌ Invalid phone number format"); return
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


# =====================================================
# PDF GENERATION
# =====================================================
def generate_professional_pdf(info, age, gender, pregnancies, glucose, bp, skin,
                               insulin, bmi, dpf, prob_positive, prob_negative,
                               risk_label, risk_factors, positive_factors,
                               recs_for_pdf, current_time, cause_labels, cause_values):

    buffer = BytesIO()
    W, H = A4
    usable_w = W - 3.4*cm

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.7*cm, leftMargin=1.7*cm,
        topMargin=1.4*cm, bottomMargin=1.4*cm
    )
    elements = []

    # ── Color Palette ──
    C_DARK   = colors.HexColor("#0f172a");  C_NAVY   = colors.HexColor("#1e3a5f")
    C_DKNAVY = colors.HexColor("#0c1f3a");  C_BLUE   = colors.HexColor("#0ea5e9")
    C_CYAN   = colors.HexColor("#06b6d4");  C_TEAL   = colors.HexColor("#0d9488")
    C_GREEN  = colors.HexColor("#10b981");  C_AMBER  = colors.HexColor("#f59e0b")
    C_RED    = colors.HexColor("#ef4444");  C_LRED   = colors.HexColor("#fff5f5")
    C_LGREE  = colors.HexColor("#f0fdf4");  C_LAMBER = colors.HexColor("#fffbeb")
    C_GREY   = colors.HexColor("#64748b");  C_LGREY  = colors.HexColor("#f1f5f9")
    C_MID    = colors.HexColor("#e2e8f0");  C_WHITE  = colors.white
    C_FAINT  = colors.HexColor("#f8fafc")

    if prob_positive < 30:
        C_RISK = C_GREEN; risk_bg = C_LGREE; risk_str = "LOW RISK – Diabetes Unlikely"; risk_icon = "✅"
    elif prob_positive < 70:
        C_RISK = C_AMBER; risk_bg = C_LAMBER; risk_str = "MODERATE RISK – Possible Diabetes"; risk_icon = "⚠️"
    else:
        C_RISK = C_RED; risk_bg = C_LRED; risk_str = "HIGH RISK – Diabetes Likely"; risk_icon = "❌"

    def S(name, **kw): return ParagraphStyle(name, **kw)

    s_hosp = S("hn", fontName="Helvetica-Bold", fontSize=17, textColor=C_WHITE, alignment=TA_CENTER, leading=21, spaceAfter=2)
    s_hsub = S("hs", fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#bae6fd"), alignment=TA_CENTER, leading=13)
    s_rtit = S("rt", fontName="Helvetica-Bold", fontSize=12, textColor=colors.HexColor("#e0f2fe"), alignment=TA_CENTER, leading=16, spaceBefore=6, spaceAfter=3)
    s_rsub = S("rs", fontName="Helvetica-Oblique", fontSize=8.5, textColor=colors.HexColor("#7dd3fc"), alignment=TA_CENTER, leading=12)
    s_secH = S("sh", fontName="Helvetica-Bold", fontSize=10.5, textColor=C_WHITE, leading=14, leftIndent=4)
    s_norm = S("nm", fontName="Helvetica", fontSize=10, textColor=C_DARK, leading=14)
    s_bold = S("bl", fontName="Helvetica-Bold", fontSize=10, textColor=C_DARK, leading=14)
    s_small= S("sm", fontName="Helvetica", fontSize=8.5, textColor=C_GREY, leading=12)
    s_disc = S("dc", fontName="Helvetica-Oblique", fontSize=8, textColor=C_GREY, alignment=TA_JUSTIFY, leading=11)
    s_risk = S("rk", fontName="Helvetica-Bold", fontSize=14.5, textColor=C_RISK, alignment=TA_CENTER, leading=19)
    s_rf   = S("rf", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.HexColor("#991b1b"), leading=14)
    s_pf   = S("pf", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.HexColor("#065f46"), leading=14)
    s_rec  = S("rc", fontName="Helvetica", fontSize=10, textColor=C_DARK, leading=15, spaceAfter=2)

    def sec_hdr(title):
        t = Table([[Paragraph(f"  {title}", s_secH)]], colWidths=[usable_w])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), C_NAVY),
            ("TOPPADDING", (0,0),(-1,-1), 7), ("BOTTOMPADDING",(0,0),(-1,-1), 7),
            ("LEFTPADDING",(0,0),(-1,-1), 12),
            ("LINEABOVE",  (0,0),(-1,0), 2.5, C_BLUE),
            ("LINEBELOW",  (0,-1),(-1,-1), 0.5, C_CYAN),
        ]))
        return t

    def kv_tbl(rows, w1_frac=0.38):
        w1 = usable_w * w1_frac; w2 = usable_w - w1
        data = [[Paragraph(k, s_bold),
                 v if isinstance(v, Paragraph) else Paragraph(str(v), s_norm)]
                for k, v in rows]
        t = Table(data, colWidths=[w1, w2])
        t.setStyle(TableStyle([
            ("GRID",          (0,0),(-1,-1), 0.5, C_MID),
            ("BACKGROUND",    (0,0),(0,-1),  C_LGREY),
            ("ROWBACKGROUNDS",(0,0),(-1,-1), [C_WHITE, C_FAINT]),
            ("BACKGROUND",    (0,0),(0,-1),  C_LGREY),
            ("TOPPADDING",    (0,0),(-1,-1), 7), ("BOTTOMPADDING",(0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(-1,-1), 10), ("RIGHTPADDING",(0,0),(-1,-1), 10),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        return t

    # ── HEADER ──
    hdr_data = [
        [Paragraph("🏥  MEDISCAN DIABETES CENTER", s_hosp)],
        [Paragraph("Advanced Clinical Diagnostics & AI-Powered Predictive Medicine", s_hsub)],
        [Spacer(1, 5)],
        [Paragraph("DIABETES RISK PREDICTION REPORT", s_rtit)],
        [Paragraph(f"Confidential Medical Document  ·  {current_time.strftime('%d %B %Y, %I:%M %p IST')}", s_rsub)],
    ]
    hdr = Table([[row[0]] for row in hdr_data], colWidths=[usable_w])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_DKNAVY),
        ("TOPPADDING",    (0,0),(0,0), 12),
        ("TOPPADDING",    (0,1),(-1,-1), 4),
        ("BOTTOMPADDING", (0,-1),(-1,-1), 12),
        ("BOTTOMPADDING", (0,0),(-1,-2), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 16),
        ("RIGHTPADDING",  (0,0),(-1,-1), 16),
        ("LINEBELOW",     (0,-1),(-1,-1), 3, C_BLUE),
    ]))
    elements.append(hdr); elements.append(Spacer(1, 7))

    id_tbl = Table([[
        Paragraph(f"Patient ID: <b>{info.get('_id','N/A')}</b>", s_norm),
        Paragraph(f"Date: <b>{current_time.strftime('%d-%m-%Y')}</b>", s_norm),
        Paragraph(f"Time: <b>{current_time.strftime('%I:%M %p IST')}</b>", s_norm),
    ]], colWidths=[usable_w/3]*3)
    id_tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#f0f9ff")),
        ("GRID",(0,0),(-1,-1),0.5,C_MID),
        ("TOPPADDING",(0,0),(-1,-1),6), ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),10), ("ALIGN",(0,0),(-1,-1),"CENTER"),
    ]))
    elements.append(id_tbl); elements.append(Spacer(1, 10))

    # ── 1. PATIENT PROFILE ──
    elements.append(sec_hdr("1.  Patient Profile")); elements.append(Spacer(1, 5))
    elements.append(kv_tbl([
        ("Full Name",     info.get("name","N/A")),
        ("Email Address", info.get("email","N/A")),
        ("Phone Number",  info.get("phone","N/A")),
        ("Country",       info.get("country","N/A")),
        ("Address",       Paragraph(info.get("address","N/A"), s_norm)),
        ("Registered On", info.get("created_at","N/A")),
    ]))
    elements.append(Spacer(1, 10))

    # ── 2. CLINICAL INPUTS ──
    elements.append(sec_hdr("2.  Clinical Inputs")); elements.append(Spacer(1, 5))
    med_rows = [
        ("Age", f"{age} Years"), ("Gender", gender),
        ("Glucose Level", f"{glucose} mg/dL"), ("Blood Pressure", f"{bp} mmHg"),
        ("Skin Thickness", f"{skin} mm"), ("Insulin Level", f"{insulin} IU/mL"),
        ("BMI", f"{bmi}"), ("Diabetes Pedigree Function", f"{dpf}"),
    ]
    if gender == "Female": med_rows.insert(2, ("Number of Pregnancies", str(pregnancies)))
    elements.append(kv_tbl(med_rows)); elements.append(Spacer(1, 10))

    # ── 3. RISK ASSESSMENT ──
    elements.append(sec_hdr("3.  Risk Assessment Result")); elements.append(Spacer(1, 7))
    risk_box = Table([[Paragraph(f"{risk_icon}  {risk_str}", s_risk)]], colWidths=[usable_w])
    risk_box.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), risk_bg),
        ("BOX",(0,0),(-1,-1),2,C_RISK), ("LINEABOVE",(0,0),(-1,0),4,C_RISK),
        ("TOPPADDING",(0,0),(-1,-1),14), ("BOTTOMPADDING",(0,0),(-1,-1),14),
    ]))
    elements.append(risk_box); elements.append(Spacer(1, 8))
    elements.append(kv_tbl([
        ("Non-Diabetic Probability", f"{prob_negative:.1f}%"),
        ("Diabetic Probability",     f"{prob_positive:.1f}%"),
        ("Risk Classification",       risk_label),
    ]))
    elements.append(Spacer(1, 10))

    # ── 4. DATA VISUALIZATION ──
    elements.append(sec_hdr("4.  Data Visualization & Risk Analysis")); elements.append(Spacer(1, 8))
    try:
        sns.set_style("whitegrid")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.0), facecolor="#ffffff")
        fig.patch.set_facecolor("#ffffff")

        bar_clrs = ["#ef4444" if v >= 70 else "#f59e0b" if v >= 40 else "#10b981" for v in cause_values]
        bars = ax1.barh(cause_labels, cause_values, color=bar_clrs, edgecolor="white", linewidth=1.0, height=0.5)
        ax1.set_xlim(0, 118)
        ax1.set_xlabel("Severity Level", fontsize=9, color="#374151", fontweight="bold")
        ax1.set_title("Risk Factor Severity", fontsize=11, fontweight="bold", color="#1e3a5f", pad=9)
        ax1.tick_params(axis='y', labelsize=8.5, colors="#374151")
        ax1.tick_params(axis='x', labelsize=8, colors="#6b7280")
        ax1.set_facecolor("#f8fafc")
        ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_color("#e5e7eb"); ax1.spines['bottom'].set_color("#e5e7eb")
        ax1.xaxis.grid(True, color="#e5e7eb", linewidth=0.7, alpha=0.8)
        ax1.set_axisbelow(True)
        for bar, val in zip(bars, cause_values):
            ax1.text(val+1.5, bar.get_y()+bar.get_height()/2, f"{val:.0f}",
                     va='center', ha='left', fontsize=8.5, fontweight="bold", color="#374151")
        ax1.legend(handles=[
            mpatches.Patch(color="#ef4444", label="High (≥70)"),
            mpatches.Patch(color="#f59e0b", label="Medium (40–70)"),
            mpatches.Patch(color="#10b981", label="Low (<40)"),
        ], loc="lower right", fontsize=7, framealpha=0.9, edgecolor="#e5e7eb")

        pie_pal = ["#0ea5e9","#06b6d4","#8b5cf6","#f59e0b","#10b981","#ef4444"]
        _, _, autotexts = ax2.pie(
            cause_values, labels=None, autopct='%1.1f%%', startangle=90,
            colors=pie_pal[:len(cause_labels)], pctdistance=0.76,
            wedgeprops=dict(edgecolor='white', linewidth=1.8, width=0.62)
        )
        for at in autotexts: at.set_fontsize(8.5); at.set_fontweight("bold"); at.set_color("#1e293b")
        ax2.set_title("Risk Contribution (%)", fontsize=11, fontweight="bold", color="#1e3a5f", pad=9)
        ax2.legend(cause_labels, loc="lower center", bbox_to_anchor=(0.5,-0.16),
                   ncol=min(3,len(cause_labels)), fontsize=7.5, framealpha=0.9, edgecolor="#e5e7eb")
        ax2.set_facecolor("#f8fafc")

        plt.tight_layout(pad=1.8)
        c_buf = BytesIO()
        fig.savefig(c_buf, format="png", dpi=160, bbox_inches="tight", facecolor="white", edgecolor="none")
        plt.close(fig); c_buf.seek(0)
        c_img = RLImage(c_buf, width=usable_w, height=usable_w*0.38)
        c_frame = Table([[c_img]], colWidths=[usable_w])
        c_frame.setStyle(TableStyle([
            ("BOX",(0,0),(-1,-1),1,C_MID), ("BACKGROUND",(0,0),(-1,-1),C_WHITE),
            ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),4), ("RIGHTPADDING",(0,0),(-1,-1),4),
        ]))
        elements.append(c_frame); elements.append(Spacer(1, 8))

        # Probability bar
        fig2, ax3 = plt.subplots(figsize=(8, 1.5), facecolor="#f0f9ff")
        bars2 = ax3.barh(["Non-Diabetic","Diabetic"], [prob_negative, prob_positive],
                         color=["#10b981","#ef4444"], edgecolor="white", height=0.38)
        ax3.set_xlim(0, 115)
        ax3.set_title("Probability Breakdown", fontsize=9.5, fontweight="bold", color="#1e3a5f", pad=6)
        ax3.tick_params(labelsize=8.5, colors="#374151"); ax3.set_facecolor("#f0f9ff")
        ax3.spines['top'].set_visible(False); ax3.spines['right'].set_visible(False)
        ax3.axvline(x=50, color="#6b7280", linestyle="--", alpha=0.35, linewidth=0.8)
        for bar, val in zip(bars2, [prob_negative, prob_positive]):
            ax3.text(val+1, bar.get_y()+bar.get_height()/2, f"{val:.1f}%",
                     va='center', ha='left', fontsize=9, fontweight="bold", color="#374151")
        ax3.xaxis.grid(True, color="#e5e7eb", linewidth=0.5); ax3.set_axisbelow(True)
        plt.tight_layout(pad=0.8)
        p_buf = BytesIO()
        fig2.savefig(p_buf, format="png", dpi=150, bbox_inches="tight", facecolor="#f0f9ff")
        plt.close(fig2); p_buf.seek(0)
        p_img = RLImage(p_buf, width=usable_w*0.72, height=usable_w*0.13)
        p_tbl = Table([[p_img]], colWidths=[usable_w])
        p_tbl.setStyle(TableStyle([
            ("ALIGN",(0,0),(-1,-1),"CENTER"), ("BOX",(0,0),(-1,-1),1,C_MID),
            ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#f0f9ff")),
            ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ]))
        elements.append(p_tbl)
    except Exception as e:
        elements.append(Paragraph(f"<font color='red'>Charts could not be generated: {e}</font>", s_norm))

    elements.append(Spacer(1, 10))

    # ── 5. RISK FACTOR ANALYSIS ──
    elements.append(sec_hdr("5.  Risk Factor Analysis")); elements.append(Spacer(1, 6))

    def factor_cell(items, bg, bdr_clr, title_txt, t_clr):
        ts = ParagraphStyle("ft_"+title_txt[:4], fontName="Helvetica-Bold",
                             fontSize=10, textColor=t_clr, leading=14, spaceAfter=4)
        content = [Paragraph(title_txt, ts), Spacer(1, 4)] + items
        t = Table([[content]], colWidths=[(usable_w/2)-5])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),bg),
            ("BOX",(0,0),(-1,-1),1.5,bdr_clr), ("LINEABOVE",(0,0),(-1,0),3,bdr_clr),
            ("TOPPADDING",(0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,-1),10),
            ("LEFTPADDING",(0,0),(-1,-1),12), ("RIGHTPADDING",(0,0),(-1,-1),10),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        return t

    rf_items = [Paragraph(f"🚨  {f}", s_rf) for f in risk_factors] or [Paragraph("No major risk factors identified.", s_small)]
    pf_items = [Paragraph(f"✔️  {f}", s_pf) for f in positive_factors] or [Paragraph("No positive indicators highlighted.", s_small)]

    f_row = Table([
        [factor_cell(rf_items, colors.HexColor("#fff5f5"), C_RED,
                     "⚠️  Identified Risk Factors", C_RED),
         Spacer(10, 1),
         factor_cell(pf_items, colors.HexColor("#f0fdf4"), C_GREEN,
                     "✅  Positive Health Indicators", C_TEAL)]
    ], colWidths=[(usable_w/2)-5, 10, (usable_w/2)-5])
    f_row.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                ("LEFTPADDING",(0,0),(-1,-1),0),
                                ("RIGHTPADDING",(0,0),(-1,-1),0)]))
    elements.append(f_row); elements.append(Spacer(1, 10))

    # ── 6. RECOMMENDATIONS ──
    elements.append(sec_hdr("6.  Medical Recommendations")); elements.append(Spacer(1, 6))
    rec_items = [ListItem(Paragraph(r, s_rec), leftIndent=14, bulletColor=C_BLUE) for r in recs_for_pdf]
    elements.append(ListFlowable(rec_items, bulletType='bullet', bulletColor=C_BLUE, leftIndent=12, spaceAfter=3))
    elements.append(Spacer(1, 16))

    # ── FOOTER ──
    disc = Table([[Paragraph(
        "<b>⚠️ MEDICAL DISCLAIMER:</b>  This report is generated by an AI-based predictive model "
        "and is intended for informational and screening purposes only. It does not constitute a "
        "clinical diagnosis or medical advice. Always consult a qualified healthcare professional "
        "for evaluation, diagnosis, and treatment decisions.", s_disc)]], colWidths=[usable_w])
    disc.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),C_FAINT), ("BOX",(0,0),(-1,-1),0.5,C_MID),
        ("LINEABOVE",(0,0),(-1,0),2.5,C_AMBER),
        ("TOPPADDING",(0,0),(-1,-1),9), ("BOTTOMPADDING",(0,0),(-1,-1),9),
        ("LEFTPADDING",(0,0),(-1,-1),10), ("RIGHTPADDING",(0,0),(-1,-1),10),
    ]))
    elements.append(disc); elements.append(Spacer(1, 7))

    sig = Table([[
        Paragraph(f"<b>Patient ID:</b> {info.get('_id','N/A')}", s_small),
        Paragraph(f"<b>Generated:</b> {current_time.strftime('%d-%m-%Y %I:%M %p')}", s_small),
        Paragraph("<b>Model:</b> SVM Classifier", s_small),
    ]], colWidths=[usable_w/3]*3)
    sig.setStyle(TableStyle([
        ("ALIGN",(0,0),(0,0),"LEFT"), ("ALIGN",(1,0),(1,0),"CENTER"),
        ("ALIGN",(2,0),(2,0),"RIGHT"), ("LINEABOVE",(0,0),(-1,0),0.5,C_MID),
        ("TOPPADDING",(0,0),(-1,-1),5),
    ]))
    elements.append(sig)

    doc.build(elements)
    pdf = buffer.getvalue(); buffer.close()
    return pdf


# =====================================================
# MAIN MODEL + PREDICTION PAGE
# =====================================================
@st.cache_resource
def load_model():
    try:
        model = joblib.load("diabetes_model.pkl")
        scaler = joblib.load("scaler_svm.pkl")
        return model, scaler
    except Exception as e:
        st.error(f"⚠️ Model Loading Error: {e}"); st.stop()


def prediction_page():
    model, scaler = load_model()
    if not st.session_state.patient_info:
        st.session_state.registered = False; st.stop()

    inject_premium_css("prediction")
    info = st.session_state.patient_info

    with st.sidebar:
        st.markdown("<h1>🩺 Patient Profile</h1>", unsafe_allow_html=True)
        for icon, label, key in [("👤","Name","name"),("📞","Phone","phone"),("✉️","Email","email"),("🌍","Country","country")]:
            st.markdown(f"""<div class="profile-chip">
                <span class="chip-label">{icon} {label}</span>
                <span class="chip-value">{info.get(key,'')}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown('<div class="section-heading" style="font-size:14px; margin-bottom:12px;">Medical Inputs</div>', unsafe_allow_html=True)
        age     = st.number_input("Age", 21, 100, 30)
        gender  = st.selectbox("Gender", ["Male", "Female"])
        if gender == "Female":
            pregnancies = st.number_input("Number of Pregnancies", min_value=0, max_value=20, value=0)
        else:
            pregnancies = 0
        glucose = st.slider("Glucose", 0, 200, 120)
        bp      = st.slider("Blood Pressure", 0, 130, 70)
        skin    = st.slider("Skin Thickness", 0, 100, 20)
        insulin = st.slider("Insulin", 0, 900, 80)
        bmi     = st.number_input("BMI", 10.0, 70.0, 25.0)
        dpf     = st.slider("DPF", 0.0, 2.5, 0.5)
        st.markdown("<br>", unsafe_allow_html=True)
        predict_btn = st.button("🔍 Predict", use_container_width=True, type="primary")
        st.markdown("<br>", unsafe_allow_html=True)
        logout_btn  = st.button("🚪 Logout", use_container_width=True)
        if logout_btn:
            st.session_state.registered = False
            st.session_state.patient_info = {}
            st.session_state.show_success = False
            st.rerun()

    st.markdown('<h1 class="main-title">🩺 Diabetes Prediction System</h1>', unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>AI-Powered Diabetes Risk Assessment Tool</p>", unsafe_allow_html=True)

    if st.session_state.show_success:
        st.success("✅ Registration Successful! Welcome to the system.")
        st.session_state.show_success = False

    if not predict_btn:
        c1, c2, c3 = st.columns(3)
        for col, ico, tit, dsc in [
            (c1,"🧬","AI-Powered","SVM machine learning model trained on clinical data"),
            (c2,"📊","Instant Results","Probability-based diabetes risk in seconds"),
            (c3,"📄","PDF Report","Download a professional hospital-grade report"),
        ]:
            col.markdown(f"""<div class="feature-card">
                <div class="fi">{ico}</div><div class="ft">{tit}</div><div class="fd">{dsc}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("""<div class="premium-card" style="margin-top:14px;">
            <div class="section-heading">📋 About This System</div>
            <p style='color:#e2e8f0; font-size:15px; line-height:1.75; margin:0;'>
            This Diabetes Prediction System is an AI-powered medical risk assessment tool designed to estimate
            the likelihood of diabetes based on key health parameters such as glucose level, BMI, blood pressure,
            age, and family history. Fill in your parameters in the sidebar and click <b>Predict</b> to begin.
            </p></div>""", unsafe_allow_html=True)

    if predict_btn:
        import plotly.graph_objects as go
        if "_id" in info:
            users_collection.update_one({"_id": info["_id"]}, {"$set": {"gender": gender}})

        input_data = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
        input_std  = scaler.transform(input_data)
        probability = model.predict_proba(input_std)[0]
        prob_negative = probability[0] * 100
        prob_positive = probability[1] * 100

        if prob_positive < 30:
            risk_label="Low Risk"; risk_color="#10b981"; risk_icon="✅"; risk_txt="LOW RISK – Diabetes Unlikely"
        elif prob_positive < 70:
            risk_label="Moderate Risk"; risk_color="#f59e0b"; risk_icon="⚠️"; risk_txt="MODERATE RISK – Possible Diabetes"
        else:
            risk_label="High Risk"; risk_color="#ef4444"; risk_icon="❌"; risk_txt="HIGH RISK – Diabetes Likely"

        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        predictions_collection.insert_one({
            "patient_id": info["_id"], "patient_name": info["name"], "age": age,
            "gender": gender, "glucose": glucose, "blood_pressure": bp, "bmi": bmi,
            "prediction": risk_label, "probability": round(prob_positive, 2),
            "created_at": current_time.strftime("%d-%m-%Y %H:%M:%S")
        })

        st.markdown("---")
        st.markdown('<div class="section-heading">Prediction Results</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""<div class="premium-card" style="border-left:6px solid {risk_color}; padding:20px 22px;">
                <div style="font-size:clamp(17px,2.4vw,23px); font-weight:800; color:{risk_color};">
                    {risk_icon} {risk_txt}
                </div></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="stat-grid">
                <div class="stat-card"><div class="sv">{prob_negative:.1f}%</div><div class="sl">Non-Diabetic</div></div>
                <div class="stat-card"><div class="sv" style="color:#ef4444;">{prob_positive:.1f}%</div><div class="sl">Diabetic</div></div>
                <div class="stat-card"><div class="sv">{age}</div><div class="sl">Age</div></div>
                <div class="stat-card"><div class="sv">{glucose}</div><div class="sl">Glucose</div></div>
                <div class="stat-card"><div class="sv">{bmi}</div><div class="sl">BMI</div></div>
                <div class="stat-card"><div class="sv">{bp}</div><div class="sl">Blood Pressure</div></div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="premium-card" style="padding:10px;">', unsafe_allow_html=True)
            gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=prob_positive,
                number={"suffix":"%","font":{"color":"white","size":28}},
                title={"text":"Risk Level","font":{"color":"white","size":13}},
                gauge={
                    "axis":{"range":[0,100],"tickcolor":"white","tickfont":{"color":"white","size":9}},
                    "bar":{"color":risk_color,"thickness":0.26},
                    "bgcolor":"rgba(0,0,0,0)","borderwidth":0,
                    "steps":[
                        {"range":[0,30],"color":"rgba(16,185,129,0.22)"},
                        {"range":[30,70],"color":"rgba(245,158,11,0.22)"},
                        {"range":[70,100],"color":"rgba(239,68,68,0.22)"},
                    ],
                }
            ))
            gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
                                 margin=dict(l=18,r=18,t=50,b=10), height=225)
            st.plotly_chart(gauge, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-heading">Risk Factor Analysis</div>', unsafe_allow_html=True)
        risk_factors, positive_factors = [], []
        if glucose >= 126:         risk_factors.append("High Glucose Level (≥126 mg/dL)")
        elif 100 <= glucose < 126: risk_factors.append("Prediabetic Glucose Level (100–125 mg/dL)")
        else:                      positive_factors.append("Normal Glucose Level (<100 mg/dL)")
        if bmi > 30:               risk_factors.append("High BMI (Obesity)")
        elif 18.5 <= bmi <= 24.9:  positive_factors.append("Healthy BMI")
        if age > 45:               risk_factors.append("Age above 45")
        if bp > 120:               risk_factors.append("High Blood Pressure (>120 mmHg)")
        elif 90 <= bp <= 120:      positive_factors.append("Normal Blood Pressure")
        if dpf > 0.5:              risk_factors.append("Higher Genetic Risk")

        r1, r2 = st.columns(2)
        with r1:
            st.markdown('<div class="premium-card" style="height:100%;">', unsafe_allow_html=True)
            st.markdown('<div class="section-heading" style="font-size:13px;color:#fca5a5;border-bottom-color:rgba(239,68,68,0.15);">⚠️ Identified Risk Factors</div>', unsafe_allow_html=True)
            if risk_factors:
                for f in risk_factors: st.markdown(f'<div class="risk-badge">🚨 {f}</div>', unsafe_allow_html=True)
            else: st.markdown('<p style="color:#94a3b8;font-size:13px;">No major risk factors identified.</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with r2:
            st.markdown('<div class="premium-card" style="height:100%;">', unsafe_allow_html=True)
            st.markdown('<div class="section-heading" style="font-size:13px;color:#6ee7b7;border-bottom-color:rgba(16,185,129,0.15);">✅ Positive Health Indicators</div>', unsafe_allow_html=True)
            if positive_factors:
                for f in positive_factors: st.markdown(f'<div class="safe-badge">✔️ {f}</div>', unsafe_allow_html=True)
            else: st.markdown('<p style="color:#94a3b8;font-size:13px;">No positive indicators highlighted.</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-heading">Recommendations</div>', unsafe_allow_html=True)
        if prob_positive >= 70:
            st.error("🚨 Consult a healthcare professional immediately\n🚨 Get complete diabetes screening\n🚨 Monitor blood sugar regularly\n🚨 Improve diet and physical activity")
            recs_for_pdf = ["Consult a healthcare professional immediately","Get complete diabetes screening","Monitor blood sugar regularly","Improve diet and physical activity"]
        elif prob_positive >= 30:
            st.warning("⚠️ Maintain healthy diet\n⚠️ Increase physical activity\n⚠️ Monitor glucose periodically")
            recs_for_pdf = ["Maintain healthy diet","Increase physical activity","Monitor glucose periodically"]
        else:
            st.success("✅ Continue healthy lifestyle\n✅ Exercise regularly\n✅ Routine health check-ups")
            recs_for_pdf = ["Continue healthy lifestyle","Exercise regularly","Routine health check-ups"]

        cause_labels, cause_values = [], []
        if glucose >= 126:  cause_labels.append("High Glucose");        cause_values.append(min(glucose/2,100))
        if bmi > 30:        cause_labels.append("High BMI (Obesity)");  cause_values.append(min(bmi*2,100))
        if age > 45:        cause_labels.append("Age Factor");           cause_values.append(min(age,100))
        if bp > 120:        cause_labels.append("High Blood Pressure");  cause_values.append(min(bp,100))
        if dpf > 0.5:       cause_labels.append("Genetic Risk (DPF)");  cause_values.append(min(dpf*100,100))
        if not cause_labels: cause_labels=["Healthy Indicators"]; cause_values=[100]

        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-heading">📊 Causes of Diabetes (Risk Contribution Analysis)</div>', unsafe_allow_html=True)
        cc1, cc2 = st.columns(2)
        bar_fig = go.Figure(go.Bar(
            x=cause_labels, y=cause_values,
            text=[f"{v:.1f}" for v in cause_values], textposition='auto',
            marker=dict(color=cause_values,
                        colorscale=[[0,"#10b981"],[0.5,"#f59e0b"],[1,"#ef4444"]],
                        line=dict(color="rgba(255,255,255,0.25)",width=1)),
            textfont=dict(color="white",size=13)
        ))
        bar_fig.update_layout(
            title="Risk Factor Severity", xaxis_title="Causes", yaxis_title="Severity Level",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.02)",
            font=dict(color="white"), autosize=True, margin=dict(l=20,r=20,t=50,b=20)
        )
        bar_fig.update_xaxes(tickfont=dict(color="white",size=11), showline=True, linecolor="rgba(255,255,255,0.1)")
        bar_fig.update_yaxes(tickfont=dict(color="white",size=11), gridcolor="rgba(255,255,255,0.06)")
        with cc1: st.plotly_chart(bar_fig, use_container_width=True)

        pie_fig = go.Figure(data=[go.Pie(
            labels=cause_labels, values=cause_values, hole=0.44,
            marker=dict(colors=["#0ea5e9","#06b6d4","#8b5cf6","#f59e0b","#10b981"],
                        line=dict(color="rgba(255,255,255,0.5)",width=2))
        )])
        pie_fig.update_layout(
            title="Percentage Contribution", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"), autosize=True, margin=dict(l=20,r=20,t=50,b=20),
            legend=dict(font=dict(color="white"))
        )
        with cc2: st.plotly_chart(pie_fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        pdf = generate_professional_pdf(
            info=info, age=age, gender=gender, pregnancies=pregnancies,
            glucose=glucose, bp=bp, skin=skin, insulin=insulin, bmi=bmi, dpf=dpf,
            prob_positive=prob_positive, prob_negative=prob_negative,
            risk_label=risk_label, risk_factors=risk_factors,
            positive_factors=positive_factors, recs_for_pdf=recs_for_pdf,
            current_time=current_time, cause_labels=cause_labels, cause_values=cause_values
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📄 Download Professional Medical Report (PDF)",
            data=pdf,
            file_name=f"Diabetes_Report_{info.get('name','Patient')}.pdf",
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
