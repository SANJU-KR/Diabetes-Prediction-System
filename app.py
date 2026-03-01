# -----------------------------
# Import Required Libraries
# -----------------------------
import streamlit as st
import numpy as np
import joblib
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import base64
import re
import pycountry
import phonenumbers
import time
import io
from io import BytesIO

def get_base64_image(image_file):
    try:
        with open(image_file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

def country_to_flag(country_code):
    return "".join(chr(127397 + ord(char)) for char in country_code.upper())

# ✅ REPORTLAB IMPORTS FOR CLINICAL PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

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

if "registered" not in st.session_state: st.session_state.registered = False
if "patient_info" not in st.session_state: st.session_state.patient_info = {}
if "show_success" not in st.session_state: st.session_state.show_success = False

# =====================================================
# REGISTRATION PAGE
# =====================================================
def registration_page():
    img = get_base64_image("health.png")
    st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.10), rgba(0,0,0,0.10)), url("data:image/jpg;base64,{img}"); background-size: cover; background-position: center; background-attachment: fixed; }}
    div[data-testid="stForm"] {{ background: rgba(255, 255, 255, 0.10); backdrop-filter: blur(12px); border-radius: 25px; padding: 40px; width: 100%; max-width: 700px; margin: 5vh auto; border: 1px solid rgba(255,255,255,0.25); box-shadow: 0 10px 50px rgba(0,0,0,0.3); }}
    h1 {{ color: white !important; text-align: center; font-weight: 700; font-size: 40px; margin-bottom: 10px; }}
    .stMarkdown p {{ color: #f1f1f1 !important; text-align: center; font-size: 18px; font-weight: 500; }}
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {{ background: rgba(255, 255, 255, 0.08) !important; backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); border-radius: 18px !important; border: 1.5px solid rgba(255, 255, 255, 0.35) !important; box-shadow: inset 0 0 12px rgba(255,255,255,0.15); transition: all 0.3s ease; }}
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {{ border: 1.5px solid rgba(255,255,255,0.8) !important; box-shadow: 0 0 20px rgba(255,255,255,0.6); }}
    input, textarea {{ color: black !important; font-weight: 500 !important; }}
    label {{ color: #ffffff !important; font-size: 19px !important; font-weight: 800 !important; letter-spacing: 0.6px; text-shadow: 0px 2px 6px rgba(0,0,0,0.7); }}
    input::placeholder, textarea::placeholder {{ color: #555 !important; font-weight: 500 !important; }}
    div[data-testid="stForm"] button {{ background: linear-gradient(90deg, #1f8ef1, #005bea); color: white !important; border-radius: 12px !important; height: 50px !important; font-size: 18px !important; font-weight: 600 !important; border: none !important; transition: 0.3s ease-in-out; }}
    div[data-testid="stForm"] button:hover {{ transform: scale(1.05); box-shadow: 0 6px 20px rgba(0,91,234,0.6); }}
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📝 Patient Registration")
    st.markdown("Please register to access the Diabetes Prediction System")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("registration_form"):
            name = st.text_input("Full Name")
            country_list = [country.name for country in pycountry.countries]
            selected_country = st.selectbox("🌍 Select Country", country_list)
            country_obj = pycountry.countries.get(name=selected_country)
            country_code = phonenumbers.country_code_for_region(country_obj.alpha_2)
            phone = st.text_input("Enter Phone Number (without country code)")
            email = st.text_input("Email Address")
            address = st.text_area("Address")
            submit = st.form_submit_button("Register")

            if submit:
                name, phone, email, address = name.strip(), phone.strip(), email.strip(), address.strip()
                if not all([name, phone, email, address]):
                    st.error("❌ Please fill all fields properly")
                    return
                if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                    st.error("❌ Please enter a valid email address")
                    return
                try:
                    parsed_number = phonenumbers.parse(phone, country_obj.alpha_2)
                    if not phonenumbers.is_valid_number(parsed_number):
                        st.error("❌ Invalid phone number for selected country")
                        return
                    formatted_phone = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
                except:
                    st.error("❌ Invalid phone number format")
                    return        
                    
                ist = pytz.timezone("Asia/Kolkata")
                current_time = datetime.now(ist)
                patient_id = "PAT-" + str(uuid.uuid4().int)[:6]
                        
                user_data = {"_id": patient_id, "name": name, "phone": formatted_phone, "country": selected_country, "email": email, "address": address, "gender": "Not Selected", "created_at": current_time.strftime("%d-%m-%Y %I:%M:%S %p")} 
                users_collection.insert_one(user_data)
                st.session_state.patient_info = user_data
                st.session_state.registered = True
                st.session_state.show_success = True
                st.rerun()

# =====================================================
# MAIN PREDICTION PAGE
# =====================================================
@st.cache_resource
def load_model():
    try: return joblib.load("diabetes_model.pkl"), joblib.load("scaler_svm.pkl")
    except Exception as e: st.error(f"⚠️ Model Loading Error: {e}"); st.stop()

def prediction_page():
    model, scaler = load_model()
    if not st.session_state.patient_info: st.session_state.registered = False; st.stop()

    img = get_base64_image("health22.png") 
    st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(rgba(0,0,0,.23), rgba(0,0,0,.23)), url("data:image/png;base64,{img}"); background-size: cover; background-position: center; background-attachment: fixed; }}
    h1, h2, h3 {{ color: white !important; }}
    p, li {{ color: #f1f1f1 !important; font-size:clamp(16px,2vw,22px); }}
    
    /* Original Sidebar Styles maintaned */
    section[data-testid="stSidebar"] {{ background: rgba(255, 255, 255, 0.05) !important; backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(25px); border-right: 1px solid rgba(255,255,255,0.15); box-shadow: 4px 0 30px rgba(0,0,0,0.4); padding: 25px; }}
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {{ color: white !important; font-weight: 600; }}
    section[data-testid="stSidebar"] button {{ background: rgba(255,255,255,0.15) !important; backdrop-filter: blur(15px); border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.4) !important; color: white !important; font-weight: 600 !important; transition: 0.3s ease; }}
    section[data-testid="stSidebar"] button:hover {{ background: rgba(255,255,255,0.25) !important; transform: scale(1.03); }}
    
    div[data-baseweb="popover"] {{ background: midnightblue !important; border: 1px solid rgba(255,255,255,0.2); backdrop-filter: blur(20px); }}
    ul[role="listbox"] {{ background: midnightblue !important; }}
    li[role="option"] {{ background: transparent !important; color: white !important; font-weight: 600 !important; }}
    li[role="option"]:hover {{ background: #00d4ff !important; color: black !important; }}
    section[data-testid="stSidebar"] div[data-baseweb="select"] span {{ color: black !important; font-weight: 600 !important; }}
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div, section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{ background-color: #f1f5f9 !important; color: black !important; border-radius: 14px !important; border: 1.5px solid rgba(255,255,255,0.35) !important; }}
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within, section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {{ border: 1.5px solid rgba(255,255,255,0.8) !important; box-shadow: 0 0 15px rgba(255,255,255,0.6); }}
    section[data-testid="stSidebar"] div[data-baseweb="input"] input {{ color: black !important; -webkit-text-fill-color: black !important; font-weight: 600 !important; }}
    input[type="number"]::-webkit-inner-spin-button, input[type="number"]::-webkit-outer-spin-button {{ -webkit-appearance: none; margin: 0; }}
    
    div.stDownloadButton > button {{ background-color: #0f172a !important; color: white !important; font-weight: 700 !important; border-radius: 12px !important; padding: 10px 20px !important; border: 1px solid #00d4ff !important; width: 100%; height: 60px; font-size: 18px; }}
    div.stDownloadButton > button:hover {{ background-color: #00d4ff !important; color: black !important; transform: scale(1.02); }}
    .glass-box {{ background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); border-radius: 20px; padding: 40px; border: 1px solid rgba(255,255,255,0.25); box-shadow: 0 8px 32px rgba(0,0,0,0.4); margin-bottom: 40px; }}
    </style>
    """, unsafe_allow_html=True)

    # Sidebar
    st.sidebar.markdown("# Patient Profile")
    info = st.session_state.patient_info
    st.sidebar.markdown(f"**Name:** {info.get('name','')}\n\n**Phone:** {info.get('phone','')}\n\n**Email:** {info.get('email','')}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Medical Inputs")

    age = st.sidebar.number_input("Age", 21, 100, 30)
    gender = st.sidebar.selectbox("Gender", ["Male", "Female"])
    pregnancies = st.sidebar.number_input("Number of Pregnancies", 0, 20, 0) if gender == "Female" else 0
    glucose = st.sidebar.slider("Glucose", 0, 250, 120)
    bp = st.sidebar.slider("Blood Pressure", 0, 180, 70)
    skin = st.sidebar.slider("Skin Thickness", 0, 100, 20)
    insulin = st.sidebar.slider("Insulin", 0, 900, 80)
    bmi = st.sidebar.number_input("BMI", 10.0, 70.0, 25.0)
    dpf = st.sidebar.slider("DPF", 0.0, 2.5, 0.5)
 
    st.sidebar.markdown("---")
    predict_btn = st.sidebar.button("Predict", use_container_width=True)
    if st.sidebar.button("Logout"): st.session_state.clear(); st.rerun() 

    st.title("🩺 Diabetes Prediction System")
    st.markdown("AI-Powered Diabetes Risk Assessment Tool")

    if st.session_state.show_success:
        st.success("✅ Registration Successful!")
        st.session_state.show_success = False

    if predict_btn:
        if "_id" in info: users_collection.update_one({"_id":info["_id"]}, {"$set":{"gender":gender}}) 
         
        input_data = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
        input_std = scaler.transform(input_data)
        prob_positive = model.predict_proba(input_std)[0][1] * 100

        if prob_positive < 30: risk_label, risk_color, risk_hex = "LOW RISK", "green", "#2e7d32"
        elif prob_positive < 70: risk_label, risk_color, risk_hex = "MODERATE RISK", "orange", "#f57c00"
        else: risk_label, risk_color, risk_hex = "HIGH RISK", "red", "#d32f2f"

        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)    
        predictions_collection.insert_one({"patient_id": info["_id"], "patient_name": info["name"], "age": age, "gender": gender, "glucose": glucose, "blood_pressure": bp, "bmi": bmi, "prediction": risk_label, "probability": round(prob_positive, 2), "created_at": current_time.strftime("%d-%m-%Y %H:%M:%S")})

        st.markdown("---")
        st.header("Prediction Results")
        
        # Determine specific Clinical Risk Factors
        risk_factors, positive_factors = [], []
        cause_labels, cause_values = [], []
        
        if glucose >= 126: risk_factors.append("High Glucose Level (>= 126 mg/dL)"); cause_labels.append("Hyperglycemia"); cause_values.append(min(glucose/2, 100))
        elif 100 <= glucose < 126: risk_factors.append("Prediabetic Glucose Level (100–125 mg/dL)"); cause_labels.append("Elevated Glucose"); cause_values.append(50)
        else: positive_factors.append("Normal Glucose Level (<100 mg/dL)")    

        if bmi > 30: risk_factors.append("High BMI (Obesity)"); cause_labels.append("High BMI"); cause_values.append(min(bmi*1.5, 100))
        elif 18.5 <= bmi <= 24.9: positive_factors.append("Healthy BMI (18.5-24.9)")

        if age > 45: risk_factors.append("Age above 45"); cause_labels.append("Age Factor"); cause_values.append(min(age, 100))
        if bp > 120: risk_factors.append("High Blood Pressure (>120 mmHg)"); cause_labels.append("Hypertension"); cause_values.append(min(bp*.8, 100))
        if dpf > 0.5: risk_factors.append("Higher Genetic Risk Profile")
        
        if not cause_labels: cause_labels = ["Baseline Risk"]; cause_values = [10]

        # Recommendations logic
        if prob_positive >= 70: recs_for_pdf = ["Consult a healthcare professional immediately", "Get complete diabetes screening", "Monitor blood sugar regularly", "Strictly improve diet and physical activity"]
        elif prob_positive >= 30: recs_for_pdf = ["Maintain healthy diet", "Increase physical activity", "Monitor glucose periodically"]
        else: recs_for_pdf = ["Continue healthy lifestyle", "Exercise regularly", "Routine health check-ups"]

        # =====================================================
        # COMPLETE PROFESSIONAL CLINICAL PDF REPORT GENERATION
        # =====================================================
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#1e293b"), fontName="Helvetica-Bold", spaceAfter=15)
        medcore_style = ParagraphStyle("Medcore", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#64748b"), fontName="Helvetica-Bold")
        meta_style = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#94a3b8"), alignment=2)
        section_heading = ParagraphStyle("SecHeading", parent=styles["Heading2"], fontSize=12, textColor=colors.white, backColor=colors.HexColor("#334155"), fontName="Helvetica-Bold", spaceBefore=15, spaceAfter=10, borderPadding=5)
        banner_text = ParagraphStyle("Banner", parent=styles["Normal"], fontSize=18, textColor=colors.white, fontName="Helvetica-Bold", alignment=1)
        sub_banner_text = ParagraphStyle("SubBanner", parent=styles["Normal"], fontSize=12, textColor=colors.white, alignment=1)
        table_header = ParagraphStyle("TH", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#334155"), fontName="Helvetica-Bold")
        table_body = ParagraphStyle("TB", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#475569"))
        bullet_warn = ParagraphStyle("BW", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#d32f2f"), spaceAfter=4)
        bullet_good = ParagraphStyle("BG", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#2e7d32"), spaceAfter=4)
        bullet_neutral = ParagraphStyle("BN", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#334155"), spaceAfter=4)

        # 1. Header Area
        report_date = current_time.strftime("%d %B %Y | %I:%M %p (IST)")
        header_table = Table([
            [Paragraph("MEDCORE AI | Diabetes Intelligence Platform", medcore_style), 
             Paragraph(f"Report ID: {info.get('_id', 'N/A')}<br/>Generated: {report_date}", meta_style)]
        ], colWidths=[3.5*inch, 4*inch])
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceBefore=5, spaceAfter=15))
        elements.append(Paragraph("DIABETES RISK PREDICTION REPORT", title_style))

        # 2. Dual Column Tables (Patient Profile & Clinical Inputs)
        def make_sub_table(title, data_dict):
            data = [[Paragraph(title, table_header), ""]]
            for k, v in data_dict.items():
                data.append([Paragraph(k, table_header), Paragraph(str(v), table_body)])
            t = Table(data, colWidths=[1.2*inch, 2.3*inch])
            t.setStyle(TableStyle([
                ('SPAN', (0,0), (1,0)),
                ('BACKGROUND', (0,0), (1,0), colors.HexColor("#f1f5f9")),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            return t

        addr_short = info.get("address", "N/A")[:30] + "..." if len(info.get("address", "")) > 30 else info.get("address", "N/A")
        patient_data = {"Patient ID": info.get("_id"), "Full Name": info.get("name"), "Email": info.get("email"), "Phone": info.get("phone"), "Country": info.get("country"), "Address": addr_short}
        
        clinical_data = {"Age": f"{age} Years", "Gender": gender, "Glucose": f"{glucose} mg/dL", "Blood Press.": f"{bp} mmHg", "Skin Thick.": f"{skin} mm", "Insulin": f"{insulin} IU/mL", "BMI": f"{bmi} kg/m²", "DPF": str(dpf)}
        if gender == "Female": clinical_data["Pregnancies"] = str(pregnancies)

        profile_table = make_sub_table("PATIENT PROFILE", patient_data)
        clinical_table = make_sub_table("CLINICAL INPUTS", clinical_data)

        master_table = Table([[profile_table, clinical_table]], colWidths=[3.8*inch, 3.8*inch])
        master_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        elements.append(master_table)
        elements.append(Spacer(1, 0.2*inch))

        # 3. Dynamic Risk Banner
        banner_data = [
            [Paragraph(risk_label, banner_text)],
            [Paragraph(f"AI Probability Score: {prob_positive:.1f}%", sub_banner_text)],
            [Paragraph(f"Assessed by MEDCORE SVM Engine • {report_date}", ParagraphStyle("s", parent=sub_banner_text, fontSize=8, textColor=colors.HexColor("#f8fafc")))]
        ]
        banner = Table(banner_data, colWidths=[7.5*inch])
        banner.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(risk_hex)),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(banner)
        elements.append(Spacer(1, 0.2*inch))

        # 4. Charts Generation (Matplotlib Custom Design)
        elements.append(Paragraph("DATA VISUALIZATION & ANALYSIS", section_heading))
        
        try:
            # Matplotlib Aesthetic Color Palette
            chart_colors = ['#d32f2f', '#f57c00', '#1976d2', '#388e3c']
            
            # --- Bar Chart ---
            fig_bar, ax_bar = plt.subplots(figsize=(4, 3))
            bars = ax_bar.bar(cause_labels, cause_values, color=chart_colors[:len(cause_values)], edgecolor='none', width=0.6)
            ax_bar.set_title("Risk Factor Severity", fontsize=11, fontweight='bold', pad=15)
            ax_bar.set_ylabel("Severity Score", fontsize=9)
            ax_bar.set_ylim(0, 120)
            ax_bar.spines['top'].set_visible(False)
            ax_bar.spines['right'].set_visible(False)
            ax_bar.spines['left'].set_color('#e2e8f0')
            ax_bar.spines['bottom'].set_color('#e2e8f0')
            ax_bar.set_facecolor('#f8fafc')
            fig_bar.patch.set_facecolor('#f8fafc')
            
            # Add value labels on top of bars
            for bar in bars:
                yval = bar.get_height()
                ax_bar.text(bar.get_x() + bar.get_width()/2, yval + 2, f"{int(yval)}", ha='center', va='bottom', fontsize=9, fontweight='bold')
                
            plt.xticks(rotation=15, ha='right', fontsize=8)
            plt.tight_layout()
            bar_buf = BytesIO()
            plt.savefig(bar_buf, format='png', bbox_inches='tight', dpi=300)
            bar_buf.seek(0)
            plt.close(fig_bar)

            # --- Donut Chart ---
            fig_pie, ax_pie = plt.subplots(figsize=(4, 3))
            wedges, texts, autotexts = ax_pie.pie(cause_values, labels=cause_labels, autopct='%1.0f%%', 
                                                  startangle=140, colors=chart_colors[:len(cause_values)],
                                                  wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2),
                                                  textprops=dict(color="white", fontweight='bold', fontsize=9))
            
            # Legend below Donut
            ax_pie.legend(wedges, cause_labels, loc="center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False, fontsize=8)
            ax_pie.set_title("Risk Contribution (%)", fontsize=11, fontweight='bold', pad=15)
            plt.tight_layout()
            
            pie_buf = BytesIO()
            plt.savefig(pie_buf, format='png', bbox_inches='tight', dpi=300)
            pie_buf.seek(0)
            plt.close(fig_pie)

            # Insert into PDF
            bar_rl = RLImage(bar_buf, width=3.3*inch, height=2.5*inch)
            pie_rl = RLImage(pie_buf, width=3.3*inch, height=2.5*inch)
            chart_table = Table([[bar_rl, pie_rl]], colWidths=[3.8*inch, 3.8*inch])
            chart_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            elements.append(chart_table)
        except Exception as e:
            elements.append(Paragraph(f"* Chart rendering failed: {e}", bullet_warn))

        # 5. Risk Factor Analysis & Recommendations (Side by Side)
        analysis_data = []
        for r in risk_factors: analysis_data.append([Paragraph(f"▲ {r}", bullet_warn)])
        for p in positive_factors: analysis_data.append([Paragraph(f"✓ {p}", bullet_good)])
        
        rec_data = [[Paragraph(f"• {r}", bullet_neutral)] for r in recs_for_pdf]

        analysis_table = Table(analysis_data, colWidths=[3.5*inch])
        rec_table = Table(rec_data, colWidths=[3.5*inch])

        footer_sections = Table([
            [Paragraph("RISK FACTOR ANALYSIS", section_heading), Paragraph("MEDICAL RECOMMENDATIONS", section_heading)],
            [analysis_table, rec_table]
        ], colWidths=[3.8*inch, 3.8*inch])
        footer_sections.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        
        elements.append(Spacer(1, 0.1*inch))
        elements.append(footer_sections)

        # 6. Disclaimer Footer
        elements.append(Spacer(1, 0.3*inch))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=5))
        disclaimer = "<b>CONFIDENTIAL MEDICAL DOCUMENT</b><br/>MEDICAL DISCLAIMER: This report is AI-generated and does not replace professional medical advice. Consult a qualified healthcare professional for clinical diagnosis, interpretation, and treatment."
        elements.append(Paragraph(disclaimer, ParagraphStyle("Disc", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#94a3b8"), alignment=1)))

        # Build PDF & Trigger Download immediately
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # UI Results (Streamlit Output)
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown(f"### Overall Risk: <span style='color:{risk_color};'>{risk_label}</span>", unsafe_allow_html=True)
            st.markdown("Your clinical report has been generated successfully. Please download it below.")
            st.download_button(
                label="📄 DOWNLOAD 'MEDCORE AI' CLINICAL REPORT",
                data=pdf_bytes,
                file_name=f"MEDCORE_Report_{info.get('_id')}.pdf",
                mime="application/pdf"
            )
        with c2:
            st.metric("Diabetic Probability", f"{prob_positive:.1f}%")
            
# Navigation
if not st.session_state.registered: registration_page()
else: prediction_page()
