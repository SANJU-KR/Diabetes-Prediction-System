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

# Create Database
db = client["diabetes_app"]

# Create Collection
users_collection = db["registered_users"]
predictions_collection = db["predictions"]


# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Diabetes Prediction System",
    page_icon="🩺",
    layout="wide"
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
# REGISTRATION PAGE
# =====================================================
def registration_page():
    img = get_base64_image("health.png")   #image name

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Clinical Healthcare Reset */
    html, body, [class*="st-"] {{
        font-family: 'Inter', sans-serif !important;
    }}
    
    .stApp {{
        /* Deep Medical Navy Overlay to give a pristine, sterile but welcoming hospital vibe */
        background: linear-gradient(rgba(10, 25, 47, 0.92), rgba(6, 15, 28, 0.96)),
                    url("data:image/jpg;base64,{img}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* Center the form - Medical Chart Style */
    div[data-testid="stForm"] {{
        background-color: #0f172a; /* Deep clinical blue */
        border-radius: 12px;
        padding: 48px;
        width: 100%;
        max-width: 650px;
        margin: 6vh auto;
        border: 1px solid #1e293b;
        border-top: 4px solid #0ea5e9; /* Medical Blue Top Accent */
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }}

    h1 {{
        color: #f8fafc !important;
        text-align: center;
        font-weight: 700;
        font-size: 34px;
        margin-bottom: 8px;
    }}

    .stMarkdown p {{
        color: #94a3b8 !important;
        text-align: center;
        font-size: 16px;
        font-weight: 400;
        margin-bottom: 24px;
    }}

    /* Inputs - Clean, precise like medical equipment */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {{
        background-color: #1e293b !important;
        border-radius: 6px !important;
        border: 1px solid #334155 !important;
        transition: all 0.2s ease;
    }}

    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {{
        border-color: #0ea5e9 !important; /* Medical Cyan */
        box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15) !important;
    }}

    input, textarea {{
        color: #f8fafc !important;
        font-weight: 500 !important;
        padding: 12px !important;
    }}

    label {{
        color: #cbd5e1 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }}

    input::placeholder, textarea::placeholder {{
        color: #475569 !important;
    }}

    div[data-baseweb="select"] span {{
        color: #f8fafc !important;
    }}

    /* Register Button - Trustworthy Teal/Blue */
    div[data-testid="stForm"] button {{
        background-color: #0ea5e9 !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        height: 48px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.2s ease;
        margin-top: 16px !important;
        width: 100% !important;
    }}

    div[data-testid="stForm"] button:hover {{
        background-color: #0284c7 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
<style>
@media (max-width: 768px) {
    div[data-testid="stForm"] {
        padding: 24px !important;
        margin-top: 16px !important;
    }
}   
</style>
""", unsafe_allow_html=True)
    
    st.title("📝 Patient Registration")
    st.markdown("Please register to access the Diabetes Prediction System")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
       with st.form("registration_form"):
        name = st.text_input("Full Name")
        
        # 🌍 Country Selection with Flag
        country_list = [country.name for country in pycountry.countries]
        selected_country = st.selectbox("🌍 Select Country", country_list)

        # Extract country name
        country_obj = pycountry.countries.get(name=selected_country)
        country_code = phonenumbers.country_code_for_region(country_obj.alpha_2)

        phone = st.text_input("Enter Phone Number (without country code)")
        email = st.text_input("Email Address")
        address = st.text_area("Address")
        submit = st.form_submit_button("Register")

        if submit:
         # Clean Inputs
         name = name.strip()
         phone = phone.strip()
         email = email.strip()
         address = address.strip()

         if not name or not phone or not email or not address:
            st.error("❌ Please fill all fields properly")
            return

         # Email Validation
         email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
         if not re.match(email_pattern, email):
            st.error("❌ Please enter a valid email address")
            return
            
         # Country & Phone Validation
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
            
         # Create Patient Record
         ist = pytz.timezone("Asia/Kolkata")
         current_time = datetime.now(ist)
         patient_id = "PAT" + str(uuid.uuid4().int)[:6]
                
         user_data ={
            "_id": patient_id,
            "name": name,
            "phone": formatted_phone,
            "country": selected_country,
            "email": email,
            "address": address,
            "gender": "Not Selected",
            "created_at": current_time.strftime("%d-%m-%Y %I:%M:%S %p")
         } 
                
         users_collection.insert_one(user_data)
         st.session_state.patient_info=user_data
                
         st.session_state.registered = True
         st.session_state.show_success = True
         st.success("Registered Successfully")   
         st.rerun()

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

       # Background Image for Prediction Page
       img = get_base64_image("health22.png")  # your image name
       st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="st-"] {{
            font-family: 'Inter', sans-serif !important;
        }}
        
        .stApp {{
            /* Clinical Deep Navy Gradient */
            background: linear-gradient(rgba(10, 25, 47, 0.95), rgba(6, 15, 28, 0.98)), url("data:image/png;base64,{img}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
      """, unsafe_allow_html=True)
  
       st.markdown("""
        <style>
     h1, h2, h3 { color: #f8fafc !important; font-weight: 700 !important; }
     p, li { color: #cbd5e1 !important; font-size: 16px; }
     
     /* Clinical Dashboard Cards */
     div[data-testid="metric-container"] {
         background-color: #0f172a;
         border: 1px solid #1e293b;
         border-left: 4px solid #0ea5e9; /* Signature Medical Blue */
         border-radius: 8px;
         padding: 16px;
     }
     [data-testid="stMetricValue"] {
         font-size: 2.2rem !important;
         color: #ffffff !important;
     }
     [data-testid="stMetricLabel"] {
         color: #94a3b8 !important;
         text-transform: uppercase;
     }
     </style>
    """, unsafe_allow_html=True)
       
    # -----------------------------
    # PROFESSIONAL SIDEBAR
    # -----------------------------
       st.markdown("""
        <style>
        section[data-testid="stSidebar"] {
            background-color: #060f1c !important; 
            border-right: 1px solid #1e293b !important;
            padding: 24px 16px;
        }
        
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #0ea5e9 !important; /* Medical Cyan Headings */
            font-size: 1.1rem;
            margin-bottom: 16px;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 8px;
        }
        
        section[data-testid="stSidebar"] label { color: #94a3b8 !important; font-size: 13px !important; }
        section[data-testid="stSidebar"] p { color: #cbd5e1 !important; font-size: 14px; }

        section[data-testid="stSidebar"] button {
            background-color: #1e293b !important;
            border-radius: 6px !important;
            border: 1px solid #334155 !important;
            color: #f8fafc !important;
            font-weight: 500 !important;
            height: 40px !important;
        }
        section[data-testid="stSidebar"] button:hover { 
            background-color: #0ea5e9 !important;
            border-color: #0ea5e9 !important;
        }
       </style>
       """, unsafe_allow_html=True)

       st.markdown("""
<style>
/* Clean Dropdown */
div[data-baseweb="popover"] { background-color: #0f172a !important; border: 1px solid #1e293b; }
li[role="option"] { color: #cbd5e1 !important; }
li[role="option"]:hover { background-color: #1e293b !important; color: #f8fafc !important; }

/* Sidebar Inputs */
section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #0f172a !important; 
    border-radius: 6px !important;
    border: 1px solid #1e293b !important;
}
section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {
    border-color: #0ea5e9 !important;
}
section[data-testid="stSidebar"] div[data-baseweb="input"] input { color: #f8fafc !important; }

/* Clinical Slider - Medical Blue */
.stSlider [data-baseweb="slider"] div[data-testid="stTickBar"] { display: none; }
.stSlider div[data-baseweb="slider"] div[role="slider"] {
    background-color: #0ea5e9 !important;
    box-shadow: 0 0 0 2px #060f1c; 
}

/* Hide Spinners */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none; margin: 0;
}
input[type="number"] { -moz-appearance: textfield; }
</style>
""", unsafe_allow_html=True) 
       
       st.markdown("""
<style>
/* Enterprise Download Button */
div.stDownloadButton > button {
    background-color: #f8fafc !important; 
    color: #0f172a !important;
    font-weight: 600 !important; 
    border-radius: 6px !important;
    border: 1px solid #e2e8f0 !important;
}
div.stDownloadButton > button:hover {
    background-color: #0ea5e9 !important; 
    color: #ffffff !important;
    border-color: #0ea5e9 !important;
}

/* SOLID MEDICAL DASHBOARD CARD */
.glass-box {
    background-color: #0f172a; 
    border-radius: 12px;
    padding: 32px; 
    border: 1px solid #1e293b;
    border-top: 4px solid #3b82f6; /* Accent color for charts box */
    margin-bottom: 32px;
}

/* Standardized Medical Alerts */
.stAlert { border-radius: 6px !important; border: none !important; }
.stSuccess { background-color: rgba(16, 185, 129, 0.15) !important; color: #34d399 !important; border-left: 4px solid #10b981 !important; }
.stWarning { background-color: rgba(245, 158, 11, 0.15) !important; color: #fbbf24 !important; border-left: 4px solid #f59e0b !important; }
.stError { background-color: rgba(225, 29, 72, 0.15) !important; color: #fb7185 !important; border-left: 4px solid #e11d48 !important; }

@media (max-width: 992px) { section[data-testid="stSidebar"] { width: 100% !important; } }
</style>
""", unsafe_allow_html=True)

    # -----------------------------
    # Sidebar
    # -----------------------------
       st.sidebar.markdown("# Patient Profile")
       info = st.session_state.patient_info

       st.sidebar.markdown(f"**Name:** {info.get('name','')}")
       st.sidebar.markdown(f"**Phone:** {info.get('phone','')}")
       st.sidebar.markdown(f"**Email:** {info.get('email','')}")

       st.sidebar.markdown("---")
       st.sidebar.markdown("### Medical Inputs")

       age = st.sidebar.number_input("Age", 21, 100, 30)
       gender = st.sidebar.selectbox("Gender", ["Male", "Female"])
   
       # Pregnancy input only for female
       if gender == "Female":
        pregnancies = st.sidebar.number_input("Number of Pregnancies", min_value=0, max_value=20, value=0)
       else:
         pregnancies = 0

       glucose = st.sidebar.slider("Glucose", 0, 200, 120)
       bp = st.sidebar.slider("Blood Pressure", 0, 130, 70)
       skin = st.sidebar.slider("Skin Thickness", 0, 100, 20)
       insulin = st.sidebar.slider("Insulin", 0, 900, 80)
       bmi = st.sidebar.number_input("BMI", 10.0, 70.0, 25.0)
       dpf = st.sidebar.slider("DPF", 0.0, 2.5, 0.5)
 
       st.sidebar.markdown("---")
       predict_btn = st.sidebar.button("Predict", use_container_width=True)
       logout_btn = st.sidebar.button("Logout")

       if logout_btn:
         st.session_state.registered = False
         st.session_state.patient_info = {}
         st.session_state.show_success = False
         st.rerun() 

    # -----------------------------
    # Main Title & About System
    # -----------------------------
       st.title("🩺 Diabetes Prediction System")
       st.markdown("AI-Powered Diabetes Risk Assessment Tool")

       if st.session_state.show_success:
        st.success("✅ Registration Successful!")
        st.session_state.show_success = False

       st.markdown("""
    ### 📋 About This System
    This Diabetes Prediction System is an AI-powered medical risk assessment tool designed to estimate the likelihood of diabetes based on key health parameters such as glucose level, BMI, blood pressure, age, and family history.
    """)

    # -----------------------------
    # Prediction Logic
    # -----------------------------
       if predict_btn:
         #update gender in mongodb
         if "_id" in info:
             users_collection.update_one({"_id":info["_id"]}, {"$set":{"gender":gender}}) 
         
         input_data = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
         input_std = scaler.transform(input_data)
         prediction = model.predict(input_std)[0]
         probability = model.predict_proba(input_std)[0]

         prob_negative = probability[0] * 100
         prob_positive = probability[1] * 100

         if prob_positive<30: risk_label="Low Risk"
         elif prob_positive<70: risk_label="Moderate Risk"
         else: risk_label="High Risk"

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

         # Display UI Results
         st.markdown("---")
         st.header("Prediction Results")
         col1, col2 = st.columns([2, 1])

         with col1:
            if prob_positive < 30: st.success("✅ LOW RISK - Diabetes Unlikely")
            elif prob_positive < 70: st.warning("⚠️ MODERATE RISK - Possible Diabetes")
            else: st.error("❌ HIGH RISK - Diabetes Likely")

            st.subheader("Probability Breakdown")
            c1, c2 = st.columns(2)
            c1.metric("Non-Diabetic", f"{prob_negative:.1f}%")
            c2.metric("Diabetic", f"{prob_positive:.1f}%")

         with col2:
            # ✅ UPDATED GAUGE COLORS: Teal (Safe), Amber (Warning), Rose/Red (Danger)
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=prob_positive, number={"suffix": "%", "font": {"color": "white"}}, title={"text": "Risk Level", "font": {"color": "white"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "white"},
                    "bar": {"color": "rgba(255,255,255,0.4)"},
                    "steps": [
                        {"range": [0, 30], "color": "#10b981"},  # Medical Teal
                        {"range": [30, 70], "color": "#f59e0b"},  # Warning Amber
                        {"range": [70, 100], "color": "#e11d48"}  # Critical Rose
                    ]
                }
            ))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)

         # Risk Factor UI Analysis
         st.markdown("---")
         st.subheader("Risk Factor Analysis")
         risk_factors, positive_factors = [], []

         if glucose >= 126: risk_factors.append("High Glucose Level (≥126 mg/dL)")
         elif 100 <= glucose < 126: risk_factors.append("Prediabetic Glucose Level (100–125 mg/dL)")
         else: positive_factors.append("Normal Glucose Level (<100 mg/dL)")   

         if bmi > 30: risk_factors.append("High BMI (Obesity)")
         elif 18.5 <= bmi <= 24.9: positive_factors.append("Healthy BMI")

         if age > 45: risk_factors.append("Age above 45")

         if bp > 120: risk_factors.append("High Blood Pressure (>120 mmHg)")
         elif 90 <= bp <= 120: positive_factors.append("Normal Blood Pressure")

         if dpf > 0.5: risk_factors.append("Higher Genetic Risk")

         if risk_factors:
            st.warning("Identified Risk Factors:")
            for factor in risk_factors: st.markdown(f"- {factor}")

         if positive_factors:
            st.success("Positive Health Indicators:")
            for factor in positive_factors: st.markdown(f"- {factor}")

         # Recommendations UI
         st.markdown("---")
         st.subheader("Recommendations")
         if prob_positive >= 70:
            st.error("- Consult a healthcare professional immediately\n- Get complete diabetes screening\n- Monitor blood sugar regularly\n- Improve diet and physical activity")
            recs_for_pdf = ["Consult a healthcare professional immediately", "Get complete diabetes screening", "Monitor blood sugar regularly", "Improve diet and physical activity"]
         elif prob_positive >= 30:
            st.warning("- Maintain healthy diet\n- Increase physical activity\n- Monitor glucose periodically")
            recs_for_pdf = ["Maintain healthy diet", "Increase physical activity", "Monitor glucose periodically"]
         else:
            st.success("- Continue healthy lifestyle\n- Exercise regularly\n- Routine health check-ups")
            recs_for_pdf = ["Continue healthy lifestyle", "Exercise regularly", "Routine health check-ups"]
            
         # -----------------------------
         # Charts Generation (For UI and PDF)
         # -----------------------------
         st.markdown('<div class="glass-box">', unsafe_allow_html=True)
         st.markdown("---")
         st.subheader("📊 Causes of Diabetes (Risk Contribution Analysis)")

         c_col1, c_col2 = st.columns([1,1])
         cause_labels, cause_values = [], []

         if glucose >= 126: cause_labels.append("High Glucose"); cause_values.append(min(glucose / 2, 100))
         if bmi > 30: cause_labels.append("High BMI (Obesity)"); cause_values.append(min(bmi * 2, 100))
         if age > 45: cause_labels.append("Age Factor"); cause_values.append(min(age, 100))
         if bp > 120: cause_labels.append("High Blood Pressure"); cause_values.append(min(bp, 100))
         if dpf > 0.5: cause_labels.append("Genetic Risk (DPF)"); cause_values.append(min(dpf * 100, 100))
         if not cause_labels: cause_labels = ["Healthy Indicators"]; cause_values = [100]

         # ✅ UPDATED BAR CHART: Medical Gradient (Teal -> Amber -> Red) based on severity
         bar_fig = go.Figure(go.Bar(
            x=cause_labels, y=cause_values, text=[f"{v:.1f}" for v in cause_values], textposition='auto',
            marker=dict(
                color=cause_values, 
                colorscale=[[0, '#10b981'], [0.5, '#f59e0b'], [1, '#e11d48']], # Healthcare severity colors
                line=dict(color="rgba(255,255,255,0.1)", width=1)
            ),
            textfont=dict(color="white", size=15)
         ))
         bar_fig.update_layout(
            title="Risk Factor Severity", xaxis_title="Causes", yaxis_title="Severity Level",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
            autosize=True, margin=dict(l=20, r=20, t=50, b=20)
         )
         bar_fig.update_xaxes(tickfont=dict(color="#cbd5e1", size=13), title_font=dict(color="#f8fafc", size=14), showline=True, linecolor="#334155")
         bar_fig.update_yaxes(tickfont=dict(color="#cbd5e1", size=13), title_font=dict(color="#f8fafc", size=14), showgrid=True, gridcolor="#1e293b", zerolinecolor="#334155")

         with c_col1: st.plotly_chart(bar_fig, use_container_width=True, config={"responsive": True})

         # ✅ UPDATED PIE CHART: Professional Medical Palette
         medical_pie_colors = ['#0ea5e9', '#14b8a6', '#6366f1', '#f59e0b', '#f43f5e', '#8b5cf6']
         pie_fig = go.Figure(data=[go.Pie(
             labels=cause_labels, values=cause_values, hole=0.45,
             marker=dict(colors=medical_pie_colors, line=dict(color='#0f172a', width=2)),
             textfont=dict(color="white", size=14)
         )])
         pie_fig.update_layout(title="Percentage Contribution", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), autosize=True, margin=dict(l=20, r=20, t=50, b=20))
         with c_col2: st.plotly_chart(pie_fig, use_container_width=True, config={"responsive": True})
         st.markdown('</div>', unsafe_allow_html=True)

         # -----------------------------
         # COMPLETE PROFESSIONAL PDF REPORT (AESTHETIC)
         # -----------------------------
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
         
         # Address Wrapping Style
         address_style = ParagraphStyle("AddressStyle", parent=styles["Normal"], fontSize=11, leading=14)

         # Title & Generated Date
         elements.append(Paragraph("🩺 DIABETES RISK PREDICTION REPORT", title_style))
         
         # Dynamic Date and Time
         report_date = current_time.strftime("%d %B %Y | %I:%M %p (IST)")
         elements.append(Paragraph(f"Report Generated On: {report_date}", date_style))

         # 1. Patient Profile Table
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

         # 2. Clinical Inputs Table
         medical_inputs = [
             ["Age", f"{age} Years"], ["Gender", gender], ["Glucose Level", f"{glucose} mg/dL"],
             ["Blood Pressure", f"{bp} mmHg"], ["Skin Thickness", f"{skin} mm"], ["Insulin Level", f"{insulin} IU/mL"],
             ["BMI", str(bmi)], ["Diabetes Pedigree Function", str(dpf)]
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

         # 3. Overall Risk Level & Risk Percentage
         elements.append(Paragraph("Risk Assessment Result", heading_style))
         if prob_positive < 30: risk_level_str = "<font color='green'><b>LOW RISK - Diabetes Unlikely</b></font>"
         elif prob_positive < 70: risk_level_str = "<font color='#d97706'><b>MODERATE RISK - Possible Diabetes</b></font>"
         else: risk_level_str = "<font color='red'><b>HIGH RISK - Diabetes Likely</b></font>"

         elements.append(Paragraph(f"<b>Overall Risk Level:</b> {risk_level_str}", normal_style))
         elements.append(Paragraph(f"<b>Risk Percentage:</b> {prob_positive:.1f}%", normal_style))
         elements.append(Spacer(1, 0.2 * inch))

         # 4. Polaroid-style Charts Generation for PDF
         try:
             # Force a small delay to allow kaleido to initialize smoothly
             time.sleep(1) 
             
             pdf_bar = go.Figure(bar_fig)
             pdf_bar.update_layout(font=dict(color="black"), paper_bgcolor="white", plot_bgcolor="white", title="Risk Severity")
             pdf_bar.update_xaxes(tickfont=dict(color="black"), title_font=dict(color="black"), linecolor="black")
             pdf_bar.update_yaxes(tickfont=dict(color="black"), title_font=dict(color="black"), gridcolor="lightgrey", zerolinecolor="black")
             
             pdf_pie = go.Figure(pie_fig)
             pdf_pie.update_layout(font=dict(color="black"), paper_bgcolor="white", plot_bgcolor="white", title="Risk Contribution")

             # Export to image bytes
             bar_img_bytes = pdf_bar.to_image(format="png", engine="kaleido", width=350, height=280, scale=2)
             pie_img_bytes = pdf_pie.to_image(format="png", engine="kaleido", width=350, height=280, scale=2)
             
             bar_rl = RLImage(BytesIO(bar_img_bytes), width=3.2*inch, height=2.5*inch)
             pie_rl = RLImage(BytesIO(pie_img_bytes), width=3.2*inch, height=2.5*inch)
             
             elements.append(Paragraph("Data Visualization & Analysis", heading_style))
             chart_table = Table([[bar_rl, pie_rl]], colWidths=[3.3*inch, 3.3*inch])
             chart_table.setStyle(TableStyle([
                 ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                 ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#e2e8f0")), # Polaroid frame look
                 ('BOTTOMPADDING', (0,0), (-1,-1), 15),
                 ('TOPPADDING', (0,0), (-1,-1), 10)
             ]))
             elements.append(chart_table)
         except Exception as e:
             elements.append(Paragraph("<font color='red'><i>* Note: Charts could not be generated. Please run 'pip install -U kaleido' in your terminal and reboot the Streamlit App.</i></font>", normal_style))
         
         elements.append(Spacer(1, 0.2 * inch))

         # 5. Recommendations in PDF
         elements.append(Paragraph("Medical Recommendations", heading_style))
         rec_list = [ListItem(Paragraph(r, normal_style)) for r in recs_for_pdf]
         elements.append(ListFlowable(rec_list, bulletType='bullet'))
         elements.append(Spacer(1, 0.4 * inch))

         elements.append(Paragraph("<b>Medical Disclaimer:</b> This report is AI-generated and does not replace professional medical advice.", styles["Italic"]))

         # Build PDF
         doc.build(elements)
         pdf = buffer.getvalue()
         buffer.close()

         st.download_button(
             label="📄 Download Professional Medical Report (PDF)",
             data=pdf,
             file_name=f"Diabetes_Report_{info.get('name', 'Patient')}.pdf",
             mime="application/pdf"
         )

         # Disclaimer UI
         st.markdown("---")
         st.warning("⚠️ Medical Disclaimer:\nThis tool does NOT replace professional medical advice.")

# =====================================================
# Navigation
# =====================================================
if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
