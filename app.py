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

# ✅ ADDED FOR PROFESSIONAL PDF GENERATION
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

uri = "mongodb+srv://diabetes_user:Diabetes%40123@diabetescluster.oxegep6.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["diabetes_app"]
users_collection = db["registered_users"]
predictions_collection = db["predictions"]

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(page_title="Diabetes Prediction System", page_icon="🩺", layout="wide")

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
    img = get_base64_image("health.png")
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.10), rgba(0,0,0,0.10)), url("data:image/jpg;base64,{img}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    div[data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.10); backdrop-filter: blur(.2px);
        border-radius: 25px; padding: 40px; width: 100%; max-width: 700px; margin: 5vh auto;
        border: 1px solid rgba(255,255,255,0.25); box-shadow: 0 10px 50px rgba(0,0,0,0.3);
    }}
    h1 {{ color: white !important; text-align: center; font-weight: 700; font-size: 40px; }}
    input, textarea {{ color: black !important; font-weight: 500 !important; }}
    label {{ color: #ffffff !important; font-size: 19px !important; font-weight: 800 !important; }}
    </style>
    """, unsafe_allow_html=True)

    st.title("📝 Patient Registration")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("registration_form"):
            name = st.text_input("Full Name")
            country_list = [c.name for c in pycountry.countries]
            selected_country = st.selectbox("🌍 Select Country", country_list)
            phone = st.text_input("Enter Phone Number (without country code)")
            email = st.text_input("Email Address")
            address = st.text_area("Address")
            submit = st.form_submit_button("Register")

            if submit:
                name, phone, email, address = name.strip(), phone.strip(), email.strip(), address.strip()
                if not all([name, phone, email, address]):
                    st.error("❌ Please fill all fields properly")
                    return
                
                ist = pytz.timezone("Asia/Kolkata")
                patient_id = "PAT" + str(uuid.uuid4().int)[:6]
                user_data = {
                    "_id": patient_id, "name": name, "phone": phone, "country": selected_country,
                    "email": email, "address": address, "gender": "Not Selected",
                    "created_at": datetime.now(ist).strftime("%d-%m-%Y %I:%M:%S %p")
                }
                users_collection.insert_one(user_data)
                st.session_state.patient_info = user_data
                st.session_state.registered, st.session_state.show_success = True, True
                st.rerun()

# =====================================================
# MAIN PREDICTION PAGE
# =====================================================
@st.cache_resource
def load_model():
    return joblib.load("diabetes_model.pkl"), joblib.load("scaler_svm.pkl")

def prediction_page():
    model, scaler = load_model()
    info = st.session_state.patient_info
    img = get_base64_image("health22.png")

    st.markdown(f"""
        <style>
        .stApp {{ background: linear-gradient(rgba(0,0,0,.23), rgba(0,0,0,.23)), url("data:image/png;base64,{img}"); background-size: cover; }}
        section[data-testid="stSidebar"] {{ background: rgba(30,30,30,0.10) !important; backdrop-filter: blur(25px); }}
        section[data-testid="stSidebar"] * {{ color: white !important; }}
        /* Input text fix */
        section[data-testid="stSidebar"] input {{ color: black !important; -webkit-text-fill-color: black !important; }}
        </style>
    """, unsafe_allow_html=True)

    # SIDEBAR INPUTS
    st.sidebar.markdown("# Patient Profile")
    st.sidebar.markdown(f"**Name:** {info.get('name')}\n**ID:** {info.get('_id')}")
    st.sidebar.markdown("---")
    
    age = st.sidebar.number_input("Age", 21, 100, 30)
    gender = st.sidebar.selectbox("Gender", ["Male", "Female"])
    pregnancies = st.sidebar.number_input("Pregnancies", 0, 20, 0) if gender == "Female" else 0
    glucose = st.sidebar.slider("Glucose", 0, 200, 120)
    bp = st.sidebar.slider("Blood Pressure", 0, 130, 70)
    skin = st.sidebar.slider("Skin Thickness", 0, 100, 20)
    insulin = st.sidebar.slider("Insulin", 0, 900, 80)
    bmi = st.sidebar.number_input("BMI", 10.0, 70.0, 25.0)
    dpf = st.sidebar.slider("DPF", 0.0, 2.5, 0.5)
    
    predict_btn = st.sidebar.button("Predict", use_container_width=True)

    if predict_btn:
        input_data = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
        input_std = scaler.transform(input_data)
        prob_positive = model.predict_proba(input_std)[0][1] * 100
        
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)

        # UI RESULTS
        st.header("Prediction Results")
        col1, col2 = st.columns([2, 1])
        with col1:
            if prob_positive < 30: st.success("✅ LOW RISK")
            elif prob_positive < 70: st.warning("⚠️ MODERATE RISK")
            else: st.error("❌ HIGH RISK")
            st.metric("Risk Percentage", f"{prob_positive:.1f}%")

        # --- CAUSES VISUALIZATION ---
        cause_labels, cause_values = ["Glucose", "BMI", "Age", "BP"], [glucose/2, bmi*2, age, bp]
        bar_fig = go.Figure(go.Bar(x=cause_labels, y=cause_values, marker_color='red'))
        pie_fig = go.Figure(go.Pie(labels=cause_labels, values=cause_values, hole=0.4))
        
        st.plotly_chart(bar_fig)
        st.plotly_chart(pie_fig)

        # -----------------------------
        # PROFESSIONAL PDF GENERATION
        # -----------------------------
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Styles
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], alignment=1, fontSize=18)
        body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=11)

        # Title and Timestamp
        elements.append(Paragraph("COMPREHENSIVE DIABETES RISK ASSESSMENT", title_style))
        elements.append(Paragraph(f"Generated on: {now.strftime('%Y-%m-%d %H:%M:%S')}", body_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Patient Profile with Address Wrap
        addr = Paragraph(info.get('address', 'N/A'), body_style)
        p_data = [["Patient ID", info.get('_id')], ["Full Name", info.get('name')], ["Address", addr]]
        p_table = Table(p_data, colWidths=[1.5*inch, 4*inch])
        p_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(Paragraph("Patient Profile", styles["Heading2"]))
        elements.append(p_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Clinical Inputs
        c_data = [["Glucose", f"{glucose} mg/dL"], ["BMI", str(bmi)], ["Age", str(age)]]
        c_table = Table(c_data, colWidths=[1.5*inch, 4*inch])
        c_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(Paragraph("Clinical Inputs", styles["Heading2"]))
        elements.append(c_table)
        
        # Risk Assessment Result
        elements.append(Paragraph("Risk Assessment Result", styles["Heading2"]))
        elements.append(Paragraph(f"Risk Percentage: {prob_positive:.1f}%", body_style))

        # --- IMAGE GENERATION ---
        try:
            time.sleep(2) # Stability wait
            bar_img = bar_fig.to_image(format="png", engine="kaleido")
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(RLImage(BytesIO(bar_img), width=4*inch, height=3*inch))
        except Exception as e:
            elements.append(Paragraph(f"Error loading charts: {e}", body_style))

        doc.build(elements)
        st.download_button("📄 Download Report", buffer.getvalue(), f"Report_{info.get('name')}.pdf", "application/pdf")

if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
