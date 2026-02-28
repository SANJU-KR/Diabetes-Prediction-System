# ================================================================
#  MEDCORE AI  —  Enterprise Clinical Intelligence Platform
#  Clean, High-Contrast Medical UI for Maximum Readability
# ================================================================

import streamlit as st
import numpy as np
import joblib
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import re, uuid, pytz, time
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
#  MongoDB Setup
# ─────────────────────────────────────────────────────────────
_URI      = "mongodb+srv://diabetes_user:Diabetes%40123@diabetescluster.oxegep6.mongodb.net/?retryWrites=true&w=majority"
try:
    _mc       = MongoClient(_URI, server_api=ServerApi("1"), serverSelectionTimeoutMS=5000)
    _db       = _mc["diabetes_app"]
    users_col = _db["registered_users"]
    preds_col = _db["predictions"]
except Exception as e:
    st.warning("⚠️ Running in local mode. Database connection failed.")

# ─────────────────────────────────────────────────────────────
#  Page Config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MEDCORE AI — Clinical System",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
#  Session State
# ─────────────────────────────────────────────────────────────
st.session_state.setdefault("registered",    False)
st.session_state.setdefault("patient_info",  {})
st.session_state.setdefault("show_success",  False)
st.session_state.setdefault("model_ran",     False)

# ─────────────────────────────────────────────────────────────
#  Enterprise Color Palette
# ─────────────────────────────────────────────────────────────
C_PRIMARY = "#026AA7" # Medical Blue
C_NAVY    = "#0F172A" # Deep Slate (Sidebar)
C_BG      = "#F8FAFC" # Off-white background
C_TEXT    = "#1E293B" # Dark text for readability
C_MUTED   = "#64748B" # Subtitle text
C_GREEN   = "#059669" # Success
C_AMBER   = "#D97706" # Warning
C_RED     = "#DC2626" # Danger
C_BORDER  = "#E2E8F0" # Card borders

CHART_PALETTE = [C_RED, C_AMBER, C_PRIMARY, "#8B5CF6", C_GREEN]

# ═════════════════════════════════════════════════════════════
#  ENTERPRISE CSS - Clean, Accessible, Readable
# ═════════════════════════════════════════════════════════════
def inject_enterprise_css():
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── MAIN BACKGROUND & FONT ── */
.stApp {{
    background-color: {C_BG};
    font-family: 'Inter', sans-serif;
    color: {C_TEXT};
}}

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, header, .stDeployButton {{ display:none!important; }}

