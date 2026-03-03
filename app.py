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
import time # Added for Kaleido stability

def get_base64_image(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

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

#  my string
uri = "mongodb+srv://diabetes_user:Diabetes%40123@diabetescluster.oxegep6.mongodb.net/?retryWrites=true&w=majority"

# Create MongoDB Client
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["diabetes_app"]
users_collection = db["registered_users"]
predictions_collection = db["predictions"]

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Diabete-X | Premium Risk Assessment",
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
# GLOBAL HIGH-END CSS INJECTION
# =====================================================
def inject_premium_css(img_b64):
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global App Styling */
    .stApp {{
        background: linear-gradient(rgba(10, 15, 30, 0.75), rgba(10, 15, 30, 0.75)), url("data:image/png;base64,{img_b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
    }}

    /* Hiding Streamlit Branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    /* Premium Custom Cards */
    .premium-card {{
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 30px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 25px;
    }}
    .premium-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}

    /* Risk Factor Badges */
    .risk-badge {{
        background: rgba(239, 68, 68, 0.15);
        border-left: 4px solid #ef4444;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-weight: 500;
        color: #fca5a5;
        display: flex;
        align-items: center;
    }}
    .safe-badge {{
        background: rgba(16, 185, 129, 0.15);
        border-left: 4px solid #10b981;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-weight: 500;
        color: #6ee7b7;
        display: flex;
        align-items: center;
    }}

    /* Elegant Typography */
    h1, h2, h3, h4 {{
        font-family: 'Inter', sans-serif !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }}
    .main-title {{
        background: -webkit-linear-gradient(45deg, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        text-align: center;
        margin-bottom: 10px;
    }}

    /* Sidebar Ultra-Modern Styling */
    section[data-testid="stSidebar"] {{
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border-right: 1px solid rgba(255,255,255,0.08);
        padding: 20px 15px;
    }}
    
    /* 🔥 EXACT FIX: White Inputs in Sidebar 🔥 */
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background-color: #f8fafc !important; /* Pure light gray/white */
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important; /* Dark text */
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {{
        border: 2px solid #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3) !important;
    }}
    
    /* Text color inside input boxes */
    section[data-testid="stSidebar"] div[data-baseweb="input"] input {{
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }}
    /* Dropdown text color */
    section[data-testid="stSidebar"] div[data-baseweb="select"] span {{
        color: #0f172a !important;
        font-weight: 600 !important;
    }}

    /* Hide Number Input +/- Buttons completely */
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {{
        -webkit-appearance: none; margin: 0;
    }}
    input[type="number"] {{ -moz-appearance: textfield; }}

    /* Sidebar Sliders Theme */
    div[data-baseweb="slider"] div[data-testid="stTickBar"] {{ display: none; }}
    div[data-baseweb="slider"] div[role="slider"] {{
        background-color: #3b82f6 !important;
        border: 2px solid white !important;
        box-shadow: 0 0 10px rgba(59,130,246,0.8);
    }}

    /* Primary Action Buttons */
    button[kind="primary"] {{
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 12px 0px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
        transition: all 0.3s ease !important;
    }}
    button[kind="primary"]:hover {{
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.6) !important;
    }}

    /* Download Button Specific */
    div.stDownloadButton > button {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
        transition: transform 0.3s ease !important;
        width: 100%;
    }}
    div.stDownloadButton > button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.6) !important;
    }}
    
    /* Metrics Styling */
    div[data-testid="metric-container"] {{
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
    </style>
    """, unsafe_allow_html=True)


# =====================================================
# REGISTRATION PAGE (Redesigned)
# =====================================================
def registration_page():
    img_b64 = get_base64_image("health.png")
    inject_premium_css(img_b64)
    
    # Registration Specific Centered Glass Form
    st.markdown("""
    <style>
    div[data-testid="stForm"] {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(25px);
        border-radius: 30px;
        padding: 50px 40px;
        width: 100%;
        max-width: 600px;
        margin: 6vh auto;
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stForm"] label { color: white !important; font-weight: 600; margin-bottom: 5px; }
    div[data-testid="stForm"] input, div[data-testid="stForm"] textarea {
        background: rgba(255,255,255,0.9) !important;
        border-radius: 12px !important;
        color: black !important;
        border: none !important;
        padding: 14px 16px !important;
    }
    div[data-testid="stForm"] div[data-baseweb="select"] > div {
        background: rgba(255,255,255,0.9) !important;
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-title">Diabete-X Portal</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 1.1rem; margin-bottom: 2rem;'>Secure Patient Registration & Clinical Assessment</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("registration_form"):
            st.markdown("<h3 style='text-align:center; margin-bottom: 20px;'>Patient Details</h3>", unsafe_allow_html=True)
            
            name = st.text_input("Full Name")
            country_list = [country.name for country in pycountry.countries]
            selected_country = st.selectbox("🌍 Select Country", country_list)
            
            country_obj = pycountry.countries.get(name=selected_country)
            country_code = phonenumbers.country_code_for_region(country_obj.alpha_2)

            phone = st.text_input("Mobile Number (Local format)")
            email = st.text_input("Email Address")
            address = st.text_area("Residential Address")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Access Clinical System", use_container_width=True, type="primary")

            if submit:
                name, phone, email, address = name.strip(), phone.strip(), email.strip(), address.strip()

                if not all([name, phone, email, address]):
                    st.error("⚠️ Please complete all fields to proceed.")
                    return

                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(email_pattern, email):
                    st.error("⚠️ Invalid email format provided.")
                    return
                
                region_code = country_obj.alpha_2
                try:
                    parsed_number = phonenumbers.parse(phone, region_code)
                    if not phonenumbers.is_valid_number(parsed_number):
                        st.error("⚠️ Phone number does not match selected country format.")
                        return
                    formatted_phone = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
                except:
                    st.error("⚠️ Critical error parsing phone number.")
                    return        
                
                ist = pytz.timezone("Asia/Kolkata")
                current_time = datetime.now(ist)
                patient_id = "PTX-" + str(uuid.uuid4().int)[:6] # Sleek ID format
               
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
# MAIN PREDICTION PAGE (Dashboard Design)
# =====================================================
@st.cache_resource
def load_model():
    try:
        return joblib.load("diabetes_model.pkl"), joblib.load("scaler_svm.pkl")
    except Exception as e:
        st.error(f"⚠️ Core System Failure: Unable to load AI models. {e}")
        st.stop()

def prediction_page():
    model, scaler = load_model()
    if not st.session_state.patient_info:
        st.session_state.registered = False
        st.stop()

    img_b64 = get_base64_image("health22.png")
    inject_premium_css(img_b64)
    info = st.session_state.patient_info

    # -----------------------------
    # HIGH-END SIDEBAR
    # -----------------------------
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3002/3002622.png", width=60) # Elegant icon
        st.markdown(f"<h2 style='margin-bottom:0;'>{info.get('name')}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8; font-size:14px; margin-top:0;'>ID: {info.get('_id')}</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("### 🧬 Clinical Parameters")
        age = st.number_input("Patient Age (Years)", 21, 100, 30)
        gender = st.selectbox("Biological Sex", ["Male", "Female"])
        pregnancies = st.number_input("Previous Pregnancies", 0, 20, 0) if gender == "Female" else 0
        
        st.markdown("<br><p style='font-size:14px; font-weight:bold; color:#cbd5e1; margin-bottom:-10px;'>Vitals Entry</p>", unsafe_allow_html=True)
        glucose = st.slider("Fasting Glucose (mg/dL)", 0, 200, 120)
        bp = st.slider("Diastolic Blood Pressure (mmHg)", 0, 130, 70)
        skin = st.slider("Triceps Skin Fold (mm)", 0, 100, 20)
        insulin = st.slider("2-Hour Serum Insulin (IU/mL)", 0, 900, 80)
        
        st.markdown("<br><p style='font-size:14px; font-weight:bold; color:#cbd5e1; margin-bottom:-10px;'>Metrics</p>", unsafe_allow_html=True)
        bmi = st.number_input("Body Mass Index (BMI)", 10.0, 70.0, 25.0)
        dpf = st.slider("Diabetes Pedigree Function", 0.0, 2.5, 0.5)
        
        st.markdown("<br>", unsafe_allow_html=True)
        predict_btn = st.button("Generate AI Assessment", use_container_width=True, type="primary")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🔒 Secure Logout", use_container_width=True):
            st.session_state.registered = False
            st.session_state.patient_info = {}
            st.session_state.show_success = False
            st.rerun() 

    # -----------------------------
    # MAIN DASHBOARD AREA
    # -----------------------------
    st.markdown('<h1 class="main-title">Diagnostic AI Engine</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 1.1rem; margin-bottom: 2rem;'>Real-time multiparametric risk evaluation using Support Vector Diagnostics</p>", unsafe_allow_html=True)

    if st.session_state.show_success:
        st.toast("✅ Secure Session Established. Patient data loaded.", icon="🔒")
        st.session_state.show_success = False

    # Default Intro view before predicting
    if not predict_btn:
        st.markdown("""
        <div class="premium-card" style="text-align:center; padding: 60px 20px;">
            <img src="https://cdn-icons-png.flaticon.com/512/2817/2817645.png" width="100" style="margin-bottom:20px; opacity:0.8;">
            <h2>System Ready for Assessment</h2>
            <p style="color:#94a3b8; font-size: 18px;">Please configure the patient's clinical parameters in the left panel and initiate the AI generation process.</p>
        </div>
        """, unsafe_allow_html=True)

    # -----------------------------
    # PREDICTION EXECUTION
    # -----------------------------
    if predict_btn:
        if "_id" in info:
            users_collection.update_one({"_id":info["_id"]}, {"$set":{"gender":gender}}) 
         
        # Run Model
        input_data = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
        input_std = scaler.transform(input_data)
        prob_negative = model.predict_proba(input_std)[0][0] * 100
        prob_positive = model.predict_proba(input_std)[0][1] * 100

        if prob_positive < 30: risk_label, risk_color, risk_hex = "LOW RISK", "green", "#10b981"
        elif prob_positive < 70: risk_label, risk_color, risk_hex = "MODERATE RISK", "orange", "#f59e0b"
        else: risk_label, risk_color, risk_hex = "HIGH RISK", "red", "#ef4444"

        # DB Save
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)    
        prediction_data = {
            "patient_id": info["_id"], "patient_name": info["name"], "age": age, "gender": gender, 
            "glucose": glucose, "blood_pressure": bp, "bmi": bmi, "prediction": risk_label, 
            "probability": round(prob_positive, 2), "created_at": current_time.strftime("%d-%m-%Y %H:%M:%S")
        }
        predictions_collection.insert_one(prediction_data)

        # ---- TOP RESULTS BANNER ----
        st.markdown(f"""
        <div class="premium-card" style="border-left: 8px solid {risk_hex};">
            <h2 style="margin-top:0; font-size:24px; color:#cbd5e1;">Diagnostic Output</h2>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h1 style="font-size: 48px; margin:0; color:{risk_hex};">{risk_label}</h1>
                    <p style="font-size: 18px; margin:0; color:#94a3b8;">Probability of Type 2 Diabetes: <b>{prob_positive:.1f}%</b></p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---- GRAPHS ROW ----
        col_g1, col_g2 = st.columns([1, 1])
        
        # Determine top causes dynamically
        cause_labels, cause_values = [], []
        if glucose >= 126: cause_labels.append("Hyperglycemia"); cause_values.append(min(glucose / 2, 100))
        if bmi > 30: cause_labels.append("Obesity (BMI)"); cause_values.append(min(bmi * 2, 100))
        if age > 45: cause_labels.append("Age Factor"); cause_values.append(min(age, 100))
        if bp > 120: cause_labels.append("Hypertension"); cause_values.append(min(bp, 100))
        if dpf > 0.5: cause_labels.append("Genetics (DPF)"); cause_values.append(min(dpf * 100, 100))
        if not cause_labels: cause_labels = ["Baseline Indicators"]; cause_values = [100]

        with col_g1:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown('<h3>Risk Gauge Analysis</h3>', unsafe_allow_html=True)
            gauge_fig = go.Figure(go.Indicator(
                mode="gauge+number", value=prob_positive, number={"suffix": "%", "font":{"color":"white"}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 2, "tickcolor": "white"},
                    "bar": {"color": "rgba(255,255,255,0.5)"},
                    "steps": [{"range": [0, 30], "color": "#10b981"}, {"range": [30, 70], "color": "#f59e0b"}, {"range": [70, 100], "color": "#ef4444"}]
                }
            ))
            gauge_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), height=250, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(gauge_fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_g2:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown('<h3>Etiology Breakdown</h3>', unsafe_allow_html=True)
            pie_fig = go.Figure(data=[go.Pie(labels=cause_labels, values=cause_values, hole=0.5, marker_colors=['#ef4444', '#f97316', '#eab308', '#3b82f6', '#8b5cf6'])])
            pie_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), height=250, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
            pie_fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(pie_fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ---- CLINICAL INSIGHTS ROW ----
        st.markdown('<h2 style="margin-top:20px;">Clinical Insights</h2>', unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        
        risk_factors, positive_factors = [], []
        if glucose >= 126: risk_factors.append("Critical Hyperglycemia (≥126 mg/dL)")
        elif 100 <= glucose < 126: risk_factors.append("Prediabetic Glucose (100–125 mg/dL)")
        else: positive_factors.append("Optimal Fasting Glucose (<100 mg/dL)")    
        if bmi > 30: risk_factors.append("Obesity Detected (BMI > 30)")
        elif 18.5 <= bmi <= 24.9: positive_factors.append("Optimal Body Mass Index")
        if age > 45: risk_factors.append("Age-related Risk Escalation")
        if bp > 120: risk_factors.append("Elevated Blood Pressure (>120 mmHg)")
        elif 90 <= bp <= 120: positive_factors.append("Normotensive Blood Pressure")
        if dpf > 0.5: risk_factors.append("Significant Genetic Predisposition")

        with col_c1:
            st.markdown('<div class="premium-card" style="height: 100%;">', unsafe_allow_html=True)
            st.markdown('<h3 style="color:#fca5a5;">⚠️ Identified Risk Vectors</h3>', unsafe_allow_html=True)
            if risk_factors:
                for factor in risk_factors:
                    st.markdown(f'<div class="risk-badge">🚨 {factor}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#94a3b8;">No critical risk vectors detected.</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_c2:
            st.markdown('<div class="premium-card" style="height: 100%;">', unsafe_allow_html=True)
            st.markdown('<h3 style="color:#6ee7b7;">🛡️ Protective Indicators</h3>', unsafe_allow_html=True)
            if positive_factors:
                for factor in positive_factors:
                    st.markdown(f'<div class="safe-badge">✅ {factor}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#94a3b8;">No optimal protective factors highlighted.</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # For PDF Logic (Hidden Bar Chart Generation)
        bar_fig = go.Figure(go.Bar(x=cause_labels, y=cause_values, marker=dict(color=cause_values, colorscale="Reds")))
        bar_fig.update_layout(title="Risk Severity", paper_bgcolor="white", font=dict(color="black"))
        pie_pdf = go.Figure(data=[go.Pie(labels=cause_labels, values=cause_values, hole=0.4)])
        pie_pdf.update_layout(title="Contribution", paper_bgcolor="white", font=dict(color="black"))

        # -----------------------------
        # PDF GENERATION (Keep Aesthetic Logic)
        # -----------------------------
        st.markdown('<br>', unsafe_allow_html=True)
        with st.spinner("Compiling Professional Medical Report..."):
            try:
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                elements = []
                styles = getSampleStyleSheet()

                title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#0f172a"), alignment=1, spaceAfter=5, fontName="Helvetica-Bold")
                date_style = ParagraphStyle("DateStyle", parent=styles["Normal"], fontSize=10, textColor=colors.dimgrey, alignment=1, spaceAfter=20, fontName="Helvetica-Oblique")
                heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#3b82f6"), spaceBefore=15, spaceAfter=10, fontName="Helvetica-Bold", borderPadding=6, backColor=colors.HexColor("#f8fafc"))
                normal_style = styles["Normal"]
                normal_style.fontSize = 11
                normal_style.spaceAfter = 6
                
                elements.append(Paragraph("🩺 DIABETES RISK PREDICTION REPORT", title_style))
                elements.append(Paragraph(f"Report Generated On: {current_time.strftime('%d %B %Y | %I:%M %p (IST)')}", date_style))

                address_style = ParagraphStyle("AddressStyle", parent=styles["Normal"], fontSize=11, leading=14)
                address_paragraph = Paragraph(info.get("address", "N/A"), address_style)
                
                patient_table = [
                    ["Patient ID", info.get("_id", "N/A")], ["Full Name", info.get("name", "N/A")],
                    ["Email", info.get("email", "N/A")], ["Phone", info.get("phone", "N/A")],
                    ["Country", info.get("country", "N/A")], ["Address", address_paragraph]
                ]
                t1 = Table(patient_table, colWidths=[2.2*inch, 4.3*inch])
                t1.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey), ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f1f5f9")), ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("PADDING", (0,0), (-1,-1), 8), ("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
                elements.append(Paragraph("Patient Profile", heading_style))
                elements.append(t1)
                elements.append(Spacer(1, 0.1 * inch))

                medical_inputs = [
                    ["Age", f"{age} Yrs"], ["Gender", gender], ["Fasting Glucose", f"{glucose} mg/dL"],
                    ["Blood Pressure", f"{bp} mmHg"], ["Skin Thickness", f"{skin} mm"], ["Insulin Level", f"{insulin} IU/mL"],
                    ["BMI", str(bmi)], ["Diabetes Pedigree", str(dpf)]
                ]
                if gender == "Female": medical_inputs.insert(2, ["Pregnancies", str(pregnancies)])

                t2 = Table(medical_inputs, colWidths=[2.2*inch, 4.3*inch])
                t2.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey), ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f1f5f9")), ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("PADDING", (0,0), (-1,-1), 8), ("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
                elements.append(Paragraph("Clinical Inputs", heading_style))
                elements.append(t2)
                elements.append(Spacer(1, 0.1 * inch))

                elements.append(Paragraph("Diagnostic Result", heading_style))
                elements.append(Paragraph(f"<b>Overall Risk Classification:</b> <font color='{risk_hex}'>{risk_label}</font>", normal_style))
                elements.append(Paragraph(f"<b>Computed AI Probability:</b> {prob_positive:.1f}%", normal_style))
                elements.append(Spacer(1, 0.2 * inch))

                # Kaleido Image Gen
                try:
                    time.sleep(1) 
                    bar_img_bytes = bar_fig.to_image(format="png", engine="kaleido", width=350, height=280, scale=2)
                    pie_img_bytes = pie_pdf.to_image(format="png", engine="kaleido", width=350, height=280, scale=2)
                    elements.append(Paragraph("Data Visualization", heading_style))
                    chart_table = Table([[RLImage(BytesIO(bar_img_bytes), width=3*inch, height=2.3*inch), RLImage(BytesIO(pie_img_bytes), width=3*inch, height=2.3*inch)]], colWidths=[3.2*inch, 3.2*inch])
                    chart_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#e2e8f0")), ('BOTTOMPADDING', (0,0), (-1,-1), 15), ('TOPPADDING', (0,0), (-1,-1), 10)]))
                    elements.append(chart_table)
                except Exception as e:
                    pass

                elements.append(Spacer(1, 0.2 * inch))
                elements.append(Paragraph("<b>Medical Disclaimer:</b> This diagnostic report is generated by an Artificial Intelligence engine and does not substitute professional medical consultation.", styles["Italic"]))

                doc.build(elements)
                pdf = buffer.getvalue()
                buffer.close()
                
                # Render Premium Download Button
                st.download_button(
                    label="📄 Download Certified Clinical Report (PDF)",
                    data=pdf,
                    file_name=f"DiabeteX_Report_{info.get('name', 'Patient')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Failed to compile PDF. Ensure libraries are correct. Error: {e}")

# =====================================================
# Navigation Engine
# =====================================================
if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
