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
    """Canvas-based A4 hospital report — 1 page, uniform cell colour, auto-fit text."""
    import math
    W, H = A4
    M  = 13 * mm
    CW = W - 2 * M

    # ── Palette ──────────────────────────────────────────────
    NAVY     = rl_colors.HexColor("#0b1f3a")
    TEAL     = rl_colors.HexColor("#0e7490")
    TEAL_DIM = rl_colors.HexColor("#0c6782")
    CELL_BG  = rl_colors.HexColor("#f0f9ff")   # ONE uniform colour — every cell
    CELL_DIV = rl_colors.HexColor("#bae6fd")
    LBL_C    = rl_colors.HexColor("#64748b")
    VAL_C    = rl_colors.HexColor("#0f172a")
    WHITE    = rl_colors.white
    SLATE    = rl_colors.HexColor("#334155")
    GREY_BG  = rl_colors.HexColor("#f8fafc")
    ICE      = rl_colors.HexColor("#e0f2fe")
    GREEN    = rl_colors.HexColor("#047857")
    GREEN_BG = rl_colors.HexColor("#f0fdf4")
    AMBER    = rl_colors.HexColor("#b45309")
    AMBER_BG = rl_colors.HexColor("#fffbeb")
    RED      = rl_colors.HexColor("#b91c1c")
    RED_BG   = rl_colors.HexColor("#fff5f5")

    buf = BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)

    # ── HEADER ───────────────────────────────────────────────
    BH = 20 * mm
    c.setFillColor(NAVY); c.rect(0, H-BH, W, BH, fill=1, stroke=0)
    c.setFillColor(TEAL); c.rect(0, H-2*mm, W, 2*mm, fill=1, stroke=0)  # top stripe

    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 13.5)
    c.drawString(M, H-8*mm, "Diabetes Prediction System")
    c.setFillColor(rl_colors.HexColor("#7dd3fc")); c.setFont("Helvetica", 7)
    c.drawString(M, H-14*mm, "Clinical AI Risk Assessment  ·  Confidential")

    pid_display = info.get("_id", "N/A").replace("-", "")
    c.setFillColor(rl_colors.HexColor("#7dd3fc")); c.setFont("Helvetica", 7)
    c.drawRightString(W-M, H-8*mm,  f"ID  {pid_display}")
    c.drawRightString(W-M, H-14*mm, current_time.strftime("%d %B %Y"))

    y = H - BH - 5*mm

    # ── TITLE ────────────────────────────────────────────────
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(W/2, y, "DIABETES RISK ASSESSMENT REPORT")
    y -= 2*mm
    c.setStrokeColor(TEAL);    c.setLineWidth(2);   c.line(M, y, W-M, y)
    y -= 1*mm
    c.setStrokeColor(CELL_DIV); c.setLineWidth(0.5); c.line(M, y, W-M, y)
    y -= 4.5*mm

    # ── HELPERS ──────────────────────────────────────────────
    SH = 6*mm

    def section(cy, label):
        c.setFillColor(ICE); c.rect(M, cy-SH, CW, SH, fill=1, stroke=0)
        c.setFillColor(TEAL); c.rect(M, cy-SH, 2.5*mm, SH, fill=1, stroke=0)
        c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 7.8)
        c.drawString(M+4.5*mm, cy-3.9*mm, label.upper())
        return cy - SH

    def smart_fit(text, avail_w, max_fs=8.0, min_fs=5.5):
        """Shrink font to fit. If still too wide at min_fs, word-wrap to 2 lines."""
        v = str(text)
        fs = max_fs
        c.setFont("Helvetica-Bold", fs)
        while c.stringWidth(v, "Helvetica-Bold", fs) > avail_w and fs > min_fs:
            fs -= 0.2
        if c.stringWidth(v, "Helvetica-Bold", fs) <= avail_w:
            return [v], fs
        # Word-wrap: find split that balances both halves inside avail_w
        words = v.split()
        best_split, best_diff = 1, float("inf")
        for i in range(1, len(words)):
            l1 = " ".join(words[:i]); l2 = " ".join(words[i:])
            d  = (abs(c.stringWidth(l1,"Helvetica-Bold",min_fs) -
                      c.stringWidth(l2,"Helvetica-Bold",min_fs))
                  + max(0, c.stringWidth(l1,"Helvetica-Bold",min_fs)-avail_w)*3
                  + max(0, c.stringWidth(l2,"Helvetica-Bold",min_fs)-avail_w)*3)
            if d < best_diff:
                best_diff = d; best_split = i
        l1 = " ".join(words[:best_split]); l2 = " ".join(words[best_split:])
        c.setFont("Helvetica-Bold", min_fs)
        # Hard-truncate each line if needed
        while c.stringWidth(l1,"Helvetica-Bold",min_fs)>avail_w and len(l1)>3: l1=l1[:-2]+"…"
        while c.stringWidth(l2,"Helvetica-Bold",min_fs)>avail_w and len(l2)>3: l2=l2[:-2]+"…"
        return [l1, l2], min_fs

    CELL_H = 12.5*mm

    def draw_grid(cy, fields, ncols):
        cw    = CW / ncols
        nrows = math.ceil(len(fields) / ncols)
        pad   = 2.5*mm
        avail = cw - pad - 2*mm

        for idx, (lbl, raw) in enumerate(fields):
            row  = idx // ncols
            col  = idx %  ncols
            cx   = M + col * cw
            top  = cy - row * CELL_H
            bot  = top - CELL_H

            # Uniform background — identical for every cell
            c.setFillColor(CELL_BG)
            c.rect(cx, bot, cw, CELL_H, fill=1, stroke=0)

            # Internal dividers
            c.setStrokeColor(CELL_DIV); c.setLineWidth(0.4)
            if col < ncols - 1:
                c.line(cx+cw, bot, cx+cw, top)  # vertical
            c.line(cx, bot, cx+cw, bot)          # horizontal bottom

            # Field label — tiny, muted
            c.setFillColor(LBL_C); c.setFont("Helvetica-Bold", 5.8)
            c.drawString(cx+pad, top-3.8*mm, lbl.upper())

            # Field value — auto-fit
            lines, fs = smart_fit(raw, avail)
            c.setFillColor(VAL_C); c.setFont("Helvetica-Bold", fs)
            if len(lines) == 1:
                c.drawString(cx+pad, top-9.5*mm, lines[0])
            else:
                c.drawString(cx+pad, top-8.5*mm,  lines[0])
                c.drawString(cx+pad, top-12.5*mm, lines[1])

        total_h = nrows * CELL_H
        c.setStrokeColor(TEAL); c.setLineWidth(1.4); c.line(M, cy, M+CW, cy)
        c.setLineWidth(0.85)
        c.rect(M, cy-total_h, CW, total_h, fill=0, stroke=1)
        return cy - total_h

    def mini_sec(cx, cy, w, label):
        c.setFillColor(TEAL_DIM); c.rect(cx, cy-SH, w, SH, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 7.2)
        c.drawString(cx+3*mm, cy-3.8*mm, label.upper())
        return cy - SH

    # ── PATIENT PROFILE  3 × 2 ───────────────────────────────
    y = section(y, "Patient Profile")
    pid_clean = info.get("_id", "N/A").replace("-", "")
    patient_fields = [
        ("Patient ID",    pid_clean),
        ("Full Name",     info.get("name", "N/A")),
        ("Phone",         info.get("phone", "N/A")),
        ("Email Address", info.get("email", "N/A")),
        ("Country",       info.get("country", "N/A")),
        ("Address",       info.get("address", "N/A")),   # full — smart_fit wraps it
    ]
    y = draw_grid(y, patient_fields, ncols=3)
    y -= 3.5*mm

    # ── CLINICAL INPUTS  4 × 2 ───────────────────────────────
    y = section(y, "Clinical Inputs")
    clinical_fields = [
        ("Age",            f"{age} yrs"),
        ("Gender",         gender),
        ("Glucose Level",  f"{glucose} mg/dL"),
        ("Blood Pressure", f"{bp} mmHg"),
        ("Skin Thickness", f"{skin} mm"),
        ("Insulin Level",  f"{insulin} IU/mL"),
        ("BMI",            f"{bmi} kg/m\u00b2"),
        ("Diabetes PF",    str(dpf)),
    ]
    if gender == "Female":
        clinical_fields.insert(2, ("Pregnancies", str(pregnancies)))
    y = draw_grid(y, clinical_fields, ncols=4)
    y -= 3.5*mm

    # ── RISK RESULT BANNER ────────────────────────────────────
    if prob_positive < 30:
        BC, BG, BT = GREEN, GREEN_BG, "LOW RISK — Diabetes Unlikely"
    elif prob_positive < 70:
        BC, BG, BT = AMBER, AMBER_BG, "MODERATE RISK — Possible Diabetes"
    else:
        BC, BG, BT = RED, RED_BG, "HIGH RISK — Diabetes Likely"

    BNH = 11*mm
    c.setFillColor(BC);  c.rect(M,      y-BNH, 3*mm,    BNH, fill=1, stroke=0)
    c.setFillColor(BG);  c.rect(M+3*mm, y-BNH, CW-3*mm, BNH, fill=1, stroke=0)
    c.setStrokeColor(BC); c.setLineWidth(0.8)
    c.rect(M, y-BNH, CW, BNH, fill=0, stroke=1)
    c.setFillColor(BC); c.setFont("Helvetica-Bold", 10.5)
    c.drawString(M+5.5*mm, y-5.3*mm, BT)
    c.setFillColor(BC); c.setFont("Helvetica-Bold", 13)
    c.drawRightString(W-M-3*mm, y-7*mm, f"{prob_positive:.1f}%")
    c.setFillColor(SLATE); c.setFont("Helvetica", 6)
    c.drawRightString(W-M-3*mm, y-10.5*mm, "probability score")
    y -= BNH + 3*mm

    # ── DIAGNOSTIC VISUALISATION ──────────────────────────────
    y = section(y, "Diagnostic Data Visualisation")
    CH   = 48*mm
    CW_h = (CW - 2*mm) / 2

    c.setFillColor(GREY_BG); c.rect(M, y-CH, CW, CH, fill=1, stroke=0)
    c.drawImage(ImageReader(_make_bar_buf(cause_labels, cause_values)),
                M+0.5*mm,    y-CH+0.5*mm,
                width=CW_h-0.5*mm, height=CH-1*mm,
                preserveAspectRatio=True, anchor="nw")
    c.drawImage(ImageReader(_make_pie_buf(cause_labels, cause_values)),
                M+CW_h+2*mm, y-CH+0.5*mm,
                width=CW_h-2*mm,   height=CH-1*mm,
                preserveAspectRatio=True, anchor="nw")
    c.setStrokeColor(CELL_DIV); c.setLineWidth(0.5)
    c.line(M+CW_h+1*mm, y-CH+2*mm, M+CW_h+1*mm, y-2*mm)
    c.setStrokeColor(TEAL); c.setLineWidth(0.85)
    c.rect(M, y-CH, CW, CH, fill=0, stroke=1)
    y -= CH + 3*mm

    # ── RISK FACTORS  |  RECOMMENDATIONS  (side by side) ─────
    GAP    = 3*mm
    LEFT_W = CW * 0.53
    RGHT_W = CW - LEFT_W - GAP
    LX     = M
    RX     = M + LEFT_W + GAP

    y_l = mini_sec(LX, y, LEFT_W, "Risk Factor Analysis")
    y_r = mini_sec(RX, y, RGHT_W, "Recommendations")
    ROW  = 5.5*mm

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

    def rf_row(cx, cy, w, text, accent, bg, txt_clr):
        c.setFillColor(bg);     c.rect(cx, cy-ROW, w, ROW, fill=1, stroke=0)
        c.setFillColor(accent); c.rect(cx, cy-ROW, 2*mm, ROW, fill=1, stroke=0)
        avw = w - 5.5*mm; fs = 7.2
        c.setFont("Helvetica", fs)
        while c.stringWidth(text,"Helvetica",fs) > avw and fs > 5.5: fs -= 0.2
        t = text
        c.setFont("Helvetica", fs)
        while c.stringWidth(t,"Helvetica",fs) > avw and len(t) > 4: t = t[:-2]+"…"
        c.setFillColor(txt_clr); c.drawString(cx+4.5*mm, cy-ROW/2-1.5*mm, t)
        c.setStrokeColor(rl_colors.HexColor("#e2e8f0")); c.setLineWidth(0.25)
        c.line(cx, cy-ROW, cx+w, cy-ROW)

    for item in risk_factors:
        rf_row(LX, y_l, LEFT_W, item, RED, RED_BG, rl_colors.HexColor("#7f1d1d"))
        y_l -= ROW + 0.4*mm
    for item in positive_factors:
        rf_row(LX, y_l, LEFT_W, item, GREEN, GREEN_BG, rl_colors.HexColor("#14532d"))
        y_l -= ROW + 0.4*mm
    c.setStrokeColor(TEAL); c.setLineWidth(0.8)
    c.rect(LX, y_l, LEFT_W, y-SH-y_l, fill=0, stroke=1)

    for r in recs_for_pdf:
        c.setFillColor(rl_colors.HexColor("#f0f9ff"))
        c.rect(RX, y_r-ROW, RGHT_W, ROW, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.circle(RX+3*mm, y_r-ROW/2-0.3*mm, 1.3*mm, fill=1, stroke=0)
        avw = RGHT_W - 7*mm; fs = 7.2
        t = r; c.setFont("Helvetica", fs)
        while c.stringWidth(t,"Helvetica",fs) > avw and fs > 5.5: fs -= 0.2
        c.setFont("Helvetica", fs)
        while c.stringWidth(t,"Helvetica",fs) > avw and len(t) > 4: t = t[:-2]+"…"
        c.setFillColor(rl_colors.HexColor("#0c4a6e")); c.drawString(RX+6.5*mm, y_r-ROW/2-1.5*mm, t)
        c.setStrokeColor(CELL_DIV); c.setLineWidth(0.25)
        c.line(RX, y_r-ROW, RX+RGHT_W, y_r-ROW)
        y_r -= ROW + 0.4*mm
    c.setStrokeColor(TEAL); c.setLineWidth(0.8)
    c.rect(RX, y_r, RGHT_W, y-SH-y_r, fill=0, stroke=1)

    # ── FOOTER ───────────────────────────────────────────────
    FH = 11*mm
    c.setFillColor(GREY_BG); c.rect(0, 0, W, FH, fill=1, stroke=0)
    c.setStrokeColor(TEAL); c.setLineWidth(0.6); c.line(0, FH, W, FH)
    c.setFillColor(SLATE); c.setFont("Helvetica-Oblique", 6)
    c.drawString(M, 7.5*mm,
        "Disclaimer: This AI-generated report is for informational purposes only "
        "and does not constitute professional medical advice.")
    c.setFont("Helvetica", 6)
    c.drawString(M, 3.5*mm, "Consult a qualified healthcare professional for diagnosis and treatment.")
    c.drawRightString(W-M, 5.5*mm, "Diabetes Prediction System  ·  Page 1 of 1")

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