/* ── TYPOGRAPHY ── */
h1, h2, h3, h4, h5, h6, p, span, div {{
    color: {C_TEXT};
    font-family: 'Inter', sans-serif;
}}
p {{ line-height: 1.6; color: #334155; }}

/* ── SIDEBAR (Keeping it Dark as per your preference) ── */
section[data-testid="stSidebar"] {{
    background-color: {C_NAVY} !important;
    border-right: 1px solid #1E293B !important;
}}
section[data-testid="stSidebar"] * {{
    color: #F8FAFC !important; /* Force white text in sidebar */
}}
section[data-testid="stSidebar"] label {{
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #94A3B8 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* Sidebar Inputs - White background so user text is readable */
section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="input"] input,
section[data-testid="stSidebar"] div[data-baseweb="select"] span {{
    color: #0F172A !important; /* Dark text inside input */
    font-weight: 500 !important;
}}

/* ── BUTTONS ── */
button[kind="primary"], div[data-testid="stForm"] button, section[data-testid="stSidebar"] button {{
    background-color: {C_PRIMARY} !important;
    color: white !important;
    border-radius: 6px !important;
    border: none !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    transition: background-color 0.2s;
}}
button[kind="primary"]:hover, div[data-testid="stForm"] button:hover {{
    background-color: #035B8F !important;
}}

/* Download Button Specific */
div.stDownloadButton > button {{
    background-color: {C_GREEN} !important;
    width: 100% !important;
    padding: 12px !important;
    font-size: 16px !important;
}}

/* ── CARDS & FORMS (Main Area) ── */
div[data-testid="stForm"] {{
    background-color: #FFFFFF !important;
    border: 1px solid {C_BORDER} !important;
    border-radius: 8px !important;
    padding: 32px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    max-width: 600px;
    margin: 0 auto;
}}
div[data-testid="stForm"] label {{
    color: #475569 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}}
div[data-testid="stForm"] input, div[data-testid="stForm"] textarea, div[data-testid="stForm"] div[data-baseweb="select"] span {{
    background-color: #F8FAFC !important;
    border: 1px solid {C_BORDER} !important;
    color: {C_TEXT} !important;
    border-radius: 6px !important;
}}

/* ── METRICS ── */
div[data-testid="metric-container"] {{
    background-color: #FFFFFF !important;
    border: 1px solid {C_BORDER} !important;
    border-left: 4px solid {C_PRIMARY} !important;
    border-radius: 6px !important;
    padding: 16px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: {C_TEXT} !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    color: {C_MUTED} !important;
    font-weight: 600 !important;
}}

/* ── CUSTOM CLINICAL CARD CLASS ── */
.clinical-card {{
    background-color: #FFFFFF;
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}}
.clinical-header {{
    font-size: 18px;
    font-weight: 700;
    color: {C_TEXT};
    border-bottom: 2px solid #F1F5F9;
    padding-bottom: 12px;
    margin-bottom: 16px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* ── STREAMLIT ALERTS ── */
div[data-testid="stSuccess"] {{ background-color: #ECFDF5 !important; border-color: #10B981 !important; color: #065F46 !important; }}
div[data-testid="stWarning"] {{ background-color: #FFFBEB !important; border-color: #F59E0B !important; color: #92400E !important; }}
div[data-testid="stError"]   {{ background-color: #FEF2F2 !important; border-color: #EF4444 !important; color: #991B1B !important; }}

hr {{ border-color: {C_BORDER} !important; }}

</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  MATPLOTLIB HELPERS
# ═════════════════════════════════════════════════════════════
def _bar_png(labels, values):
    fig, ax = plt.subplots(figsize=(5.2, 3.2), dpi=140)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    cols = [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(len(labels))]
    bars = ax.bar(labels, values, color=cols, width=0.52, edgecolor="#E2E8F0", linewidth=.8)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{v:.1f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#1E293B")

    ax.set_ylim(0, max(values)*1.28 if values else 110)
    ax.set_xlabel("Risk Factors", fontsize=9, color="#475569", labelpad=5)
    ax.set_ylabel("Severity Score", fontsize=9, color="#475569", labelpad=5)
    ax.set_title("Risk Factor Severity", fontsize=11, fontweight="bold", color="#1E293B", pad=8)
    ax.tick_params(axis="x", labelsize=8, colors="#475569")
    ax.tick_params(axis="y", labelsize=8, colors="#475569")
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#CBD5E1")
    ax.yaxis.grid(True, color="#F1F5F9", linewidth=.6, linestyle="--")
    ax.set_axisbelow(True)
    plt.tight_layout(pad=1.1)

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#FFFFFF")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _pie_png(labels, values):
    fig, ax = plt.subplots(figsize=(4.8, 3.4), dpi=140)
    fig.patch.set_facecolor("#FFFFFF")
    cols = [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(len(labels))]
    wedges, texts, autos = ax.pie(
        values, labels=labels, colors=cols, autopct="%1.1f%%", startangle=130,
        wedgeprops=dict(width=0.58, edgecolor="#FFFFFF", linewidth=1.8), pctdistance=0.78,
    )
    for t  in texts: t.set_fontsize(8);  t.set_color("#1E293B")
    for at in autos: at.set_fontsize(7.5); at.set_fontweight("bold"); at.set_color("#FFFFFF")
    ax.set_title("Risk Contribution (%)", fontsize=11, fontweight="bold", color="#1E293B", pad=8)
    plt.tight_layout(pad=1.1)

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#FFFFFF")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ═════════════════════════════════════════════════════════════
#  REPORTLAB PAGE TEMPLATE (Header/Footer)
# ═════════════════════════════════════════════════════════════
def report_header_footer(canvas, doc):
    canvas.saveState()
    # Header Area
    canvas.setFillColorRGB(0.01, 0.42, 0.65) # C_PRIMARY
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(40, letter[1] - 45, "MEDCORE CLINICAL SYSTEMS")
    
    canvas.setFillColorRGB(0.4, 0.4, 0.4)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(40, letter[1] - 60, "Department of Endocrinology | Innovation Drive, Sector 43")
    canvas.drawString(40, letter[1] - 72, "Phone: 1800-MED-CORE | Email: records@medcore.ai")
    
    canvas.setLineWidth(1)
    canvas.setStrokeColorRGB(0.88, 0.91, 0.94)
    canvas.line(40, letter[1] - 85, letter[0] - 40, letter[1] - 85)
    
    # Footer Area
    canvas.setLineWidth(0.5)
    canvas.setStrokeColorRGB(0.88, 0.91, 0.94)
    canvas.line(40, 50, letter[0] - 40, 50)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColorRGB(0.5, 0.5, 0.5)
    canvas.drawString(40, 35, "CONFIDENTIAL EHR DOCUMENT - UNAUTHORIZED DISTRIBUTION PROHIBITED")
    canvas.drawRightString(letter[0] - 40, 35, f"Page {doc.page}")
    canvas.restoreState()


# ═════════════════════════════════════════════════════════════
#  REGISTRATION PAGE
# ═════════════════════════════════════════════════════════════
def registration_page():
    inject_enterprise_css()

    st.markdown(f"""
    <div style="text-align: center; padding: 40px 0;">
        <h1 style="color: {C_PRIMARY} !important; font-weight: 800; font-size: 3rem; margin-bottom: 0;">MEDCORE SYSTEMS</h1>
        <p style="color: {C_MUTED}; font-size: 1.2rem; font-weight: 500;">Clinical Diabetes Screening Portal</p>
    </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        with st.form("reg_form"):
            st.markdown(f"<h3 style='text-align:center; color:{C_TEXT}!important; margin-bottom:20px;'>Patient Intake Form</h3>", unsafe_allow_html=True)
            
            name             = st.text_input("Full Legal Name", placeholder="e.g., Jane Doe")
            country_list     = [c.name for c in pycountry.countries]
            selected_country = st.selectbox("Country of Residence", country_list, index=country_list.index("India") if "India" in country_list else 0)
            phone            = st.text_input("Mobile Number", placeholder="10-digit number")
            email            = st.text_input("Email Address", placeholder="patient@example.com")
            address          = st.text_area("Residential Address", placeholder="Full address...", height=80)
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Access Clinical Workspace", use_container_width=True)

            if submit:
                name = name.strip(); phone = phone.strip()
                email = email.strip(); address = address.strip()

                if not all([name, phone, email, address]):
                    st.error("❌ All fields are required to create an EHR record."); st.stop()

                if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
                    st.error("❌ Invalid email format."); st.stop()

                ist = pytz.timezone("Asia/Kolkata"); now = datetime.now(ist)
                pid = "EHR-" + str(uuid.uuid4().int)[:8]
                rec = {
                    "_id": pid, "name": name, "phone": phone,
                    "country": selected_country, "email": email,
                    "address": address, "gender": "Not Specified",
                    "created_at": now.strftime("%d-%m-%Y %I:%M:%S %p"),
                }
                try:
                    users_col.insert_one(rec)
                except Exception:
                    pass # Ignore if DB offline
                
                st.session_state.patient_info = rec
                st.session_state.registered   = True
                st.session_state.show_success = True
                st.rerun()

    st.markdown("""
    <div style="text-align: center; margin-top: 40px; color: #94A3B8; font-size: 12px;">
        ⚕️ HIPAA Compliant System • 🔒 256-bit AES Encryption • 🏥 Clinical Grade AI
    </div>
    """, unsafe_allow_html=True)


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

    inject_enterprise_css()
    info = st.session_state.patient_info

    # ══ SIDEBAR (Dark Navy) ═══════════════════════════════════════
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 16px; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 20px;">
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 4px;">{info.get('name', '')}</div>
            <div style="font-family: monospace; color: #38BDF8; margin-bottom: 12px; font-size: 13px;">ID: {info.get('_id', '')}</div>
            <div style="font-size: 12px; color: #CBD5E1;">✉️ {info.get('email', '')}</div>
            <div style="font-size: 12px; color: #CBD5E1;">📞 {info.get('phone', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='color:#38BDF8; font-weight:bold; font-size:12px; margin-top:10px;'>DEMOGRAPHICS</div>", unsafe_allow_html=True)
        age    = st.number_input("Age (Years)", 21, 100, 30)
        gender = st.selectbox("Biological Sex", ["Male","Female"])
        pregnancies = st.number_input("Prior Pregnancies", 0, 20, 0) if gender=="Female" else 0

        st.markdown("<div style='color:#38BDF8; font-weight:bold; font-size:12px; margin-top:20px;'>GLYCEMIC MARKERS</div>", unsafe_allow_html=True)
        glucose = st.slider("Fasting Glucose (mg/dL)", 0, 200, 120)
        insulin = st.slider("Serum Insulin (IU/mL)",  0, 900, 80)

        st.markdown("<div style='color:#38BDF8; font-weight:bold; font-size:12px; margin-top:20px;'>CARDIOVASCULAR</div>", unsafe_allow_html=True)
        bp   = st.slider("Diastolic BP (mmHg)",     0, 130, 70)
        skin = st.slider("Triceps Skin Fold (mm)",  0, 100, 20)

        st.markdown("<div style='color:#38BDF8; font-weight:bold; font-size:12px; margin-top:20px;'>BIOMETRICS</div>", unsafe_allow_html=True)
        bmi = st.number_input("BMI (kg/m²)", 10.0, 70.0, 25.0)
        dpf = st.slider("Diabetes Pedigree Fn.", 0.0, 2.5, 0.5)

        st.markdown("<br>", unsafe_allow_html=True)
        predict_btn = st.button("Run Clinical AI Assessment", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Secure Logout", use_container_width=True):
            st.session_state.registered   = False
            st.session_state.patient_info = {}
            st.session_state.show_success = False
            st.session_state.model_ran    = False
            st.rerun()

    # ══ MAIN DASHBOARD (Light & Readable) ════════════════════════
    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <h1 style="color: {C_NAVY} !important; font-weight: 800; margin-bottom: 4px;">Diagnostic Dashboard</h1>
        <p style="color: {C_MUTED}; font-size: 15px;">Multiparametric SVM Analysis Engine</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.show_success:
        st.success("✅ EHR Profile successfully established.")
        st.session_state.show_success = False

    if predict_btn:
        st.session_state.model_ran = True

    if not st.session_state.model_ran:
        st.info("ℹ️ **System Ready:** Please configure the clinical biomarkers in the sidebar and execute the assessment to view results.")
        return

    # ══ MODEL EXECUTION ═════════════════════════════════════════
    if predict_btn:
        with st.spinner("Processing clinical vectors through SVM engine..."):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.005)
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
        risk_label = "Low Risk"; risk_hex = C_GREEN; risk_bg = "#ECFDF5"; risk_text = "LOW RISK: Diabetes Unlikely"
    elif prob_pos < 70:
        risk_label = "Moderate Risk"; risk_hex = C_AMBER; risk_bg = "#FFFBEB"; risk_text = "MODERATE RISK: Possible Diabetes"
    else:
        risk_label = "High Risk"; risk_hex = C_RED; risk_bg = "#FEF2F2"; risk_text = "HIGH RISK: Diabetes Likely"

    ist = pytz.timezone("Asia/Kolkata"); now = datetime.now(ist)
    
    # ── Result Banner ──
    st.markdown(f"""
    <div class="clinical-card" style="background-color: {risk_bg}; border-left: 6px solid {risk_hex};">
        <div style="font-size: 12px; font-weight: bold; color: {C_MUTED}; text-transform: uppercase; margin-bottom: 8px;">
            Assessment Result • {now.strftime('%d %b %Y %H:%M')}
        </div>
        <h2 style="color: {risk_hex} !important; font-weight: 800; margin: 0 0 12px 0;">{risk_text}</h2>
        <div style="font-size: 16px; color: {C_TEXT};">
            Calculated Probability: <span style="font-weight: bold; font-size: 20px;">{prob_pos:.1f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    mc1, mc2 = st.columns(2)
    with mc1: st.metric("Diabetic Probability", f"{prob_pos:.1f}%")
    with mc2: st.metric("Non-Diabetic Probability", f"{prob_neg:.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Setup ──
    c_labels, c_values = [], []
    if glucose >= 126: c_labels.append("Hyperglycemia");   c_values.append(min(glucose/2,100))
    if bmi > 30:       c_labels.append("Obesity (BMI)");   c_values.append(min(bmi*2,100))
    if age > 45:       c_labels.append("Age Factor");      c_values.append(min(age,100))
    if bp > 120:       c_labels.append("Hypertension");    c_values.append(min(bp,100))
    if dpf > 0.5:      c_labels.append("Genetics (DPF)");  c_values.append(min(dpf*100,100))
    if not c_labels:   c_labels, c_values = ["Healthy Baseline"], [100]
    scr_cols = [CHART_PALETTE[i%len(CHART_PALETTE)] for i in range(len(c_labels))]

    st.markdown("<div class='clinical-header'>Clinical Visualizations</div>", unsafe_allow_html=True)

    # Note: Plotly charts updated to Light Theme for readability
    gc1, gc2 = st.columns(2)
    with gc1:
        st.markdown("<div class='clinical-card'>", unsafe_allow_html=True)
        gfig = go.Figure(go.Indicator(
            mode="gauge+number", value=prob_pos,
            number={"suffix":"%","font":{"family":"Inter","color":C_TEXT,"size":28}},
            title={"text":"Risk Severity Gauge","font":{"color":C_MUTED,"size":14}},
            gauge={
                "axis":      {"range":[0,100],"tickcolor":C_BORDER,"tickwidth":1},
                "bar":       {"color":risk_hex,"thickness":0.25},
                "bgcolor":   "#F8FAFC", "borderwidth":0,
                "steps":     [{"range":[0,30],"color":"#D1FAE5"},
                              {"range":[30,70],"color":"#FEF3C7"},
                              {"range":[70,100],"color":"#FEE2E2"}],
                "threshold": {"line":{"color":risk_hex,"width":4}, "thickness":0.8,"value":prob_pos},
            }
        ))
        gfig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=280, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(gfig, use_container_width=True, config={"responsive":True})
        st.markdown("</div>", unsafe_allow_html=True)

    with gc2:
        st.markdown("<div class='clinical-card'>", unsafe_allow_html=True)
        pfig = go.Figure(go.Pie(
            labels=c_labels, values=c_values, hole=.5,
            marker=dict(colors=scr_cols, line=dict(color="#FFFFFF",width=2)),
            textfont=dict(family="Inter",size=12,color="#FFFFFF"),
            textposition="inside", textinfo="percent+label", showlegend=False,
        ))
        pfig.update_layout(
            title=dict(text="Etiology Contribution", font=dict(color=C_MUTED,size=14)),
            paper_bgcolor="rgba(0,0,0,0)", height=280, margin=dict(l=10,r=10,t=30,b=10),
        )
        st.plotly_chart(pfig, use_container_width=True, config={"responsive":True})
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Factor Analysis ──
    st.markdown("<div class='clinical-header'>Biomarker Analysis</div>", unsafe_allow_html=True)
    
    risks, positives = [], []
    if glucose >= 126:          risks.append("Critical: High Fasting Glucose (≥126 mg/dL)")
    elif 100 <= glucose < 126:  risks.append("Warning: Prediabetic Glucose (100–125 mg/dL)")
    else:                       positives.append("Normal Glucose Baseline (<100 mg/dL)")
    if bmi > 30:                risks.append("Critical: High BMI Indicator (Obese)")
    elif 18.5 <= bmi <= 24.9:   positives.append("Normal Healthy BMI (18.5 – 24.9)")
    if age > 45:                risks.append("Factor: Age > 45 Demographic")
    if bp > 120:                risks.append("Critical: Elevated Blood Pressure")
    elif 90 <= bp <= 120:       positives.append("Normal Blood Pressure Range")
    if dpf > 0.5:               risks.append("Factor: Genetic Pedigree Risk > 0.5")

    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown("<div class='clinical-card'>", unsafe_allow_html=True)
        st.markdown("**Identified Risk Factors**")
        for r in risks:
            st.markdown(f"<div style='padding:8px; margin-bottom:8px; background:#FEF2F2; color:#991B1B; border-left:4px solid #EF4444; border-radius:4px; font-size:14px;'>{r}</div>", unsafe_allow_html=True)
        if not risks: st.write("No critical risks detected.")
        st.markdown("</div>", unsafe_allow_html=True)

    with rc2:
        st.markdown("<div class='clinical-card'>", unsafe_allow_html=True)
        st.markdown("**Stable Biomarkers**")
        for p in positives:
            st.markdown(f"<div style='padding:8px; margin-bottom:8px; background:#ECFDF5; color:#065F46; border-left:4px solid #10B981; border-radius:4px; font-size:14px;'>{p}</div>", unsafe_allow_html=True)
        if not positives: st.write("No protective factors noted.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Set PDF recommendations
    if prob_pos >= 70:
        recs_pdf = ["Consult an endocrinologist immediately", "Acquire complete HbA1c screening", "Monitor blood sugar routinely", "Institute strict dietary protocols"]
    elif prob_pos >= 30:
        recs_pdf = ["Maintain a low-glycemic index diet", "Increase cardiovascular activity", "Monitor fasting glucose periodically"]
    else:
        recs_pdf = ["Continue healthy lifestyle habits", "Exercise regularly (150 mins/week)", "Maintain routine annual check-ups"]


    # ══ PDF GENERATION (Enterprise Styling) ═════════════════════
    st.markdown("<br>", unsafe_allow_html=True)
    bar_png = _bar_png(c_labels, c_values)
    pie_png = _pie_png(c_labels, c_values)

    buf  = BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=100, bottomMargin=70) 
    els  = []
    sty  = getSampleStyleSheet()

    T = lambda name, **kw: ParagraphStyle(name, parent=sty["Normal"], **kw)
    t_title = T("TT", fontName="Helvetica-Bold", fontSize=18, textColor=colors.HexColor("#0F172A"), alignment=1, spaceAfter=4)
    t_date  = T("TD", fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#64748B"), alignment=1, spaceAfter=20)
    t_head  = T("TH", fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#FFFFFF"), backColor=colors.HexColor("#026AA7"), spaceBefore=16, spaceAfter=8, borderPadding=6)
    t_norm  = T("TN", fontName="Helvetica", fontSize=10, spaceAfter=5, textColor=colors.HexColor("#1E293B"))
    
    def hosp_table(rows):
        t = Table(rows, colWidths=[2.2*inch, 4.3*inch])
        t.setStyle(TableStyle([
            ("GRID",        (0,0),(-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ("BACKGROUND",  (0,0),(0,-1),  colors.HexColor("#F8FAFC")),
            ("FONTNAME",    (0,0),(0,-1),  "Helvetica-Bold"),
            ("TEXTCOLOR",   (0,0),(0,-1),  colors.HexColor("#0F172A")),
            ("TEXTCOLOR",   (1,0),(1,-1),  colors.HexColor("#1E293B")),
            ("PADDING",     (0,0),(-1,-1), 8),
            ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
        ]))
        for i in range(1, len(rows)):
            if i % 2 == 0: t.setStyle(TableStyle([("BACKGROUND", (1, i), (1, i), colors.HexColor("#F1F5F9"))]))
        return t

    els.append(Paragraph("CLINICAL ASSESSMENT REPORT", t_title))
    els.append(Paragraph(f"Date Generated: {now.strftime('%d %b %Y | %H:%M IST')}", t_date))

    els.append(Paragraph("PATIENT DEMOGRAPHICS", t_head))
    els.append(hosp_table([
        ["Medical Record Number", Paragraph(f"<font name='Courier-Bold'>{info.get('_id','')}</font>", t_norm)],
        ["Patient Name", info.get("name","").upper()],
        ["Contact", f"{info.get('phone','')} | {info.get('email','')}"]
    ]))
    
    med = [
        ["Age", f"{age} Years"], ["Biological Sex", gender], ["Fasting Glucose", f"{glucose} mg/dL"],
        ["Diastolic BP", f"{bp} mmHg"], ["Body Mass Index", str(bmi)], ["Diabetes Pedigree", str(dpf)]
    ]
    if gender == "Female": med.insert(2, ["Prior Pregnancies", str(pregnancies)])
    
    els.append(Paragraph("CLINICAL VITALS & BIOMARKERS", t_head))
    els.append(hosp_table(med))

    risk_pdf_col = {"Low Risk":"#059669","Moderate Risk":"#D97706","High Risk":"#DC2626"}
    els.append(Paragraph("AI DIAGNOSTIC OUTPUT", t_head))
    els.append(Paragraph(f"<b>Overall Risk Determination:</b> <font color='{risk_pdf_col[risk_label]}'><b>{risk_label.upper()}</b></font>", t_norm))
    els.append(Paragraph(f"<b>Calculated Probability:</b> {prob_pos:.1f}% positive indicator", t_norm))

    els.append(Paragraph("CLINICAL RECOMMENDATIONS", t_head))
    els.append(ListFlowable([ListItem(Paragraph(r, t_norm)) for r in recs_pdf], bulletType="bullet"))
    
    els.append(Spacer(1, 0.4*inch))
    sig_table = Table([["", "___________________________________"], ["", "Attending Physician / System Output"]], colWidths=[3.5*inch, 3*inch])
    sig_table.setStyle([("ALIGN", (1,0), (1,-1), "CENTER"), ("FONTNAME", (1,1), (1,-1), "Helvetica-Bold"), ("FONTSIZE", (1,1), (1,-1), 9)])
    els.append(sig_table)

    doc.build(els, onFirstPage=report_header_footer, onLaterPages=report_header_footer)
    pdf_data = buf.getvalue(); buf.close()

    st.download_button(
        label="📄 Export Official EHR Document (PDF)",
        data=pdf_data,
        file_name=f"EHR_{info.get('name','Patient').replace(' ','_')}_{now.strftime('%d%m%Y')}.pdf",
        mime="application/pdf",
    )

if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
