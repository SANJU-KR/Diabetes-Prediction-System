# -----------------------------
# Import Required Libraries
# -----------------------------
import streamlit as st
import numpy as np
import joblib
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
    except FileNotFoundError:
        return ""

def country_to_flag(country_code):
    return "".join(chr(127397 + ord(char)) for char in country_code.upper())

# PDF imports - canvas-based for real hospital layout
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
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
st.set_page_config(
    page_title="Diabetes Prediction System",
    page_icon="🩺",
    layout="wide"
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
# HOSPITAL PDF BUILDER  (canvas-based, A4, real layout)
# =====================================================
_BAR_COLORS = ["#dc2626", "#d97706", "#2563eb", "#7c3aed", "#047857"]

def _make_bar_buf(labels, values):
    fig, ax = plt.subplots(figsize=(4.6, 3.0), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f8fafc")
    cols = [_BAR_COLORS[i % len(_BAR_COLORS)] for i in range(len(labels))]
    bars = ax.bar(labels, values, color=cols, edgecolor="white", linewidth=1.5, zorder=3)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{val:.0f}", ha="center", va="bottom",
                fontsize=8.5, fontweight="bold", color="#1e293b")
    ax.set_ylim(0, max(values) * 1.35 if values else 110)
    ax.set_title("Risk Severity", fontsize=11, fontweight="bold", color="#0f172a", pad=8)
    ax.set_xlabel("Causes", fontsize=8.5, color="#64748b", labelpad=4)
    ax.set_ylabel("Severity Level", fontsize=8.5, color="#64748b", labelpad=4)
    ax.tick_params(axis="x", labelsize=8, colors="#64748b", rotation=15)
    ax.tick_params(axis="y", labelsize=8, colors="#64748b")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#e2e8f0")
    ax.yaxis.grid(True, color="#e2e8f0", linewidth=0.6, linestyle="--", zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout(pad=0.9)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=160, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf

def _make_pie_buf(labels, values):
    fig, ax = plt.subplots(figsize=(4.4, 3.0), dpi=160)
    fig.patch.set_facecolor("white")
    cols = [_BAR_COLORS[i % len(_BAR_COLORS)] for i in range(len(labels))]
    wedges, texts, autos = ax.pie(
        values, labels=None, colors=cols,
        autopct="%1.0f%%", startangle=140,
        wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.0),
        pctdistance=0.78,
    )
    for at in autos:
        at.set_fontsize(8); at.set_fontweight("bold"); at.set_color("white")
    ax.legend(wedges, labels, loc="lower center",
              bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=7.5, frameon=False)
    ax.set_title("Percentage Contribution", fontsize=11,
                 fontweight="bold", color="#0f172a", pad=8)
    plt.tight_layout(pad=0.9)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=160, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def build_hospital_pdf(info, age, gender, glucose, bp, skin, insulin, bmi, dpf,
                        pregnancies, prob_positive, risk_label, current_time,
                        cause_labels, cause_values, recs_for_pdf):
    """Canvas-based A4 hospital report — clean, aligned, professional."""
    W, H = A4
    M  = 17 * mm     # left/right margin
    CW = W - 2 * M   # content width

    # ── PDF colour palette ───────────────────────────────────
    NAVY    = rl_colors.HexColor("#0a1f3d")
    TEAL    = rl_colors.HexColor("#006e8c")
    WHITE   = rl_colors.white
    BLACK   = rl_colors.HexColor("#0f172a")
    GRY_T   = rl_colors.HexColor("#475569")
    GRY_L   = rl_colors.HexColor("#f1f5f9")
    GRY_R   = rl_colors.HexColor("#cbd5e1")
    ROW_ALT = rl_colors.HexColor("#eef4f8")
    GREEN_C = rl_colors.HexColor("#047857")
    GREEN_B = rl_colors.HexColor("#ecfdf5")
    AMBR_C  = rl_colors.HexColor("#d97706")
    AMBR_B  = rl_colors.HexColor("#fffbeb")
    RED_C   = rl_colors.HexColor("#b91c1c")
    RED_B   = rl_colors.HexColor("#fef2f2")

    buf = BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)

    # ── HEADER BAND ─────────────────────────────────────────
    BH = 28 * mm
    c.setFillColor(NAVY)
    c.rect(0, H - BH, W, BH, fill=1, stroke=0)

    # Left: clinic name + subtitle
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 13.5)
    c.drawString(M, H - 10 * mm, "Diabetes Prediction System")
    c.setFillColor(rl_colors.HexColor("#93c5fd")); c.setFont("Helvetica", 7.5)
    c.drawString(M, H - 16.5 * mm,
                 "AI-Powered Clinical Risk Assessment  ·  SVM Architecture")

    # Right: report meta  (patient ID shown WITHOUT hyphen)
    pid_display = info.get('_id', 'N/A').replace('-', '')
    c.setFillColor(rl_colors.HexColor("#93c5fd")); c.setFont("Helvetica", 7.5)
    c.drawRightString(W - M, H - 9 * mm,  f"Report ID: {pid_display}")
    c.drawRightString(W - M, H - 15 * mm,
                      f"Generated: {current_time.strftime('%d %B %Y | %I:%M %p (IST)')}")
    c.drawRightString(W - M, H - 21 * mm, "CONFIDENTIAL MEDICAL DOCUMENT")

    y = H - BH - 8 * mm

    # ── PAGE TITLE ───────────────────────────────────────────
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W / 2, y, "DIABETES RISK PREDICTION REPORT")
    y -= 3.5 * mm
    c.setStrokeColor(TEAL); c.setLineWidth(2)
    c.line(M, y, W - M, y)
    y -= 8 * mm

    # ── HELPERS ──────────────────────────────────────────────
    def sec_head(cx, cy, label, w):
        """Teal section heading bar; returns y after bar."""
        c.setFillColor(TEAL)
        c.rect(cx, cy - 6 * mm, w, 6 * mm, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 8.5)
        c.drawString(cx + 3 * mm, cy - 4 * mm, label.upper())
        return cy - 6 * mm

    CELL_H = 14 * mm   # height of each grid cell (label + value)

    def grid_cell(cx, cy, label, value, cw, shade, last_col=False, last_row=False):
        """Draw one label-over-value cell inside a grid table."""
        # background
        c.setFillColor(ROW_ALT if shade else WHITE)
        c.rect(cx, cy - CELL_H, cw, CELL_H, fill=1, stroke=0)
        # right border (vertical divider) — skip for last column
        c.setStrokeColor(GRY_R); c.setLineWidth(0.4)
        if not last_col:
            c.line(cx + cw, cy - CELL_H, cx + cw, cy)
        # bottom border
        c.line(cx, cy - CELL_H, cx + cw, cy - CELL_H)
        # label (small caps, muted)
        c.setFillColor(GRY_T); c.setFont("Helvetica-Bold", 7)
        c.drawString(cx + 2.5 * mm, cy - 5 * mm, str(label).upper())
        # value (larger, dark)
        c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 8.5)
        v = str(value)
        # truncate if too wide
        max_w = cw - 5 * mm
        while c.stringWidth(v, "Helvetica-Bold", 8.5) > max_w and len(v) > 4:
            v = v[:-3] + ".."
        c.drawString(cx + 2.5 * mm, cy - 11 * mm, v)

    def outer_border(cx, cy, w, h):
        """Draw outer border rect around a grid block."""
        c.setStrokeColor(TEAL); c.setLineWidth(0.8)
        c.rect(cx, cy - h, w, h, fill=0, stroke=1)

    # ── PATIENT PROFILE  —  3-column grid ───────────────────
    # 6 fields  →  2 rows × 3 cols
    pid_no_hyphen = info.get("_id", "N/A").replace("-", "")
    p_fields = [
        ("Patient ID",    pid_no_hyphen),
        ("Full Name",     info.get("name", "N/A")),
        ("Phone Number",  info.get("phone", "N/A")),
        ("Email Address", info.get("email", "N/A")),
        ("Country",       info.get("country", "N/A")),
        ("Address",       info.get("address", "N/A")[:38] +
                          ("…" if len(info.get("address", "")) > 38 else "")),
    ]

    NCOLS_P  = 3
    CELL_W_P = CW / NCOLS_P
    NROWS_P  = 2   # ceil(6 / 3)
    P_H      = NROWS_P * CELL_H

    y = sec_head(M, y, "Patient Profile", CW) - 0 * mm
    for idx, (lbl, val) in enumerate(p_fields):
        row = idx // NCOLS_P
        col = idx %  NCOLS_P
        cx  = M + col * CELL_W_P
        cy  = y - row * CELL_H
        shade    = (row % 2 == 0)
        last_col = (col == NCOLS_P - 1)
        grid_cell(cx, cy, lbl, val, CELL_W_P, shade, last_col=last_col)
    outer_border(M, y, CW, P_H)
    y -= P_H + 7 * mm

    # ── CLINICAL INPUTS  —  4-column grid ───────────────────
    # build field list (8 or 9 if Female)
    cl_fields = [
        ("Age",             f"{age} yrs"),
        ("Gender",          gender),
        ("Glucose Level",   f"{glucose} mg/dL"),
        ("Blood Pressure",  f"{bp} mmHg"),
        ("Skin Thickness",  f"{skin} mm"),
        ("Insulin Level",   f"{insulin} IU/mL"),
        ("BMI",             str(bmi)),
        ("DPF",             str(dpf)),
    ]
    if gender == "Female":
        cl_fields.insert(2, ("Pregnancies", str(pregnancies)))

    import math
    NCOLS_C  = 4
    NROWS_C  = math.ceil(len(cl_fields) / NCOLS_C)
    CELL_W_C = CW / NCOLS_C
    C_H      = NROWS_C * CELL_H

    y = sec_head(M, y, "Clinical Inputs", CW) - 0 * mm
    for idx, (lbl, val) in enumerate(cl_fields):
        row = idx // NCOLS_C
        col = idx %  NCOLS_C
        cx  = M + col * CELL_W_C
        cy  = y - row * CELL_H
        shade    = (row % 2 == 0)
        last_col = (col == NCOLS_C - 1) or (idx == len(cl_fields) - 1)
        grid_cell(cx, cy, lbl, val, CELL_W_C, shade, last_col=last_col)
    outer_border(M, y, CW, C_H)
    y -= C_H + 8 * mm

    # ── RISK RESULT BANNER ───────────────────────────────────
    if prob_positive < 30:
        BC, BG, BT = GREEN_C, GREEN_B, "LOW RISK  —  Diabetes Unlikely"
    elif prob_positive < 70:
        BC, BG, BT = AMBR_C, AMBR_B, "MODERATE RISK  —  Possible Diabetes"
    else:
        BC, BG, BT = RED_C,  RED_B,  "HIGH RISK  —  Diabetes Likely"

    BANh = 15 * mm
    # left accent strip
    c.setFillColor(BC); c.rect(M, y - BANh, 3 * mm, BANh, fill=1, stroke=0)
    # background fill
    c.setFillColor(BG); c.rect(M + 3 * mm, y - BANh, CW - 3 * mm, BANh, fill=1, stroke=0)
    # border
    c.setStrokeColor(BC); c.setLineWidth(0.9)
    c.rect(M, y - BANh, CW, BANh, fill=0, stroke=1)
    # text
    c.setFillColor(BC); c.setFont("Helvetica-Bold", 12)
    c.drawString(M + 6 * mm, y - 7 * mm, BT)
    c.setFillColor(GRY_T); c.setFont("Helvetica", 8)
    c.drawString(M + 6 * mm, y - 12.5 * mm,
        f"Risk Percentage: {prob_positive:.1f}%   |   MEDCORE AI · SVM Engine   |   "
        f"{current_time.strftime('%d %B %Y | %I:%M %p (IST)')}")
    y -= BANh + 7 * mm

    # ── DATA VISUALIZATION ───────────────────────────────────
    y = sec_head(M, y, "Data Visualization & Analysis", CW) - 2 * mm
    CH = 57 * mm
    CW2 = (CW - 4 * mm) / 2

    bar_reader = ImageReader(_make_bar_buf(cause_labels, cause_values))
    pie_reader = ImageReader(_make_pie_buf(cause_labels, cause_values))
    c.drawImage(bar_reader, M,            y - CH, width=CW2, height=CH,
                preserveAspectRatio=True, anchor="c")
    c.drawImage(pie_reader, M + CW2 + 4 * mm, y - CH, width=CW2, height=CH,
                preserveAspectRatio=True, anchor="c")
    # frame around charts
    c.setStrokeColor(GRY_R); c.setLineWidth(0.5)
    c.rect(M, y - CH, CW, CH, fill=0, stroke=1)
    y -= CH + 7 * mm

    # ── RISK FACTOR ANALYSIS ─────────────────────────────────
    y = sec_head(M, y, "Risk Factor Analysis", CW) - 2 * mm
    RFH = 6 * mm

    risk_factors, positive_factors = [], []
    if glucose >= 126:         risk_factors.append("High Glucose Level (≥126 mg/dL)")
    elif 100 <= glucose < 126: risk_factors.append("Prediabetic Glucose Level (100-125 mg/dL)")
    else:                      positive_factors.append("Normal Glucose Level (<100 mg/dL)")
    if bmi > 30:               risk_factors.append("High BMI (Obesity)")
    elif 18.5 <= bmi <= 24.9:  positive_factors.append("Healthy BMI")
    if age > 45:               risk_factors.append("Age above 45")
    if bp > 120:               risk_factors.append("High Blood Pressure (>120 mmHg)")
    elif 90 <= bp <= 120:      positive_factors.append("Normal Blood Pressure")
    if dpf > 0.5:              risk_factors.append("Higher Genetic Risk")

    for item in risk_factors:
        c.setFillColor(rl_colors.HexColor("#fff1f2"))
        c.rect(M, y - RFH, CW, RFH, fill=1, stroke=0)
        c.setFillColor(RED_C); c.rect(M, y - RFH, 2.5 * mm, RFH, fill=1, stroke=0)
        c.setFillColor(rl_colors.HexColor("#991b1b")); c.setFont("Helvetica-Bold", 8.2)
        c.drawString(M + 5 * mm, y - 4 * mm, f"  {item}")
        c.setStrokeColor(GRY_R); c.setLineWidth(0.3)
        c.line(M, y - RFH, M + CW, y - RFH)
        y -= RFH + 1 * mm

    for item in positive_factors:
        c.setFillColor(rl_colors.HexColor("#f0fdf4"))
        c.rect(M, y - RFH, CW, RFH, fill=1, stroke=0)
        c.setFillColor(GREEN_C); c.rect(M, y - RFH, 2.5 * mm, RFH, fill=1, stroke=0)
        c.setFillColor(rl_colors.HexColor("#065f46")); c.setFont("Helvetica-Bold", 8.2)
        c.drawString(M + 5 * mm, y - 4 * mm, f"  {item}")
        c.setStrokeColor(GRY_R); c.setLineWidth(0.3)
        c.line(M, y - RFH, M + CW, y - RFH)
        y -= RFH + 1 * mm

    y -= 5 * mm

    # ── MEDICAL RECOMMENDATIONS ──────────────────────────────
    y = sec_head(M, y, "Medical Recommendations", CW) - 3 * mm
    for r in recs_for_pdf:
        c.setFillColor(BLACK); c.setFont("Helvetica", 8.5)
        c.drawString(M + 5 * mm, y - 4 * mm, f"  \u2022   {r}")
        y -= 6.5 * mm

    # ── FOOTER ──────────────────────────────────────────────
    FH = 13 * mm
    c.setFillColor(GRY_L); c.rect(0, 0, W, FH, fill=1, stroke=0)
    c.setStrokeColor(GRY_R); c.setLineWidth(0.5); c.line(0, FH, W, FH)
    c.setFillColor(GRY_T); c.setFont("Helvetica-Oblique", 7)
    c.drawString(M, 9 * mm,
        "MEDICAL DISCLAIMER: This report is AI-generated and does not replace professional medical advice.")
    c.drawString(M, 5 * mm,
        "Consult a qualified healthcare professional for clinical diagnosis, interpretation, and treatment.")
    c.setFont("Helvetica", 7)
    c.drawRightString(W - M, 7 * mm,
        f"Diabetes Prediction System  |  {current_time.strftime('%d %B %Y')}  |  Page 1 of 1")

    c.save()
    return buf.getvalue()


