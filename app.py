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
    try:
        with open(image_file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return "" # Fallback if image not found

def country_to_flag(country_code):
    return "".join(chr(127397 + ord(char)) for char in country_code.upper())

# ✅ ADDED FOR PDF GENERATION ONLY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from io import BytesIO

# -----------------------------
# MongoDB Connection
# -----------------------------
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import uuid
import pytz

# MongoDB Setup
uri = "mongodb+srv://diabetes_user:Diabetes%40123@diabetescluster.oxegep6.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["diabetes_app"]
users_collection = db["registered_users"]
predictions_collection = db["predictions"]

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Diabete-X | AI Risk Engine",
    page_icon="🧬",
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
# ADVANCED UI/UX CSS INJECTION
# =====================================================
def inject_advanced_css(bg_image):
    st.markdown(f"""
    <style>
    /* Import Premium Font */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    /* Global App Styling */
    .stApp {{
        background: linear-gradient(rgba(10, 15, 30, 0.8), rgba(10, 15, 30, 0.8)), url("data:image/png;base64,{bg_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Poppins', sans-serif !important;
        color: #f8fafc;
    }}

    /* Hide Streamlit Default UI */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    /* Typography Upgrades */
    h1, h2, h3, h4, p, span {{ font-family: 'Poppins', sans-serif !important; }}
    
    .gradient-title {{
        background: -webkit-linear-gradient(45deg, #00d4ff, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem !important;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0px;
    }}

    .sub-title {{
        text-align: center;
        color: #94a3b8 !important;
        font-weight: 400;
        font-size: 1.2rem;
        margin-bottom: 30px;
        letter-spacing: 1px;
    }}

    /* ------------------------------------- */
    /* 🚀 PREMIUM DASHBOARD CARDS            */
    /* ------------------------------------- */
    .adv-card {{
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        transition: all 0.4s ease;
        margin-bottom: 25px;
    }}
    .adv-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }}

    /* ------------------------------------- */
    /* 🚀 BADGES FOR RISK/HEALTH FACTORS     */
    /* ------------------------------------- */
    .badge-risk {{
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.05));
        border-left: 5px solid #ef4444;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 12px;
        color: #fca5a5;
        font-weight: 500;
        font-size: 15px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .badge-safe {{
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.15), rgba(16, 185, 129, 0.05));
        border-left: 5px solid #10b981;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 12px;
        color: #6ee7b7;
        font-weight: 500;
        font-size: 15px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}

    /* ------------------------------------- */
    /* 🚀 ENHANCED SIDEBAR (WHITE INPUTS)    */
    /* ------------------------------------- */
    section[data-testid="stSidebar"] {{
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.08);
        padding: 20px 10px;
    }}
    
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label {{
        color: #ffffff !important;
        font-weight: 500;
    }}

    /* 🔥 PURE WHITE INPUT BOXES & DROPDOWNS 🔥 */
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background-color: #ffffff !important; 
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        transition: all 0.3s ease;
    }}
    
    /* Glowing effect on focus */
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {{
        border: 2px solid #00d4ff !important;
        box-shadow: 0 0 12px rgba(0, 212, 255, 0.4) !important;
    }}

    /* Text inside Inputs is Dark/Black */
    section[data-testid="stSidebar"] div[data-baseweb="input"] input,
    section[data-testid="stSidebar"] div[data-baseweb="select"] span {{
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }}

    /* Hide +/- Buttons on Numbers */
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {{
        -webkit-appearance: none; margin: 0;
    }}
    input[type="number"] {{ -moz-appearance: textfield; }}

    /* Slider Customization */
    div[data-baseweb="slider"] div[role="slider"] {{
        background-color: #00d4ff !important;
        border: 2px solid white !important;
        box-shadow: 0 0 10px rgba(0,212,255,0.6);
    }}

    /* ------------------------------------- */
    /* 🚀 BUTTON UPGRADES                    */
    /* ------------------------------------- */
    /* Primary Sidebar Button */
    button[kind="primary"] {{
        background: linear-gradient(135deg, #00d4ff 0%, #3b82f6 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 14px !important;
        padding: 12px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
        transition: all 0.3s ease !important;
    }}
    button[kind="primary"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.6) !important;
    }}

    /* Secondary / Download Button */
    div.stDownloadButton > button {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 14px !important;
        padding: 12px 24px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100%;
        font-family: 'Poppins', sans-serif !important;
    }}
    div.stDownloadButton > button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.6) !important;
    }}
    </style>
    """, unsafe_allow_html=True)


# =====================================================
# REGISTRATION PAGE (Glass Form)
# =====================================================
def registration_page():
    img_b64 = get_base64_image("health.png")
    inject_advanced_css(img_b64)
    
    st.markdown("""
    <style>
    div[data-testid="stForm"] {
        background: rgba(15, 23, 42, 0.5);
        backdrop-filter: blur(25px);
        border-radius: 30px;
        padding: 40px;
        width: 100%;
        max-width: 650px;
        margin: 5vh auto;
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stForm"] label { color: white !important; font-weight: 500; font-size: 15px;}
    div[data-testid="stForm"] input, div[data-testid="stForm"] textarea {
        background: #ffffff !important;
        border-radius: 12px !important;
        color: #0f172a !important;
        font-weight: 500 !important;
        border: none !important;
        padding: 12px 16px !important;
    }
    div[data-testid="stForm"] div[data-baseweb="select"] > div {
        background: #ffffff !important; border-radius: 12px !important;
    }
    div[data-testid="stForm"] div[data-baseweb="select"] span { color: #0f172a !important; font-weight: 500;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="gradient-title">Diabete-X Portal</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Secure Patient Registration & Clinical AI Engine</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("registration_form"):
            st.markdown("<h3 style='text-align:center; margin-bottom: 20px; font-weight:600;'>Patient Profile Creation</h3>", unsafe_allow_html=True)
            
            name = st.text_input("Full Name")
            country_list = [country.name for country in pycountry.countries]
            selected_country = st.selectbox("🌍 Select Country", country_list)
            
            country_obj = pycountry.countries.get(name=selected_country)
            country_code = phonenumbers.country_code_for_region(country_obj.alpha_2)

            phone = st.text_input("Mobile Number (without country code)")
            email = st.text_input("Email Address")
            address = st.text_area("Residential Address")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Access AI Engine 🚀", use_container_width=True, type="primary")

            if submit:
                name, phone, email, address = name.strip(), phone.strip(), email.strip(), address.strip()

                if not all([name, phone, email, address]):
                    st.error("⚠️ Please fill all required fields.")
                    return

                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(email_pattern, email):
                    st.error("⚠️ Invalid email address format.")
                    return
                
                region_code = country_obj.alpha_2
                try:
                    parsed_number = phonenumbers.parse(phone, region_code)
                    if not phonenumbers.is_valid_number(parsed_number):
                        st.error("⚠️ Phone number does not match selected country.")
                        return
                    formatted_phone = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
                except:
                    st.error("⚠️ Phone format parsing error.")
                    return        
                
                ist = pytz.timezone("Asia/Kolkata")
                current_time = datetime.now(ist)
                patient_id = "PTX-" + str(uuid.uuid4().int)[:6] 
               
                user_data = {
                    "_id": patient_id, "name": name, "phone": formatted_phone,
                    "country": selected_country, "email": email, "address": address,
                    "gender": "Pending", "created_at": current_time.strftime("%d-%m-%Y %I:%M %p")
                } 
                users_collection.insert_one(user_data)
                st.session_state.patient_info = user_data
                st.session_state.registered = True
                st.session_state.show_success = True
                st.rerun()

# =====================================================
# MAIN PREDICTION DASHBOARD
# =====================================================
@st.cache_resource
def load_model():
    try:
        return joblib.load("diabetes_model.pkl"), joblib.load("scaler_svm.pkl")
    except Exception as e:
        st.error(f"⚠️ Model System Offline: {e}")
        st.stop()

def prediction_page():
    model, scaler = load_model()
    if not st.session_state.patient_info:
        st.session_state.registered = False
        st.stop()

    img_b64 = get_base64_image("health22.png")
    inject_advanced_css(img_b64)
    info = st.session_state.patient_info

    # -----------------------------
    # SIDEBAR CONTROL PANEL
    # -----------------------------
    with st.sidebar:
        st.markdown(f"<h2 style='margin-bottom:0; font-weight:700; color:#00d4ff !important;'>{info.get('name')}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8; font-size:13px; margin-top:0;'>PID: {info.get('_id')}</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("<h3 style='font-size:16px; margin-bottom:15px;'>🧬 Clinical Parameters</h3>", unsafe_allow_html=True)
        age = st.number_input("Patient Age", 21, 100, 30)
        gender = st.selectbox("Biological Sex", ["Male", "Female"])
        pregnancies = st.number_input("Number of Pregnancies", 0, 20, 0) if gender == "Female" else 0
        
        st.markdown("<h3 style='font-size:16px; margin-top:15px; margin-bottom:15px;'>🩸 Vital Signs</h3>", unsafe_allow_html=True)
        glucose = st.slider("Fasting Glucose (mg/dL)", 0, 200, 120)
        bp = st.slider("Blood Pressure (mmHg)", 0, 130, 70)
        skin = st.slider("Skin Thickness (mm)", 0, 100, 20)
        insulin = st.slider("Insulin Level (IU/mL)", 0, 900, 80)
        
        st.markdown("<h3 style='font-size:16px; margin-top:15px; margin-bottom:15px;'>📏 Key Metrics</h3>", unsafe_allow_html=True)
        bmi = st.number_input("Body Mass Index (BMI)", 10.0, 70.0, 25.0)
        dpf = st.slider("Diabetes Pedigree (DPF)", 0.0, 2.5, 0.5)
        
        st.markdown("<br>", unsafe_allow_html=True)
        predict_btn = st.button("Run AI Diagnostics", use_container_width=True, type="primary")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Logout Session", use_container_width=True):
            st.session_state.registered = False
            st.session_state.patient_info = {}
            st.session_state.show_success = False
            st.rerun() 

    # -----------------------------
    # MAIN DASHBOARD UI
    # -----------------------------
    st.markdown('<h1 class="gradient-title">Diagnostic Core Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Advanced multiparametric evaluation using SVM Architecture</p>', unsafe_allow_html=True)

    if st.session_state.show_success:
        st.toast("✅ Active Session Established. Ready for inputs.", icon="🛡️")
        st.session_state.show_success = False

    # Default idle state
    if not predict_btn:
        st.markdown("""
        <div class="adv-card" style="text-align:center; padding: 80px 20px;">
            <h2 style="color: #f8fafc; font-weight: 600;">System Standby</h2>
            <p style="color:#94a3b8; font-size: 16px;">Configure the clinical parameters in the left control panel and execute the diagnostic run.</p>
        </div>
        """, unsafe_allow_html=True)

    # -----------------------------
    # DIAGNOSTIC ENGINE (ON PREDICT)
    # -----------------------------
    if predict_btn:
        if "_id" in info:
            users_collection.update_one({"_id":info["_id"]}, {"$set":{"gender":gender}}) 
         
        # Model Prediction
        input_data = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
        input_std = scaler.transform(input_data)
        prob_negative = model.predict_proba(input_std)[0][0] * 100
        prob_positive = model.predict_proba(input_std)[0][1] * 100

        # Dynamic Styling based on Risk
        if prob_positive < 30: 
            risk_label, risk_color_hex, risk_icon = "LOW RISK", "#10b981", "🟢"
            bg_gradient = "linear-gradient(135deg, rgba(16,185,129,0.2), rgba(16,185,129,0.05))"
        elif prob_positive < 70: 
            risk_label, risk_color_hex, risk_icon = "MODERATE RISK", "#f59e0b", "🟠"
            bg_gradient = "linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.05))"
        else: 
            risk_label, risk_color_hex, risk_icon = "HIGH RISK", "#ef4444", "🔴"
            bg_gradient = "linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.05))"

        # Save to DB
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)    
        prediction_data = {
            "patient_id": info["_id"], "patient_name": info["name"], "age": age, "gender": gender, 
            "glucose": glucose, "blood_pressure": bp, "bmi": bmi, "prediction": risk_label, 
            "probability": round(prob_positive, 2), "created_at": current_time.strftime("%d-%m-%Y %H:%M:%S")
        }
        predictions_collection.insert_one(prediction_data)

        # ---- 1. MASTER RESULT CARD ----
        st.markdown(f"""
        <div class="adv-card" style="background: {bg_gradient}; border-left: 6px solid {risk_color_hex};">
            <h3 style="margin-top:0; color:#cbd5e1; font-weight:500;">AI Diagnostic Conclusion</h3>
            <div style="display: flex; align-items: baseline; gap: 20px;">
                <h1 style="font-size: 50px; margin: 0; color: {risk_color_hex}; font-weight: 800;">{risk_icon} {risk_label}</h1>
                <h2 style="margin: 0; color: white; font-weight: 300;">Probability: <b style="color:{risk_color_hex};">{prob_positive:.1f}%</b></h2>
            </div>
            <p style="margin-top: 10px; color:#94a3b8;">Analysis derived from 8 distinct clinical biomarkers.</p>
        </div>
        """, unsafe_allow_html=True)

        # ---- 2. VISUALIZATION ROW ----
        col_chart1, col_chart2 = st.columns(2)
        
        # Calculate Contributions
        cause_labels, cause_values = [], []
        if glucose >= 126: cause_labels.append("Glucose"); cause_values.append(min(glucose / 2, 100))
        if bmi > 30: cause_labels.append("BMI"); cause_values.append(min(bmi * 2, 100))
        if age > 45: cause_labels.append("Age"); cause_values.append(min(age, 100))
        if bp > 120: cause_labels.append("BP"); cause_values.append(min(bp, 100))
        if dpf > 0.5: cause_labels.append("Genetics"); cause_values.append(min(dpf * 100, 100))
        if not cause_labels: cause_labels = ["Baseline"]; cause_values = [100]

        with col_chart1:
            st.markdown('<div class="adv-card">', unsafe_allow_html=True)
            st.markdown('<h3 style="text-align:center; font-size:18px;">Risk Severity Index</h3>', unsafe_allow_html=True)
            bar_fig = go.Figure(go.Bar(
                x=cause_labels, y=cause_values, text=[f"{v:.1f}" for v in cause_values], textposition='auto',
                marker=dict(color=cause_values, colorscale="Reds", line=dict(color="rgba(255,255,255,0.2)", width=1))
            ))
            bar_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), height=280, margin=dict(l=10, r=10, t=10, b=10))
            bar_fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
            st.plotly_chart(bar_fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

        with col_chart2:
            st.markdown('<div class="adv-card">', unsafe_allow_html=True)
            st.markdown('<h3 style="text-align:center; font-size:18px;">Etiology Distribution</h3>', unsafe_allow_html=True)
            pie_fig = go.Figure(data=[go.Pie(labels=cause_labels, values=cause_values, hole=0.55, marker=dict(colors=['#ef4444', '#f97316', '#3b82f6', '#8b5cf6', '#eab308']))])
            pie_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), height=280, margin=dict(l=10, r=10, t=10, b=10))
            pie_fig.update_traces(hoverinfo='label+percent', textinfo='percent', textfont_size=14)
            st.plotly_chart(pie_fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

        # ---- 3. CLINICAL INSIGHTS ROW ----
        col_risk, col_safe = st.columns(2)
        
        risk_factors, positive_factors = [], []
        if glucose >= 126: risk_factors.append("Critical Hyperglycemia (≥126 mg/dL)")
        elif 100 <= glucose < 126: risk_factors.append("Prediabetic Fasting Glucose")
        else: positive_factors.append("Optimal Fasting Glucose")    
        if bmi > 30: risk_factors.append("Obesity Range Detected")
        elif 18.5 <= bmi <= 24.9: positive_factors.append("Optimal Body Mass Index")
        if age > 45: risk_factors.append("Age-related Risk Factor")
        if bp > 120: risk_factors.append("Elevated Blood Pressure")
        elif 90 <= bp <= 120: positive_factors.append("Normotensive Status")
        if dpf > 0.5: risk_factors.append("High Genetic Predisposition")

        with col_risk:
            st.markdown('<div class="adv-card" style="height: 100%;">', unsafe_allow_html=True)
            st.markdown('<h3 style="color: #fca5a5; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">⚠️ Highlighted Risk Vectors</h3>', unsafe_allow_html=True)
            if risk_factors:
                for factor in risk_factors: st.markdown(f'<div class="badge-risk">{factor}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#94a3b8; font-style:italic;">No critical risk vectors identified in current data.</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_safe:
            st.markdown('<div class="adv-card" style="height: 100%;">', unsafe_allow_html=True)
            st.markdown('<h3 style="color: #6ee7b7; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">🛡️ Protective Health Indicators</h3>', unsafe_allow_html=True)
            if positive_factors:
                for factor in positive_factors: st.markdown(f'<div class="badge-safe">{factor}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#94a3b8; font-style:italic;">No definitive protective factors identified.</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Medical Recommendations Array (For PDF)
        if prob_positive >= 70: recs_for_pdf = ["Consult an endocrinologist immediately", "Schedule HbA1c and lipid profile tests", "Initiate strict dietary modifications", "Monitor daily blood glucose metrics"]
        elif prob_positive >= 30: recs_for_pdf = ["Adopt a low-glycemic index diet", "Integrate daily cardiovascular exercise", "Schedule follow-up screening in 3 months"]
        else: recs_for_pdf = ["Maintain current baseline health routines", "Continue regular physical activity", "Annual routine health check-up"]

        # -----------------------------
        # PDF GENERATION SYSTEM
        # -----------------------------
        with st.spinner("Generating High-Resolution Clinical PDF..."):
            try:
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                elements, styles = [], getSampleStyleSheet()

                title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=22, textColor=colors.HexColor("#0f172a"), alignment=1, spaceAfter=5, fontName="Helvetica-Bold")
                date_style = ParagraphStyle("DateStyle", parent=styles["Normal"], fontSize=10, textColor=colors.dimgrey, alignment=1, spaceAfter=25, fontName="Helvetica-Oblique")
                heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#005bea"), spaceBefore=15, spaceAfter=12, fontName="Helvetica-Bold", borderPadding=6, backColor=colors.HexColor("#f8fafc"))
                normal_style = styles["Normal"]
                normal_style.fontSize = 11
                normal_style.spaceAfter = 6
                
                # Title
                elements.append(Paragraph("🩺 CLINICAL RISK ASSESSMENT REPORT", title_style))
                elements.append(Paragraph(f"Generated via AI Engine On: {current_time.strftime('%d %B %Y | %I:%M %p (IST)')}", date_style))

                # Profile Table
                addr_para = Paragraph(info.get("address", "N/A"), ParagraphStyle("Addr", parent=styles["Normal"], fontSize=11, leading=14))
                patient_table = [
                    ["Patient ID", info.get("_id", "N/A")], ["Full Name", info.get("name", "N/A")],
                    ["Email Contact", info.get("email", "N/A")], ["Phone Contact", info.get("phone", "N/A")],
                    ["Country", info.get("country", "N/A")], ["Registered Addr.", addr_para]
                ]
                t1 = Table(patient_table, colWidths=[2.2*inch, 4.3*inch])
                t1.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey), ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f1f5f9")), ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("PADDING", (0,0), (-1,-1), 8), ("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
                elements.append(Paragraph("Patient Demographics", heading_style))
                elements.append(t1)
                
                # Clinical Table
                medical_inputs = [
                    ["Age", f"{age} Years"], ["Biological Sex", gender], ["Fasting Glucose", f"{glucose} mg/dL"],
                    ["Diastolic BP", f"{bp} mmHg"], ["Triceps Fold", f"{skin} mm"], ["Serum Insulin", f"{insulin} IU/mL"],
                    ["BMI", str(bmi)], ["DPF Rating", str(dpf)]
                ]
                if gender == "Female": medical_inputs.insert(2, ["Pregnancies", str(pregnancies)])
                
                t2 = Table(medical_inputs, colWidths=[2.2*inch, 4.3*inch])
                t2.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey), ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f1f5f9")), ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("PADDING", (0,0), (-1,-1), 8), ("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
                elements.append(Paragraph("Clinical Biomarkers", heading_style))
                elements.append(t2)

                # Result Conclusion
                elements.append(Paragraph("Diagnostic Conclusion", heading_style))
                elements.append(Paragraph(f"<b>Overall Classification:</b> <font color='{risk_color_hex}'>{risk_label}</font>", normal_style))
                elements.append(Paragraph(f"<b>Computed Pathological Risk:</b> {prob_positive:.1f}%", normal_style))
                elements.append(Spacer(1, 0.2 * inch))

                # Chart Export (PDF specific styling)
                try:
                    time.sleep(1) # Crucial for kaleido stability
                    bar_pdf = go.Figure(bar_fig); bar_pdf.update_layout(font=dict(color="black"), paper_bgcolor="white", plot_bgcolor="white", title="Risk Severity")
                    bar_pdf.update_traces(marker=dict(line=dict(color="black", width=1)))
                    bar_pdf.update_xaxes(tickfont=dict(color="black"), linecolor="black")
                    bar_pdf.update_yaxes(tickfont=dict(color="black"), gridcolor="lightgrey")
                    
                    pie_pdf = go.Figure(pie_fig); pie_pdf.update_layout(font=dict(color="black"), paper_bgcolor="white", title="Etiology Contribution")

                    bar_img = bar_pdf.to_image(format="png", engine="kaleido", width=350, height=280, scale=2)
                    pie_img = pie_pdf.to_image(format="png", engine="kaleido", width=350, height=280, scale=2)
                    
                    elements.append(Paragraph("Analytical Visualizations", heading_style))
                    c_table = Table([[RLImage(BytesIO(bar_img), width=3.1*inch, height=2.4*inch), RLImage(BytesIO(pie_img), width=3.1*inch, height=2.4*inch)]], colWidths=[3.2*inch, 3.2*inch])
                    c_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")), ('BOTTOMPADDING', (0,0), (-1,-1), 10)]))
                    elements.append(c_table)
                except Exception as e:
                    elements.append(Paragraph("<font color='red'><i>Visualizations omitted: Kaleido engine unavailable.</i></font>", normal_style))

                elements.append(Spacer(1, 0.1 * inch))
                elements.append(Paragraph("Clinical Recommendations", heading_style))
                elements.append(ListFlowable([ListItem(Paragraph(r, normal_style)) for r in recs_for_pdf], bulletType='bullet'))
                elements.append(Spacer(1, 0.4 * inch))
                elements.append(Paragraph("<b>Disclaimer:</b> This document is generated by a predictive algorithm and should be reviewed by a certified medical practitioner.", styles["Italic"]))

                doc.build(elements)
                pdf = buffer.getvalue()
                buffer.close()

                # Render Download Button
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    label="📄 Export Certified Clinical PDF",
                    data=pdf,
                    file_name=f"Clinical_Report_{info.get('name', 'Patient')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error("Document Generation Failed.")

        st.markdown("<br><hr style='border-color: rgba(255,255,255,0.1);'><p style='text-align:center; color:#64748b; font-size:12px;'>Diabete-X AI Engine v2.0 | Not for self-diagnosis</p>", unsafe_allow_html=True)

# =====================================================
# App Routing
# =====================================================
if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