# =====================================================
# REGISTRATION PAGE
# =====================================================
def registration_page():
    img = get_base64_image("health.png")

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Syne:wght@700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── BACKGROUND ── */
.stApp {{
    background: linear-gradient(rgba(2,6,18,0.72), rgba(2,6,18,0.72)),
                url("data:image/jpg;base64,{img}") center/cover fixed;
    font-family: 'DM Sans', sans-serif;
}}
#MainMenu, footer, header, .stDeployButton {{ display: none !important; }}

/* ── TITLE ── */
h1 {{
    font-family: 'Syne', sans-serif !important;
    color: #ffffff !important;
    text-align: center;
    font-weight: 800;
    font-size: clamp(2rem, 4.5vw, 3rem);
    letter-spacing: -0.03em;
    margin-bottom: 6px;
    background: linear-gradient(110deg, #ffffff 20%, #67e8f9 60%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

/* ── SUBTITLE ── */
.stMarkdown p {{
    color: #94a3b8 !important;
    text-align: center;
    font-size: 15px;
    font-weight: 400;
    letter-spacing: 0.03em;
}}

/* ── FORM CARD ── */
div[data-testid="stForm"] {{
    background: rgba(8, 15, 36, 0.82) !important;
    backdrop-filter: blur(28px) saturate(1.4);
    -webkit-backdrop-filter: blur(28px);
    border-radius: 24px !important;
    padding: 44px 40px !important;
    width: 100%;
    max-width: 700px;
    margin: 4vh auto;
    border: 1px solid rgba(103, 232, 249, 0.18) !important;
    box-shadow: 0 32px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04);
    position: relative;
    overflow: hidden;
}}
div[data-testid="stForm"]::before {{
    content: '';
    position: absolute; top: 0; left: 25%; right: 25%; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(103,232,249,0.6), transparent);
}}

/* ── FORM LABELS ── */
div[data-testid="stForm"] label {{
    color: #94a3b8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    text-shadow: none !important;
}}

/* ── FORM INPUTS — dark glass ── */
div[data-testid="stForm"] div[data-baseweb="input"] > div,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div,
div[data-testid="stForm"] div[data-baseweb="select"] > div {{
    background: rgba(255, 255, 255, 0.06) !important;
    backdrop-filter: blur(10px);
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    transition: all 0.25s ease;
}}
div[data-testid="stForm"] div[data-baseweb="input"] > div:focus-within,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div:focus-within,
div[data-testid="stForm"] div[data-baseweb="select"] > div:focus-within {{
    border: 1px solid rgba(103, 232, 249, 0.55) !important;
    box-shadow: 0 0 0 3px rgba(103, 232, 249, 0.12) !important;
    background: rgba(255, 255, 255, 0.09) !important;
}}
div[data-testid="stForm"] input,
div[data-testid="stForm"] textarea {{
    color: #e2e8f0 !important;
    -webkit-text-fill-color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    font-weight: 500 !important;
}}
div[data-testid="stForm"] input::placeholder,
div[data-testid="stForm"] textarea::placeholder {{
    color: #475569 !important;
}}
div[data-testid="stForm"] div[data-baseweb="select"] span {{
    color: #e2e8f0 !important;
}}

/* ── REGISTER BUTTON ── */
div[data-testid="stForm"] button {{
    background: linear-gradient(135deg, #0891b2 0%, #1d4ed8 100%) !important;
    color: white !important;
    border-radius: 12px !important;
    height: 52px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    border: none !important;
    box-shadow: 0 4px 24px rgba(8,145,178,0.35) !important;
    transition: all 0.25s ease !important;
}}
div[data-testid="stForm"] button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(8,145,178,0.5) !important;
}}

/* ── DROPDOWN POPUP ── */
div[data-baseweb="popover"] {{
    background: #0f172a !important;
    border: 1px solid rgba(103,232,249,0.18);
    border-radius: 12px;
}}
ul[role="listbox"] {{ background: #0f172a !important; }}
li[role="option"] {{ color: #94a3b8 !important; }}
li[role="option"]:hover {{ background: rgba(103,232,249,0.10) !important; color: #67e8f9 !important; }}

/* ── ALERTS ── */
div[data-testid="stSuccess"] {{
    background: rgba(4,120,87,0.12) !important;
    border: 1px solid rgba(4,120,87,0.4) !important;
    border-radius: 12px !important;
}}
div[data-testid="stSuccess"] p {{ color: #6ee7b7 !important; font-weight: 600; }}
div[data-testid="stError"] {{
    background: rgba(185,28,28,0.12) !important;
    border: 1px solid rgba(185,28,28,0.4) !important;
    border-radius: 12px !important;
}}
div[data-testid="stError"] p {{ color: #fca5a5 !important; font-weight: 600; }}

@media (max-width: 768px) {{
    div[data-testid="stForm"] {{ padding: 24px 18px !important; }}
    h1 {{ font-size: 1.8rem !important; }}
}}
</style>
""", unsafe_allow_html=True)

    st.title("📝 Patient Registration")
    st.markdown("Please register to access the Diabetes Prediction System")

    col1, col2, col3 = st.columns([1, 2, 1])
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
                    formatted_phone = phonenumbers.format_number(
                        parsed_number, phonenumbers.PhoneNumberFormat.E164)
                except:
                    st.error("❌ Invalid phone number format")
                    return

                ist = pytz.timezone("Asia/Kolkata")
                current_time = datetime.now(ist)
                patient_id = "PAT" + str(uuid.uuid4().int)[:6]  # no hyphen

                user_data = {
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
                st.session_state.patient_info = user_data
                st.session_state.registered = True
                st.session_state.show_success = True
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

    img = get_base64_image("health22.png")

    # ── MASTER CSS ───────────────────────────────────────────
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Syne:wght@700;800&family=JetBrains+Mono:wght@400;600&display=swap');

.stApp {{
    background: linear-gradient(rgba(2,6,18,0.78), rgba(2,6,18,0.78)),
                url("data:image/png;base64,{img}") center/cover fixed;
    font-family: 'DM Sans', sans-serif;
}}
#MainMenu, footer, header, .stDeployButton {{ display: none !important; }}
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-thumb {{ background: rgba(8,145,178,.45); border-radius: 99px; }}

/* ── GLOBAL HEADINGS ── */
h1, h2, h3 {{ color: white !important; font-family: 'Syne', sans-serif !important; letter-spacing: -0.02em; }}
p, li {{ color: #e2e8f0 !important; font-size: clamp(14px, 1.8vw, 18px); }}
ul {{ line-height: 1.8; }}

/* ══════════════════════════════════
   SIDEBAR
══════════════════════════════════ */
section[data-testid="stSidebar"] {{
    background: rgba(2, 6, 18, 0.94) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border-right: 1px solid rgba(8,145,178,0.15) !important;
    box-shadow: 6px 0 40px rgba(0,0,0,0.5) !important;
}}
section[data-testid="stSidebar"] > div {{ padding-top: 10px !important; }}

/* Sidebar text */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    color: #e2e8f0 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
}}
section[data-testid="stSidebar"] label {{
    color: #64748b !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.13em !important;
    text-transform: uppercase !important;
    font-weight: 600 !important;
}}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {{
    color: #94a3b8 !important;
    font-size: 13px;
}}

/* Sidebar inputs — light so numbers always readable */
section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    background-color: #dde8f5 !important;
    color: black !important;
    border-radius: 10px !important;
    border: 1.5px solid #8ba4c8 !important;
    transition: border-color 0.2s;
}}
section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {{
    border-color: #0891b2 !important;
    box-shadow: 0 0 0 3px rgba(8,145,178,0.18) !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="input"] input {{
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="select"] span {{
    color: #0f172a !important;
    font-weight: 700 !important;
}}

/* Hide number input spinners */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {{ -webkit-appearance: none; margin: 0; }}
input[type="number"] {{ -moz-appearance: textfield; }}

/* Slider handle */
div[data-baseweb="slider"] [role="slider"] {{
    background: #0891b2 !important;
    border: 2px solid white !important;
    box-shadow: 0 0 8px rgba(8,145,178,0.7) !important;
}}
div[data-testid="stTickBar"] {{ display: none !important; }}

/* Dropdown popup */
div[data-baseweb="popover"] {{
    background: #0f172a !important;
    border: 1px solid rgba(8,145,178,0.2);
    border-radius: 12px;
}}
ul[role="listbox"] {{ background: #0f172a !important; }}
li[role="option"] {{ background: transparent !important; color: #94a3b8 !important; font-weight: 600 !important; }}
li[role="option"]:hover {{ background: rgba(8,145,178,0.12) !important; color: #67e8f9 !important; }}
section[data-testid="stSidebar"] div[data-baseweb="select"] span {{ color: black !important; font-weight: 600 !important; }}

/* ── SIDEBAR BUTTONS ── */
section[data-testid="stSidebar"] button {{
    background: linear-gradient(135deg, #0891b2 0%, #1d4ed8 100%) !important;
    backdrop-filter: none;
    border-radius: 11px !important;
    border: none !important;
    color: white !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: 0.03em !important;
    box-shadow: 0 4px 16px rgba(8,145,178,0.3) !important;
    transition: all 0.25s ease !important;
}}
section[data-testid="stSidebar"] button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(8,145,178,0.45) !important;
}}

/* ── DOWNLOAD BUTTON ── */
div.stDownloadButton > button {{
    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    color: white !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    border: none !important;
    box-shadow: 0 4px 18px rgba(5,150,105,0.35) !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
    font-size: 15px !important;
}}
div.stDownloadButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(5,150,105,0.5) !important;
}}

/* ── METRIC CARDS ── */
div[data-testid="metric-container"] {{
    background: rgba(8,145,178,0.08) !important;
    border: 1px solid rgba(8,145,178,0.22) !important;
    border-radius: 14px !important;
    padding: 16px !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-family: 'Syne', sans-serif !important;
    font-size: 2rem !important;
    color: #67e8f9 !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #64748b !important;
}}

/* ── ALERT BOXES ── */
div[data-testid="stSuccess"] {{
    background: rgba(4,120,87,0.10) !important;
    border: 1px solid rgba(4,120,87,0.38) !important;
    border-radius: 12px !important;
}}
div[data-testid="stSuccess"] p {{ color: #6ee7b7 !important; font-weight: 600; }}
div[data-testid="stWarning"] {{
    background: rgba(180,83,9,0.10) !important;
    border: 1px solid rgba(180,83,9,0.38) !important;
    border-radius: 12px !important;
}}
div[data-testid="stWarning"] p {{ color: #fcd34d !important; font-weight: 600; }}
div[data-testid="stError"] {{
    background: rgba(185,28,28,0.10) !important;
    border: 1px solid rgba(185,28,28,0.38) !important;
    border-radius: 12px !important;
}}
div[data-testid="stError"] p {{ color: #fca5a5 !important; font-weight: 600; }}

/* ── HR divider ── */
hr {{ border-color: rgba(8,145,178,0.18) !important; }}

/* ── GLASS BOX ── */
.glass-box {{
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 36px;
    border: 1px solid rgba(255,255,255,0.10);
    box-shadow: 0 8px 32px rgba(0,0,0,0.35);
    margin-bottom: 32px;
}}

@media (max-width: 992px) {{
    section[data-testid="stSidebar"] {{ width: 100% !important; }}
}}
</style>
""", unsafe_allow_html=True)

    # ── SIDEBAR ──────────────────────────────────────────────
    st.sidebar.markdown("# Patient Profile")
    info = st.session_state.patient_info

    st.sidebar.markdown(f"**Name:** {info.get('name','')}")
    st.sidebar.markdown(f"**Phone:** {info.get('phone','')}")
    st.sidebar.markdown(f"**Email:** {info.get('email','')}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Medical Inputs")

    age = st.sidebar.number_input("Age", 21, 100, 30)
    gender = st.sidebar.selectbox("Gender", ["Male", "Female"])

    if gender == "Female":
        pregnancies = st.sidebar.number_input("Number of Pregnancies",
                                               min_value=0, max_value=20, value=0)
    else:
        pregnancies = 0

    glucose = st.sidebar.slider("Glucose", 0, 200, 120)
    bp      = st.sidebar.slider("Blood Pressure", 0, 130, 70)
    skin    = st.sidebar.slider("Skin Thickness", 0, 100, 20)
    insulin = st.sidebar.slider("Insulin", 0, 900, 80)
    bmi     = st.sidebar.number_input("BMI", 10.0, 70.0, 25.0)
    dpf     = st.sidebar.slider("DPF", 0.0, 2.5, 0.5)

    st.sidebar.markdown("---")
    predict_btn = st.sidebar.button("Predict", use_container_width=True)
    logout_btn  = st.sidebar.button("Logout")

    if logout_btn:
        st.session_state.registered   = False
        st.session_state.patient_info = {}
        st.session_state.show_success = False
        st.rerun()

    # ── MAIN TITLE & ABOUT ───────────────────────────────────
    st.title("🩺 Diabetes Prediction System")
    st.markdown("AI-Powered Diabetes Risk Assessment Tool")

    if st.session_state.show_success:
        st.success("✅ Registration Successful!")
        st.session_state.show_success = False

    st.markdown("""
### 📋 About This System
This Diabetes Prediction System is an AI-powered medical risk assessment tool designed to estimate the likelihood of diabetes based on key health parameters such as glucose level, BMI, blood pressure, age, and family history.
""")

    # ── PREDICTION LOGIC ─────────────────────────────────────
    if predict_btn:
        if "_id" in info:
            users_collection.update_one({"_id": info["_id"]}, {"$set": {"gender": gender}})

        input_data = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
        input_std  = scaler.transform(input_data)
        prediction = model.predict(input_std)[0]
        probability = model.predict_proba(input_std)[0]

        prob_negative = probability[0] * 100
        prob_positive = probability[1] * 100

        if prob_positive < 30:   risk_label = "Low Risk"
        elif prob_positive < 70: risk_label = "Moderate Risk"
        else:                    risk_label = "High Risk"

        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        prediction_data = {
            "patient_id":   info["_id"],
            "patient_name": info["name"],
            "age":          age,
            "gender":       gender,
            "glucose":      glucose,
            "blood_pressure": bp,
            "bmi":          bmi,
            "prediction":   risk_label,
            "probability":  round(prob_positive, 2),
            "created_at":   current_time.strftime("%d-%m-%Y %H:%M:%S")
        }
        predictions_collection.insert_one(prediction_data)

        # ── UI RESULTS ───────────────────────────────────────
        st.markdown("---")
        st.header("Prediction Results")
        col1, col2 = st.columns([2, 1])

        with col1:
            if prob_positive < 30:
                st.success("✅ LOW RISK - Diabetes Unlikely")
            elif prob_positive < 70:
                st.warning("⚠️ MODERATE RISK - Possible Diabetes")
            else:
                st.error("❌ HIGH RISK - Diabetes Likely")

            st.subheader("Probability Breakdown")
            c1, c2 = st.columns(2)
            c1.metric("Non-Diabetic", f"{prob_negative:.1f}%")
            c2.metric("Diabetic",     f"{prob_positive:.1f}%")

        with col2:
            # Determine gauge colour
            gauge_color = "#22c55e" if prob_positive < 30 else \
                          "#f59e0b" if prob_positive < 70 else "#ef4444"
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prob_positive,
                number={"suffix": "%", "font": {"color": "white", "size": 28,
                                                 "family": "DM Sans"}},
                title={"text": "Risk Level", "font": {"color": "#94a3b8", "size": 13}},
                gauge={
                    "axis": {"range": [0, 100],
                             "tickcolor": "rgba(255,255,255,0.2)", "tickwidth": 1},
                    "bar":  {"color": gauge_color, "thickness": 0.22},
                    "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
                    "steps": [
                        {"range": [0,  30], "color": "rgba(34,197,94,0.14)"},
                        {"range": [30, 70], "color": "rgba(245,158,11,0.14)"},
                        {"range": [70,100], "color": "rgba(239,68,68,0.14)"},
                    ],
                    "threshold": {"line": {"color": gauge_color, "width": 3},
                                  "thickness": 0.8, "value": prob_positive},
                }
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                height=250,
                margin=dict(l=16, r=16, t=24, b=8),
            )
            st.plotly_chart(fig, use_container_width=True)

        # ── RISK FACTOR ANALYSIS ─────────────────────────────
        st.markdown("---")
        st.subheader("Risk Factor Analysis")
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

        if risk_factors:
            st.warning("Identified Risk Factors:")
            for factor in risk_factors:
                st.markdown(f"- {factor}")

        if positive_factors:
            st.success("Positive Health Indicators:")
            for factor in positive_factors:
                st.markdown(f"- {factor}")

        # ── RECOMMENDATIONS ──────────────────────────────────
        st.markdown("---")
        st.subheader("Recommendations")
        if prob_positive >= 70:
            st.error("- Consult a healthcare professional immediately\n"
                     "- Get complete diabetes screening\n"
                     "- Monitor blood sugar regularly\n"
                     "- Improve diet and physical activity")
            recs_for_pdf = [
                "Consult a healthcare professional immediately",
                "Get complete diabetes screening",
                "Monitor blood sugar regularly",
                "Improve diet and physical activity",
            ]
        elif prob_positive >= 30:
            st.warning("- Maintain healthy diet\n"
                       "- Increase physical activity\n"
                       "- Monitor glucose periodically")
            recs_for_pdf = [
                "Maintain healthy diet",
                "Increase physical activity",
                "Monitor glucose periodically",
            ]
        else:
            st.success("- Continue healthy lifestyle\n"
                       "- Exercise regularly\n"
                       "- Routine health check-ups")
            recs_for_pdf = [
                "Continue healthy lifestyle",
                "Exercise regularly",
                "Routine health check-ups",
            ]

        # ── CHARTS (UI) ──────────────────────────────────────
        st.markdown('<div class="glass-box">', unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("📊 Causes of Diabetes (Risk Contribution Analysis)")

        c_col1, c_col2 = st.columns([1, 1])
        cause_labels, cause_values = [], []

        if glucose >= 126: cause_labels.append("High Glucose");        cause_values.append(min(glucose / 2, 100))
        if bmi > 30:       cause_labels.append("High BMI (Obesity)");  cause_values.append(min(bmi * 2, 100))
        if age > 45:       cause_labels.append("Age Factor");          cause_values.append(min(age, 100))
        if bp > 120:       cause_labels.append("High Blood Pressure");  cause_values.append(min(bp, 100))
        if dpf > 0.5:      cause_labels.append("Genetic Risk (DPF)");  cause_values.append(min(dpf * 100, 100))
        if not cause_labels:
            cause_labels = ["Healthy Indicators"]
            cause_values = [100]

        # Plotly bar (dark on-screen)
        scr_colors = ["#dc2626","#d97706","#2563eb","#7c3aed","#047857"]
        bar_col = [scr_colors[i % len(scr_colors)] for i in range(len(cause_labels))]
        bar_fig = go.Figure(go.Bar(
            x=cause_labels, y=cause_values,
            text=[f"{v:.1f}" for v in cause_values], textposition="auto",
            marker=dict(color=bar_col, line=dict(color="rgba(255,255,255,0.15)", width=1.5)),
            textfont=dict(color="white", size=14, family="DM Sans"),
        ))
        bar_fig.update_layout(
            title="Risk Factor Severity",
            xaxis_title="Causes", yaxis_title="Severity Level",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="DM Sans"),
            autosize=True, margin=dict(l=20, r=20, t=50, b=20),
        )
        bar_fig.update_xaxes(tickfont=dict(color="#94a3b8", size=13),
                             title_font=dict(color="#94a3b8", size=14),
                             showline=True, linecolor="rgba(255,255,255,0.12)")
        bar_fig.update_yaxes(tickfont=dict(color="#94a3b8", size=13),
                             title_font=dict(color="#94a3b8", size=14),
                             showgrid=True, gridcolor="rgba(255,255,255,0.07)",
                             zerolinecolor="rgba(255,255,255,0.12)")
        with c_col1:
            st.plotly_chart(bar_fig, use_container_width=True, config={"responsive": True})

        # Plotly pie (dark on-screen)
        pie_fig = go.Figure(data=[go.Pie(
            labels=cause_labels, values=cause_values, hole=0.45,
            marker=dict(colors=bar_col, line=dict(color="rgba(0,0,0,0.35)", width=2)),
            textfont=dict(color="white", size=12, family="DM Sans"),
        )])
        pie_fig.update_layout(
            title="Percentage Contribution",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="DM Sans"),
            autosize=True, margin=dict(l=20, r=20, t=50, b=20),
        )
        with c_col2:
            st.plotly_chart(pie_fig, use_container_width=True, config={"responsive": True})
        st.markdown("</div>", unsafe_allow_html=True)

        # ── PDF GENERATION ───────────────────────────────────
        pdf_bytes = build_hospital_pdf(
            info=info, age=age, gender=gender, glucose=glucose, bp=bp,
            skin=skin, insulin=insulin, bmi=bmi, dpf=dpf,
            pregnancies=pregnancies, prob_positive=prob_positive,
            risk_label=risk_label, current_time=current_time,
            cause_labels=cause_labels, cause_values=cause_values,
            recs_for_pdf=recs_for_pdf,
        )

        st.download_button(
            label="📄 Download Professional Medical Report (PDF)",
            data=pdf_bytes,
            file_name=f"Diabetes_Report_{info.get('name', 'Patient')}.pdf",
            mime="application/pdf",
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

