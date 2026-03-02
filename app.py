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
import matplotlib.patches as mpatches
import seaborn as sns
import base64
import re
import pycountry
import phonenumbers
import time
import math

def get_base64_image(image_file):
    try:
        with open(image_file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

def country_to_flag(country_code):
    return "".join(chr(127397 + ord(char)) for char in country_code.upper())

# PDF imports
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# MongoDB
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

st.set_page_config(
    page_title="Diabetes Prediction System",
    page_icon="🩺",
    layout="wide"
)

if "registered" not in st.session_state:
    st.session_state.registered = False
if "patient_info" not in st.session_state:
    st.session_state.patient_info = {}
if "show_success" not in st.session_state:
    st.session_state.show_success = False


# ╔══════════════════════════════════════════════════════════════╗
# ║              PROFESSIONAL HOSPITAL PDF BUILDER               ║
# ╚══════════════════════════════════════════════════════════════╝

def _make_bar_chart_pdf(labels, values):
    """High-quality seaborn-styled bar chart for PDF"""
    sns.set_style("white")
    fig, ax = plt.subplots(figsize=(5.2, 3.4), dpi=200)
    fig.patch.set_facecolor("#FAFCFF")
    ax.set_facecolor("#F0F6FF")

    palette = ["#C0392B", "#E67E22", "#2980B9", "#8E44AD", "#27AE60",
               "#16A085", "#D35400", "#2C3E50"]
    cols = [palette[i % len(palette)] for i in range(len(labels))]

    bars = ax.bar(labels, values, color=cols, edgecolor="white",
                  linewidth=2.0, width=0.55, zorder=3,
                  capstyle='round')

    # Gradient effect simulation via bar hatching
    for bar, col, val in zip(bars, cols, values):
        # Add value label on top
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.03,
                f"{val:.0f}", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color="#1A202C",
                fontfamily="DejaVu Sans")

    ax.set_ylim(0, max(values) * 1.45 if values else 110)
    ax.set_title("Risk Factor Severity Analysis", fontsize=12,
                 fontweight="bold", color="#1A202C", pad=12,
                 fontfamily="DejaVu Sans")
    ax.set_xlabel("Risk Factors", fontsize=9, color="#4A5568", labelpad=6)
    ax.set_ylabel("Severity Score", fontsize=9, color="#4A5568", labelpad=6)

    ax.tick_params(axis="x", labelsize=8, colors="#4A5568",
                   rotation=20, pad=4)
    ax.tick_params(axis="y", labelsize=8, colors="#4A5568")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["left"].set_color("#CBD5E0")
    ax.spines["bottom"].set_color("#CBD5E0")
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.yaxis.grid(True, color="#E2E8F0", linewidth=0.7,
                  linestyle="--", zorder=0, alpha=0.8)
    ax.set_axisbelow(True)

    # Add light background bands
    for i, (lbl, val) in enumerate(zip(labels, values)):
        ax.axvspan(i - 0.4, i + 0.4, alpha=0.04, color=cols[i], zorder=1)

    plt.tight_layout(pad=1.2)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=200,
                facecolor="#FAFCFF")
    plt.close(fig)
    buf.seek(0)
    return buf


def _make_pie_chart_pdf(labels, values):
    """High-quality donut chart for PDF"""
    sns.set_style("white")
    fig, ax = plt.subplots(figsize=(5.0, 3.6), dpi=200)
    fig.patch.set_facecolor("#FAFCFF")

    palette = ["#C0392B", "#E67E22", "#2980B9", "#8E44AD", "#27AE60",
               "#16A085", "#D35400", "#2C3E50"]
    cols = [palette[i % len(palette)] for i in range(len(labels))]

    wedges, texts, autos = ax.pie(
        values, labels=None, colors=cols,
        autopct="%1.1f%%", startangle=90,
        wedgeprops=dict(width=0.60, edgecolor="white", linewidth=2.5,
                        antialiased=True),
        pctdistance=0.80,
        shadow=False
    )
    for at in autos:
        at.set_fontsize(8.5)
        at.set_fontweight("bold")
        at.set_color("white")

    # Center label
    total = sum(values)
    ax.text(0, 0, f"{total:.0f}\nTotal", ha="center", va="center",
            fontsize=9, fontweight="bold", color="#2D3748",
            fontfamily="DejaVu Sans")

    ax.legend(wedges, labels,
              loc="lower center",
              bbox_to_anchor=(0.5, -0.14),
              ncol=min(3, len(labels)),
              fontsize=7.5,
              frameon=False,
              labelcolor="#4A5568")
    ax.set_title("Risk Contribution Distribution", fontsize=12,
                 fontweight="bold", color="#1A202C", pad=10)

    plt.tight_layout(pad=1.0)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=200,
                facecolor="#FAFCFF")
    plt.close(fig)
    buf.seek(0)
    return buf


def _make_risk_gauge_pdf(prob_positive):
    """Horizontal risk meter / gauge for PDF"""
    fig, ax = plt.subplots(figsize=(5.5, 1.8), dpi=200)
    fig.patch.set_facecolor("#FAFCFF")
    ax.set_facecolor("#FAFCFF")

    # Background bar segments
    segments = [(0, 33, "#D4EDDA", "Low Risk"),
                (33, 66, "#FFF3CD", "Moderate"),
                (66, 100, "#F8D7DA", "High Risk")]
    for start, end, color, label in segments:
        ax.barh(0, end - start, left=start, height=0.6,
                color=color, edgecolor="white", linewidth=1.5)
        ax.text((start + end) / 2, 0, label,
                ha="center", va="center",
                fontsize=7.5, color="#4A5568", fontweight="bold")

    # Indicator
    if prob_positive < 33:
        ind_color = "#27AE60"
    elif prob_positive < 66:
        ind_color = "#E67E22"
    else:
        ind_color = "#C0392B"

    ax.axvline(x=prob_positive, color=ind_color, linewidth=3.5, zorder=5)
    ax.scatter([prob_positive], [0.4], color=ind_color, s=120,
               zorder=6, edgecolors="white", linewidths=1.5)
    ax.text(prob_positive, 0.55,
            f"{prob_positive:.1f}%",
            ha="center", va="bottom",
            fontsize=10, fontweight="bold",
            color=ind_color)

    ax.set_xlim(0, 100)
    ax.set_ylim(-0.5, 0.9)
    ax.axis("off")
    ax.set_title("Risk Level Meter", fontsize=10, fontweight="bold",
                 color="#2D3748", pad=6)

    plt.tight_layout(pad=0.5)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=200,
                facecolor="#FAFCFF")
    plt.close(fig)
    buf.seek(0)
    return buf


def _auto_fit_col_widths(fields, ncols, total_w, c):
    """Calculate auto-fit column widths based on actual content"""
    col_max = [0.0] * ncols
    for idx, (lbl, val) in enumerate(fields):
        col = idx % ncols
        lw = c.stringWidth(str(lbl).upper(), "Helvetica-Bold", 7) + 10 * mm
        vw = c.stringWidth(str(val), "Helvetica-Bold", 8.5) + 10 * mm
        col_max[col] = max(col_max[col], lw, vw)

    total = sum(col_max)
    if total < 1:
        return [total_w / ncols] * ncols
    return [w * total_w / total for w in col_max]


def build_hospital_pdf(info, age, gender, glucose, bp, skin, insulin, bmi, dpf,
                        pregnancies, prob_positive, risk_label, current_time,
                        cause_labels, cause_values, recs_for_pdf):
    W, H = A4
    M  = 15 * mm
    CW = W - 2 * M

    # ── COLOR PALETTE ────────────────────────────────────────
    NAVY      = rl_colors.HexColor("#0B2447")
    NAVY2     = rl_colors.HexColor("#19376D")
    TEAL      = rl_colors.HexColor("#0A6EBD")
    TEAL_LT   = rl_colors.HexColor("#A5D7E8")
    WHITE     = rl_colors.white
    BLACK     = rl_colors.HexColor("#0D1B2A")
    GRY_T     = rl_colors.HexColor("#4A5568")
    GRY_L     = rl_colors.HexColor("#F7FAFC")
    GRY_R     = rl_colors.HexColor("#CBD5E0")
    GRY_LN    = rl_colors.HexColor("#E2E8F0")
    ROW_A     = rl_colors.HexColor("#EBF4FD")
    ROW_B     = rl_colors.white
    GREEN_C   = rl_colors.HexColor("#276749")
    GREEN_B   = rl_colors.HexColor("#E6FFFA")
    GREEN_D   = rl_colors.HexColor("#C6F6D5")
    AMBR_C    = rl_colors.HexColor("#9C4221")
    AMBR_B    = rl_colors.HexColor("#FFFAF0")
    AMBR_D    = rl_colors.HexColor("#FEEBC8")
    RED_C     = rl_colors.HexColor("#9B1C1C")
    RED_B     = rl_colors.HexColor("#FFF5F5")
    RED_D     = rl_colors.HexColor("#FEB2B2")
    ACCENT    = rl_colors.HexColor("#576CBC")

    buf = BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)

    # ══════════════════════════════════════════════════════════
    # HEADER BAND
    # ══════════════════════════════════════════════════════════
    BH = 30 * mm

    # Deep navy gradient simulation (two rect layers)
    c.setFillColor(NAVY)
    c.rect(0, H - BH, W, BH, fill=1, stroke=0)
    c.setFillColor(NAVY2)
    c.rect(0, H - BH, W * 0.55, BH, fill=1, stroke=0)

    # Left accent stripe
    c.setFillColor(TEAL)
    c.rect(0, H - BH, 4 * mm, BH, fill=1, stroke=0)

    # Hospital cross icon (simplified geometric)
    cx_icon, cy_icon, sz = 14 * mm, H - BH / 2, 5.5 * mm
    c.setFillColor(WHITE)
    c.rect(cx_icon - sz * 0.15, cy_icon - sz * 0.5,
           sz * 0.3, sz, fill=1, stroke=0)  # vertical
    c.rect(cx_icon - sz * 0.5, cy_icon - sz * 0.15,
           sz, sz * 0.3, fill=1, stroke=0)  # horizontal

    # Title
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(24 * mm, H - 11 * mm, "MedCore AI  ·  Diabetes Prediction System")
    c.setFillColor(TEAL_LT)
    c.setFont("Helvetica", 8)
    c.drawString(24 * mm, H - 17 * mm,
                 "AI-Powered Clinical Risk Assessment  ·  Support Vector Machine (SVM) Architecture")
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(24 * mm, H - 23 * mm,
                 "For Clinical Use Only  ·  Confidential Patient Document")

    # Right info block
    pid_display = info.get("_id", "N/A")
    right_x = W - M
    c.setFillColor(rl_colors.HexColor("#A5D7E8"))
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(right_x, H - 10 * mm, f"Patient ID:  {pid_display}")
    c.setFillColor(rl_colors.HexColor("#90CDF4"))
    c.setFont("Helvetica", 7.5)
    c.drawRightString(right_x, H - 16 * mm,
                      f"Date: {current_time.strftime('%d %B %Y')}")
    c.drawRightString(right_x, H - 21.5 * mm,
                      f"Time: {current_time.strftime('%I:%M %p IST')}")
    c.setFillColor(rl_colors.HexColor("#FC8181"))
    c.setFont("Helvetica-Bold", 7.5)
    c.drawRightString(right_x, H - 27 * mm, "● CONFIDENTIAL")

    # Bottom accent line of header
    c.setStrokeColor(TEAL)
    c.setLineWidth(2.5)
    c.line(0, H - BH, W, H - BH)

    y = H - BH - 7 * mm

    # ══════════════════════════════════════════════════════════
    # REPORT TITLE ROW
    # ══════════════════════════════════════════════════════════
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(W / 2, y, "DIABETES RISK PREDICTION REPORT")
    y -= 3 * mm
    # Decorative double line
    c.setStrokeColor(TEAL)
    c.setLineWidth(2.5)
    c.line(M, y, W - M, y)
    c.setStrokeColor(TEAL_LT)
    c.setLineWidth(0.8)
    c.line(M, y - 1.5 * mm, W - M, y - 1.5 * mm)
    y -= 7 * mm

    # ── SECTION HEADER HELPER ────────────────────────────────
    def sec_head(cx, cy, label, w, icon=""):
        # Gradient band simulation
        c.setFillColor(NAVY2)
        c.rect(cx, cy - 7.5 * mm, w, 7.5 * mm, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.rect(cx, cy - 7.5 * mm, 3.5 * mm, 7.5 * mm, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(cx + 6 * mm, cy - 5 * mm, f"{icon}  {label.upper()}" if icon else label.upper())
        # Right-aligned light label
        c.setFillColor(TEAL_LT)
        c.setFont("Helvetica", 7)
        c.drawRightString(cx + w - 3 * mm, cy - 5 * mm, "MedCore AI")
        return cy - 7.5 * mm

    CELL_H = 13.5 * mm

    # ── GRID CELL HELPER ─────────────────────────────────────
    def grid_cell(cx, cy, label, value, cw, shade, last_col=False):
        bg = ROW_A if shade else ROW_B
        c.setFillColor(bg)
        c.rect(cx, cy - CELL_H, cw, CELL_H, fill=1, stroke=0)

        # Left mini accent
        c.setFillColor(TEAL if shade else TEAL_LT)
        c.rect(cx, cy - CELL_H, 1.5 * mm, CELL_H, fill=1, stroke=0)

        c.setStrokeColor(GRY_LN)
        c.setLineWidth(0.35)
        c.line(cx, cy - CELL_H, cx + cw, cy - CELL_H)
        if not last_col:
            c.line(cx + cw, cy - CELL_H, cx + cw, cy)

        c.setFillColor(GRY_T)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(cx + 3.5 * mm, cy - 5 * mm, str(label).upper())

        c.setFillColor(BLACK)
        c.setFont("Helvetica-Bold", 8.5)
        v = str(value)
        max_text_w = cw - 5.5 * mm
        while c.stringWidth(v, "Helvetica-Bold", 8.5) > max_text_w and len(v) > 3:
            v = v[:-3] + "…"
        c.drawString(cx + 3.5 * mm, cy - 11 * mm, v)

    def outer_border(cx, cy, w, h):
        c.setStrokeColor(TEAL)
        c.setLineWidth(1.0)
        c.rect(cx, cy - h, w, h, fill=0, stroke=1)

    # ══════════════════════════════════════════════════════════
    # PATIENT PROFILE SECTION
    # ══════════════════════════════════════════════════════════
    pid_no_hyphen = info.get("_id", "N/A")
    p_fields_raw = [
        ("Patient ID",    pid_no_hyphen),
        ("Full Name",     info.get("name", "N/A")),
        ("Phone Number",  info.get("phone", "N/A")),
        ("Email Address", info.get("email", "N/A")),
        ("Country",       info.get("country", "N/A")),
        ("Address",       info.get("address", "N/A")),
    ]

    NCOLS_P   = 3
    col_ws_p  = _auto_fit_col_widths(p_fields_raw, NCOLS_P, CW, c)
    NROWS_P   = math.ceil(len(p_fields_raw) / NCOLS_P)
    P_H       = NROWS_P * CELL_H

    y = sec_head(M, y, "Patient Profile", CW, "👤")
    for idx, (lbl, val) in enumerate(p_fields_raw):
        row = idx // NCOLS_P
        col = idx %  NCOLS_P
        cx  = M + sum(col_ws_p[:col])
        cy  = y - row * CELL_H
        shade    = (row % 2 == 0)
        last_col = (col == NCOLS_P - 1) or (idx == len(p_fields_raw) - 1)
        grid_cell(cx, cy, lbl, val, col_ws_p[col], shade, last_col=last_col)
    outer_border(M, y, CW, P_H)
    y -= P_H + 6 * mm

    # ══════════════════════════════════════════════════════════
    # CLINICAL INPUTS SECTION
    # ══════════════════════════════════════════════════════════
    cl_fields = [
        ("Age",             f"{age} yrs"),
        ("Gender",          gender),
        ("Glucose Level",   f"{glucose} mg/dL"),
        ("Blood Pressure",  f"{bp} mmHg"),
        ("Skin Thickness",  f"{skin} mm"),
        ("Insulin Level",   f"{insulin} IU/mL"),
        ("BMI",             f"{bmi} kg/m²"),
        ("DPF Score",       str(dpf)),
    ]
    if gender == "Female":
        cl_fields.insert(2, ("Pregnancies", str(pregnancies)))

    NCOLS_C   = 4
    col_ws_c  = _auto_fit_col_widths(cl_fields, NCOLS_C, CW, c)
    NROWS_C   = math.ceil(len(cl_fields) / NCOLS_C)
    C_H       = NROWS_C * CELL_H

    y = sec_head(M, y, "Clinical Input Parameters", CW, "🔬")
    for idx, (lbl, val) in enumerate(cl_fields):
        row = idx // NCOLS_C
        col = idx %  NCOLS_C
        cx  = M + sum(col_ws_c[:col])
        cy  = y - row * CELL_H
        shade    = (row % 2 == 0)
        last_col = (col == NCOLS_C - 1) or (idx == len(cl_fields) - 1)
        grid_cell(cx, cy, lbl, val, col_ws_c[col], shade, last_col=last_col)
    outer_border(M, y, CW, C_H)
    y -= C_H + 6 * mm

    # ══════════════════════════════════════════════════════════
    # RISK RESULT BANNER (prominent)
    # ══════════════════════════════════════════════════════════
    if prob_positive < 30:
        BC, BG, BD, BT = GREEN_C, GREEN_B, GREEN_D, "✔  LOW RISK  —  Diabetes Unlikely"
        risk_icon = "LOW"
    elif prob_positive < 70:
        BC, BG, BD, BT = AMBR_C, AMBR_B, AMBR_D, "⚠  MODERATE RISK  —  Possible Diabetes"
        risk_icon = "MOD"
    else:
        BC, BG, BD, BT = RED_C, RED_B, RED_D, "✖  HIGH RISK  —  Diabetes Likely"
        risk_icon = "HIGH"

    BANH = 18 * mm

    # Shadow layer
    c.setFillColor(rl_colors.HexColor("#CBD5E0"))
    c.rect(M + 1.2 * mm, y - BANH - 1.2 * mm, CW, BANH,
           fill=1, stroke=0)

    c.setFillColor(BC)
    c.rect(M, y - BANH, 5 * mm, BANH, fill=1, stroke=0)
    c.setFillColor(BG)
    c.rect(M + 5 * mm, y - BANH, CW - 5 * mm, BANH, fill=1, stroke=0)

    # Risk percentage block on right
    pct_w = 28 * mm
    c.setFillColor(BD)
    c.rect(M + CW - pct_w, y - BANH, pct_w, BANH, fill=1, stroke=0)
    c.setFillColor(BC)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(M + CW - pct_w / 2, y - 10 * mm,
                        f"{prob_positive:.1f}%")
    c.setFont("Helvetica", 7)
    c.drawCentredString(M + CW - pct_w / 2, y - 15 * mm, "Risk Score")

    c.setStrokeColor(BC)
    c.setLineWidth(1.2)
    c.rect(M, y - BANH, CW, BANH, fill=0, stroke=1)

    c.setFillColor(BC)
    c.setFont("Helvetica-Bold", 12.5)
    c.drawString(M + 8 * mm, y - 8.5 * mm, BT)
    c.setFillColor(GRY_T)
    c.setFont("Helvetica", 7.5)
    c.drawString(M + 8 * mm, y - 14.5 * mm,
                 f"SVM Prediction Engine  ·  {current_time.strftime('%d %B %Y  |  %I:%M %p IST')}")
    y -= BANH + 7 * mm

    # ══════════════════════════════════════════════════════════
    # VISUALIZATION SECTION (charts)
    # ══════════════════════════════════════════════════════════
    y = sec_head(M, y, "Data Visualization & Risk Analysis Charts", CW, "📊")
    y -= 2 * mm

    CHART_H = 60 * mm
    CW_HALF = (CW - 3 * mm) / 2

    # Chart backgrounds
    c.setFillColor(rl_colors.HexColor("#FAFCFF"))
    c.roundRect(M, y - CHART_H, CW_HALF, CHART_H, 3 * mm, fill=1, stroke=0)
    c.roundRect(M + CW_HALF + 3 * mm, y - CHART_H, CW_HALF, CHART_H,
                3 * mm, fill=1, stroke=0)

    bar_reader = ImageReader(_make_bar_chart_pdf(cause_labels, cause_values))
    pie_reader = ImageReader(_make_pie_chart_pdf(cause_labels, cause_values))

    c.drawImage(bar_reader, M, y - CHART_H, width=CW_HALF,
                height=CHART_H, preserveAspectRatio=True, anchor="c")
    c.drawImage(pie_reader, M + CW_HALF + 3 * mm, y - CHART_H,
                width=CW_HALF, height=CHART_H,
                preserveAspectRatio=True, anchor="c")

    c.setStrokeColor(GRY_R)
    c.setLineWidth(0.6)
    c.roundRect(M, y - CHART_H, CW_HALF, CHART_H, 3 * mm, fill=0, stroke=1)
    c.roundRect(M + CW_HALF + 3 * mm, y - CHART_H, CW_HALF, CHART_H,
                3 * mm, fill=0, stroke=1)
    y -= CHART_H + 4 * mm

    # Risk Gauge bar
    GAUGE_H = 22 * mm
    c.setFillColor(rl_colors.HexColor("#FAFCFF"))
    c.roundRect(M, y - GAUGE_H, CW, GAUGE_H, 3 * mm, fill=1, stroke=0)
    gauge_reader = ImageReader(_make_risk_gauge_pdf(prob_positive))
    c.drawImage(gauge_reader, M, y - GAUGE_H, width=CW, height=GAUGE_H,
                preserveAspectRatio=True, anchor="c")
    c.setStrokeColor(GRY_R)
    c.setLineWidth(0.5)
    c.roundRect(M, y - GAUGE_H, CW, GAUGE_H, 3 * mm, fill=0, stroke=1)
    y -= GAUGE_H + 6 * mm

    # ══════════════════════════════════════════════════════════
    # RISK FACTOR ANALYSIS (two column layout)
    # ══════════════════════════════════════════════════════════
    y = sec_head(M, y, "Risk Factor Analysis", CW, "⚕")
    y -= 2 * mm

    risk_factors, positive_factors = [], []
    if glucose >= 126:          risk_factors.append(("High Glucose Level", f"≥126 mg/dL — Current: {glucose}"))
    elif 100 <= glucose < 126:  risk_factors.append(("Prediabetic Glucose", f"100–125 mg/dL — Current: {glucose}"))
    else:                        positive_factors.append(("Normal Glucose Level", f"<100 mg/dL — Current: {glucose}"))
    if bmi > 30:                 risk_factors.append(("High BMI (Obesity)", f"BMI >30 — Current: {bmi}"))
    elif 18.5 <= bmi <= 24.9:   positive_factors.append(("Healthy BMI", f"18.5–24.9 — Current: {bmi}"))
    if age > 45:                 risk_factors.append(("Age Risk Factor", f"Age >45 — Current: {age} yrs"))
    if bp > 120:                 risk_factors.append(("High Blood Pressure", f">120 mmHg — Current: {bp}"))
    elif 90 <= bp <= 120:        positive_factors.append(("Normal Blood Pressure", f"90–120 mmHg — Current: {bp}"))
    if dpf > 0.5:                risk_factors.append(("Elevated Genetic Risk", f"DPF >0.5 — Current: {dpf}"))

    RFH = 7.5 * mm
    half_w = (CW - 3 * mm) / 2
    left_x  = M
    right_x_col = M + half_w + 3 * mm
    y_left  = y
    y_right = y

    def draw_rf_item(cx, cy, title, detail, is_risk):
        bg   = rl_colors.HexColor("#FFF5F5") if is_risk else rl_colors.HexColor("#F0FFF4")
        ac   = RED_C if is_risk else GREEN_C
        icon = "▲" if is_risk else "✓"
        c.setFillColor(bg)
        c.roundRect(cx, cy - RFH, half_w, RFH, 1.5 * mm, fill=1, stroke=0)
        c.setFillColor(ac)
        c.rect(cx, cy - RFH, 2.8 * mm, RFH, fill=1, stroke=0)
        c.setFillColor(ac)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(cx + 4 * mm, cy - 3.8 * mm, f"{icon} {title}")
        c.setFillColor(GRY_T)
        c.setFont("Helvetica", 6.5)
        c.drawString(cx + 4 * mm, cy - 6.8 * mm, detail)
        c.setStrokeColor(GRY_LN)
        c.setLineWidth(0.3)
        c.line(cx, cy - RFH, cx + half_w, cy - RFH)
        return cy - RFH - 1 * mm

    all_items = [(r[0], r[1], True)  for r in risk_factors] + \
                [(p[0], p[1], False) for p in positive_factors]

    mid = math.ceil(len(all_items) / 2)
    left_items  = all_items[:mid]
    right_items = all_items[mid:]

    for title, detail, is_risk in left_items:
        y_left = draw_rf_item(left_x, y_left, title, detail, is_risk)
    for title, detail, is_risk in right_items:
        y_right = draw_rf_item(right_x_col, y_right, title, detail, is_risk)

    y = min(y_left, y_right) - 4 * mm

    # ══════════════════════════════════════════════════════════
    # MEDICAL RECOMMENDATIONS
    # ══════════════════════════════════════════════════════════
    y = sec_head(M, y, "Medical Recommendations", CW, "💊")
    y -= 2 * mm

    rec_icons = ["①", "②", "③", "④", "⑤"]
    for i, r in enumerate(recs_for_pdf):
        icon_str = rec_icons[i] if i < len(rec_icons) else "•"
        bg = rl_colors.HexColor("#EBF8FF") if i % 2 == 0 else rl_colors.HexColor("#F0FFF4")
        REC_H = 8 * mm
        c.setFillColor(bg)
        c.roundRect(M, y - REC_H, CW, REC_H, 1.5 * mm, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.rect(M, y - REC_H, 3 * mm, REC_H, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(M + 5 * mm, y - 5.5 * mm, icon_str)
        c.setFillColor(BLACK)
        c.setFont("Helvetica", 8.5)
        c.drawString(M + 12 * mm, y - 5.5 * mm, r)
        c.setStrokeColor(GRY_LN)
        c.setLineWidth(0.3)
        c.line(M, y - REC_H, M + CW, y - REC_H)
        y -= REC_H + 1 * mm

    # ══════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════
    FH = 16 * mm
    c.setFillColor(rl_colors.HexColor("#1A365D"))
    c.rect(0, 0, W, FH, fill=1, stroke=0)
    c.setStrokeColor(TEAL)
    c.setLineWidth(1.5)
    c.line(0, FH, W, FH)

    # Left disclaimer
    c.setFillColor(rl_colors.HexColor("#A0AEC0"))
    c.setFont("Helvetica-Oblique", 6.8)
    c.drawString(M, 11 * mm,
                 "⚕  MEDICAL DISCLAIMER: This report is AI-generated and for informational purposes only.")
    c.drawString(M, 7 * mm,
                 "    Consult a qualified healthcare professional for clinical diagnosis and treatment.")
    c.setFillColor(rl_colors.HexColor("#718096"))
    c.setFont("Helvetica", 6.5)
    c.drawString(M, 3 * mm,
                 f"Report ID: {pid_display}  ·  Generated: {current_time.strftime('%d %B %Y %I:%M %p IST')}")

    # Right page number
    c.setFillColor(TEAL_LT)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawRightString(W - M, 8 * mm, "Diabetes Prediction System")
    c.setFillColor(rl_colors.HexColor("#718096"))
    c.setFont("Helvetica", 7)
    c.drawRightString(W - M, 4 * mm, "Page 1 of 1")

    c.save()
    return buf.getvalue()


# ╔══════════════════════════════════════════════════════════════╗
# ║                  BACKGROUND GENERATORS                       ║
# ╚══════════════════════════════════════════════════════════════╝

def get_reg_bg(img_b64):
    """Returns CSS background for registration page"""
    if img_b64:
        return f"""
        background:
          linear-gradient(135deg, rgba(4,12,36,0.85) 0%, rgba(6,30,60,0.80) 50%, rgba(4,12,36,0.88) 100%),
          url("data:image/jpg;base64,{img_b64}") center/cover fixed;
        """
    # Creative SVG fallback — animated medical grid + DNA
    return """
        background: radial-gradient(ellipse at 20% 50%, #0B2447 0%, #07101F 60%),
                    radial-gradient(ellipse at 80% 20%, #19376D 0%, transparent 50%);
    """

def get_pred_bg(img_b64):
    """Returns CSS background for prediction page"""
    if img_b64:
        return f"""
        background:
          linear-gradient(160deg, rgba(3,10,30,0.83) 0%, rgba(5,25,55,0.80) 60%, rgba(3,10,30,0.87) 100%),
          url("data:image/png;base64,{img_b64}") center/cover fixed;
        """
    return """
        background: radial-gradient(ellipse at 70% 30%, #0A2647 0%, #040D1E 70%),
                    radial-gradient(ellipse at 20% 80%, #11265A 0%, transparent 55%);
    """


# ╔══════════════════════════════════════════════════════════════╗
# ║                    REGISTRATION PAGE                         ║
# ╚══════════════════════════════════════════════════════════════╝
def registration_page():
    img = get_base64_image("health.png")
    bg  = get_reg_bg(img)

    st.markdown(f"""
<style>
/* ── FONTS ── */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}

/* ── ROOT BACKGROUND ── */
.stApp {{
    {bg}
    font-family: 'Outfit', sans-serif;
    min-height: 100vh;
}}
.stApp::before {{
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background:
      radial-gradient(ellipse 60% 50% at 15% 40%, rgba(14,165,233,0.07) 0%, transparent 70%),
      radial-gradient(ellipse 50% 60% at 85% 60%, rgba(99,102,241,0.07) 0%, transparent 70%),
      url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%230ea5e9' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    pointer-events: none;
}}

#MainMenu, footer, header, .stDeployButton {{ display:none !important; }}

/* ── ANIMATIONS ── */
@keyframes fadeUp {{
    from {{ opacity:0; transform:translateY(28px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}
@keyframes pulse-glow {{
    0%, 100% {{ box-shadow: 0 0 20px rgba(14,165,233,0.2), 0 32px 80px rgba(0,0,0,0.55); }}
    50%        {{ box-shadow: 0 0 40px rgba(14,165,233,0.35), 0 32px 80px rgba(0,0,0,0.55); }}
}}
@keyframes shimmer {{
    0%   {{ background-position: -200% center; }}
    100% {{ background-position:  200% center; }}
}}
@keyframes float {{
    0%,100% {{ transform: translateY(0px); }}
    50%      {{ transform: translateY(-8px); }}
}}

/* ── PAGE ENTRY ── */
section.main > div {{ animation: fadeUp 0.7s cubic-bezier(.2,.8,.2,1) both; }}

/* ── TITLE ── */
h1 {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: clamp(2rem, 5vw, 3.2rem) !important;
    text-align: center;
    letter-spacing: -0.04em;
    background: linear-gradient(120deg,
        #ffffff 0%, #7dd3fc 35%, #818cf8 65%, #ffffff 100%);
    background-size: 300% auto;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    animation: shimmer 4s linear infinite;
    margin-bottom: 4px !important;
}}

/* ── SUBTITLE ── */
.stMarkdown p {{
    color: #94a3b8 !important;
    text-align: center;
    font-size: clamp(13px, 1.5vw, 16px);
    font-weight: 400;
    letter-spacing: 0.06em;
}}

/* ── FORM CARD ── */
div[data-testid="stForm"] {{
    background: linear-gradient(145deg,
        rgba(8,18,42,0.88) 0%,
        rgba(11,24,54,0.85) 100%) !important;
    backdrop-filter: blur(32px) saturate(1.5) brightness(1.05) !important;
    -webkit-backdrop-filter: blur(32px) !important;
    border-radius: 28px !important;
    padding: clamp(28px,5vw,52px) clamp(22px,5vw,48px) !important;
    width: 100%;
    max-width: 680px;
    margin: 3vh auto !important;
    border: 1px solid rgba(125,211,252,0.20) !important;
    box-shadow: 0 40px 90px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.04);
    animation: pulse-glow 4s ease-in-out infinite;
    position: relative; overflow: hidden;
}}
div[data-testid="stForm"]::before {{
    content: '';
    position: absolute; top:0; left:20%; right:20%; height:2px;
    background: linear-gradient(90deg, transparent, #7dd3fc, #818cf8, transparent);
    border-radius: 99px;
}}
div[data-testid="stForm"]::after {{
    content: '';
    position: absolute; bottom:0; left:30%; right:30%; height:1px;
    background: linear-gradient(90deg, transparent, rgba(129,140,248,0.4), transparent);
}}

/* ── FORM LABELS ── */
div[data-testid="stForm"] label {{
    color: #7dd3fc !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
}}

/* ── FORM INPUTS ── */
div[data-testid="stForm"] div[data-baseweb="input"] > div,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div,
div[data-testid="stForm"] div[data-baseweb="select"] > div {{
    background: rgba(255,255,255,0.055) !important;
    backdrop-filter: blur(8px) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(125,211,252,0.16) !important;
    transition: all 0.3s cubic-bezier(.2,.8,.2,1) !important;
}}
div[data-testid="stForm"] div[data-baseweb="input"] > div:hover,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div:hover {{
    border-color: rgba(125,211,252,0.35) !important;
    background: rgba(255,255,255,0.075) !important;
}}
div[data-testid="stForm"] div[data-baseweb="input"] > div:focus-within,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div:focus-within,
div[data-testid="stForm"] div[data-baseweb="select"] > div:focus-within {{
    border: 1px solid rgba(125,211,252,0.85) !important;
    box-shadow: 0 0 0 3px rgba(125,211,252,0.15), 0 0 20px rgba(125,211,252,0.25) !important;
    background: rgba(255,255,255,0.09) !important;
}}
div[data-testid="stForm"] input,
div[data-testid="stForm"] textarea {{
    color: #e2e8f0 !important;
    -webkit-text-fill-color: #e2e8f0 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    caret-color: #7dd3fc !important;
}}
div[data-testid="stForm"] input::placeholder,
div[data-testid="stForm"] textarea::placeholder {{ color: #334155 !important; }}
div[data-testid="stForm"] div[data-baseweb="select"] span {{ color: #e2e8f0 !important; }}

/* ── REGISTER BUTTON ── */
div[data-testid="stForm"] button[kind="primaryFormSubmit"],
div[data-testid="stForm"] button {{
    background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%) !important;
    color: white !important;
    border-radius: 14px !important;
    height: 54px !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    border: none !important;
    box-shadow: 0 6px 30px rgba(2,132,199,0.4) !important;
    transition: all 0.25s cubic-bezier(.2,.8,.2,1) !important;
    width: 100% !important;
    position: relative; overflow: hidden;
}}
div[data-testid="stForm"] button::after {{
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.1) 60%, transparent 80%);
    transform: translateX(-100%);
    transition: transform 0.4s ease;
}}
div[data-testid="stForm"] button:hover {{
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 40px rgba(2,132,199,0.55) !important;
}}
div[data-testid="stForm"] button:hover::after {{ transform: translateX(100%); }}
div[data-testid="stForm"] button:active {{ transform: scale(0.97) translateY(0) !important; }}

/* ── DROPDOWN ── */
div[data-baseweb="popover"],
ul[role="listbox"] {{ background: #0c1a35 !important; border-radius: 14px !important; border:1px solid rgba(125,211,252,0.18) !important; }}
li[role="option"] {{ color: #94a3b8 !important; font-weight:500; }}
li[role="option"]:hover {{ background:rgba(125,211,252,0.12) !important; color:#7dd3fc !important; }}

/* ── ALERTS ── */
div[data-testid="stSuccess"] {{ background:rgba(6,95,70,0.14)!important; border:1px solid rgba(16,185,129,0.4)!important; border-radius:14px!important; }}
div[data-testid="stSuccess"] p {{ color:#6ee7b7!important; font-weight:600; }}
div[data-testid="stError"]   {{ background:rgba(153,27,27,0.14)!important; border:1px solid rgba(239,68,68,0.4)!important; border-radius:14px!important; }}
div[data-testid="stError"] p {{ color:#fca5a5!important; font-weight:600; }}

/* ── RESPONSIVE ── */
@media (max-width:640px) {{
    div[data-testid="stForm"] {{ padding:22px 16px!important; border-radius:20px!important; }}
    h1 {{ font-size:1.7rem!important; }}
}}
@media (min-width:1440px) {{
    div[data-testid="stForm"] {{ max-width:760px; }}
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

            country_obj  = pycountry.countries.get(name=selected_country)
            country_code = phonenumbers.country_code_for_region(country_obj.alpha_2)

            phone   = st.text_input("Enter Phone Number (without country code)")
            email   = st.text_input("Email Address")
            address = st.text_area("Address")
            submit  = st.form_submit_button("Register")

            if submit:
                name    = name.strip()
                phone   = phone.strip()
                email   = email.strip()
                address = address.strip()

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
                    formatted_phone = phonenumbers.format_number(
                        parsed_number, phonenumbers.PhoneNumberFormat.E164)
                except:
                    st.error("❌ Invalid phone number format"); return

                ist          = pytz.timezone("Asia/Kolkata")
                current_time = datetime.now(ist)
                patient_id   = "PAT" + str(uuid.uuid4().int)[:6]

                user_data = {
                    "_id":        patient_id,
                    "name":       name,
                    "phone":      formatted_phone,
                    "country":    selected_country,
                    "email":      email,
                    "address":    address,
                    "gender":     "Not Selected",
                    "created_at": current_time.strftime("%d-%m-%Y %I:%M:%S %p")
                }
                users_collection.insert_one(user_data)
                st.session_state.patient_info  = user_data
                st.session_state.registered    = True
                st.session_state.show_success  = True
                st.rerun()


# ╔══════════════════════════════════════════════════════════════╗
# ║                    PREDICTION PAGE                           ║
# ╚══════════════════════════════════════════════════════════════╝
@st.cache_resource
def load_model():
    try:
        model  = joblib.load("diabetes_model.pkl")
        scaler = joblib.load("scaler_svm.pkl")
        return model, scaler
    except Exception as e:
        st.error(f"⚠️ Model Loading Error: {e}"); st.stop()


def prediction_page():
    model, scaler = load_model()
    if not st.session_state.patient_info:
        st.session_state.registered = False; st.stop()

    img = get_base64_image("health22.png")
    bg  = get_pred_bg(img)

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

*, *::before, *::after {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}

.stApp {{
    {bg}
    font-family:'Outfit',sans-serif;
    min-height:100vh;
}}
.stApp::before {{
    content:'';
    position:fixed; inset:0; z-index:0; pointer-events:none;
    background:
      radial-gradient(ellipse 70% 50% at 10% 30%, rgba(14,165,233,0.06) 0%, transparent 65%),
      radial-gradient(ellipse 60% 70% at 90% 70%, rgba(99,102,241,0.06) 0%, transparent 65%),
      url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%230ea5e9' fill-opacity='0.025'%3E%3Ccircle cx='40' cy='40' r='1.5'/%3E%3Ccircle cx='0' cy='0' r='1.5'/%3E%3Ccircle cx='80' cy='0' r='1.5'/%3E%3Ccircle cx='0' cy='80' r='1.5'/%3E%3Ccircle cx='80' cy='80' r='1.5'/%3E%3C/g%3E%3C/svg%3E");
}}

#MainMenu, footer, header, .stDeployButton {{ display:none !important; }}
::-webkit-scrollbar {{ width:5px; }}
::-webkit-scrollbar-track {{ background:rgba(255,255,255,0.03); }}
::-webkit-scrollbar-thumb {{ background:rgba(14,165,233,0.5); border-radius:99px; }}

/* ── ANIMATIONS ── */
@keyframes fadeUp {{ from {{opacity:0;transform:translateY(22px);}} to {{opacity:1;transform:translateY(0);}} }}
@keyframes shimmer {{ 0% {{background-position:-200% center;}} 100% {{background-position:200% center;}} }}
@keyframes glowPulse {{ 0%,100% {{opacity:0.6;}} 50% {{opacity:1;}} }}
@keyframes countUp {{ from {{opacity:0;transform:scale(0.75);}} to {{opacity:1;transform:scale(1);}} }}

section.main > div {{ animation:fadeUp 0.65s cubic-bezier(.2,.8,.2,1) both; }}

/* ── HEADINGS ── */
h1, h2, h3 {{
    font-family:'Space Grotesk',sans-serif !important;
    color:white !important;
    letter-spacing:-0.03em;
}}
h1 {{
    background:linear-gradient(120deg,#ffffff 10%,#7dd3fc 45%,#818cf8 75%,#ffffff 100%);
    background-size:300% auto;
    -webkit-background-clip:text !important;
    -webkit-text-fill-color:transparent !important;
    background-clip:text !important;
    animation:shimmer 5s linear infinite;
    font-size:clamp(1.6rem,3vw,2.6rem) !important;
}}
p, li {{ color:#e2e8f0 !important; font-size:clamp(13px,1.6vw,16px); line-height:1.7; }}

/* ════════════════════════════════════════
   SIDEBAR
════════════════════════════════════════ */
section[data-testid="stSidebar"] {{
    background:linear-gradient(180deg,rgba(3,10,30,0.97) 0%,rgba(5,18,50,0.96) 100%) !important;
    backdrop-filter:blur(28px) saturate(1.6) !important;
    -webkit-backdrop-filter:blur(28px) !important;
    border-right:1px solid rgba(14,165,233,0.18) !important;
    box-shadow:8px 0 50px rgba(0,0,0,0.6) !important;
}}
section[data-testid="stSidebar"] > div {{ padding-top:12px !important; }}

section[data-testid="stSidebar"] hr {{
    border:none !important;
    border-top:1px solid rgba(14,165,233,0.25) !important;
    margin:16px 0 !important;
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    color:#e2e8f0 !important;
    font-family:'Space Grotesk',sans-serif !important;
}}
section[data-testid="stSidebar"] label {{
    color:#7dd3fc !important;
    font-family:'JetBrains Mono',monospace !important;
    font-size:9.5px !important;
    letter-spacing:0.15em !important;
    text-transform:uppercase !important;
    font-weight:600 !important;
}}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {{
    color:#94a3b8 !important;
    font-size:13px !important;
}}

/* ── SIDEBAR NUMBER/SELECT INPUTS ── */
section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    background:rgba(226,240,255,0.92) !important;
    border-radius:11px !important;
    border:1.5px solid rgba(14,165,233,0.35) !important;
    transition:all 0.2s ease !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {{
    border-color:#38bdf8 !important;
    box-shadow:0 0 0 3px rgba(56,189,248,0.2), 0 0 14px rgba(56,189,248,0.3) !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="input"] input {{
    color:#0c1a35 !important;
    -webkit-text-fill-color:#0c1a35 !important;
    font-family:'JetBrains Mono',monospace !important;
    font-weight:600 !important;
    font-size:14px !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="select"] span {{
    color:#0c1a35 !important;
    font-weight:700 !important;
}}

/* ═══════════════════════════════════════
   SKY BLUE SLIDERS
   Filled portion = sky blue (#38bdf8)
   Unfilled portion = white/light
═══════════════════════════════════════ */
/* Remove default spinners */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {{ -webkit-appearance:none; margin:0; }}
input[type="number"] {{ -moz-appearance:textfield; }}

/* The full slider track (unfilled = white background) */
section[data-testid="stSidebar"] div[data-baseweb="slider"] > div {{
    background: rgba(255,255,255,0.85) !important;
    border-radius: 99px !important;
    height: 6px !important;
}}

/* The filled portion track (sky blue) */
section[data-testid="stSidebar"] div[data-baseweb="slider"] > div > div:first-child {{
    background: linear-gradient(90deg, #0ea5e9, #38bdf8) !important;
    border-radius: 99px !important;
    height: 6px !important;
    box-shadow: 0 0 8px rgba(56,189,248,0.6) !important;
}}

/* The thumb handle */
section[data-testid="stSidebar"] div[data-baseweb="slider"] [role="slider"] {{
    background: #ffffff !important;
    border: 2.5px solid #0ea5e9 !important;
    box-shadow: 0 0 0 3px rgba(14,165,233,0.25), 0 2px 8px rgba(0,0,0,0.3) !important;
    width: 18px !important;
    height: 18px !important;
    border-radius: 50% !important;
    transition: all 0.15s ease !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="slider"] [role="slider"]:hover {{
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 5px rgba(56,189,248,0.3), 0 2px 12px rgba(0,0,0,0.4) !important;
    transform: translateY(-50%) scale(1.15) !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="slider"] [role="slider"]:focus {{
    box-shadow: 0 0 0 5px rgba(56,189,248,0.4) !important;
}}

/* Hide tick bar numbers */
div[data-testid="stTickBar"] {{ display:none !important; }}

/* ── DROPDOWN ── */
div[data-baseweb="popover"] {{
    background:#07122A !important;
    border:1px solid rgba(56,189,248,0.22) !important;
    border-radius:14px !important;
}}
ul[role="listbox"] {{ background:#07122A !important; }}
li[role="option"] {{ color:#94a3b8 !important; font-weight:500 !important; }}
li[role="option"]:hover {{ background:rgba(56,189,248,0.14) !important; color:#38bdf8 !important; }}

/* ── SIDEBAR BUTTONS ── */
section[data-testid="stSidebar"] button {{
    background:linear-gradient(135deg,#0284c7 0%,#4f46e5 100%) !important;
    border-radius:12px !important;
    border:none !important;
    color:white !important;
    font-family:'Outfit',sans-serif !important;
    font-weight:700 !important;
    font-size:14px !important;
    box-shadow:0 4px 18px rgba(2,132,199,0.35) !important;
    transition:all 0.25s ease !important;
    letter-spacing:0.04em !important;
}}
section[data-testid="stSidebar"] button:hover {{
    transform:translateY(-2px) !important;
    box-shadow:0 8px 28px rgba(2,132,199,0.5) !important;
}}
section[data-testid="stSidebar"] button:active {{ transform:scale(0.96) !important; }}

/* ── DOWNLOAD BUTTON ── */
div.stDownloadButton > button {{
    background:linear-gradient(135deg,#059669 0%,#0891b2 100%) !important;
    border-radius:14px !important;
    border:none !important;
    color:white !important;
    font-family:'Outfit',sans-serif !important;
    font-weight:700 !important;
    font-size:15px !important;
    padding:14px 28px !important;
    width:100% !important;
    box-shadow:0 6px 24px rgba(5,150,105,0.4) !important;
    transition:all 0.25s ease !important;
    letter-spacing:0.05em !important;
}}
div.stDownloadButton > button:hover {{
    transform:translateY(-3px) !important;
    box-shadow:0 12px 36px rgba(5,150,105,0.55) !important;
}}

/* ── METRIC CARDS ── */
div[data-testid="metric-container"] {{
    background:linear-gradient(135deg,rgba(14,165,233,0.10),rgba(99,102,241,0.10)) !important;
    border:1px solid rgba(14,165,233,0.28) !important;
    border-radius:16px !important;
    padding:18px !important;
    transition:all 0.3s ease !important;
}}
div[data-testid="metric-container"]:hover {{
    border-color:rgba(56,189,248,0.5) !important;
    box-shadow:0 8px 24px rgba(14,165,233,0.18) !important;
    transform:translateY(-2px) !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-family:'Space Grotesk',sans-serif !important;
    font-size:2.1rem !important;
    font-weight:700 !important;
    color:#38bdf8 !important;
    animation:countUp 0.9s cubic-bezier(0.2,0.8,0.2,1);
}}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    font-family:'JetBrains Mono',monospace !important;
    font-size:9.5px !important;
    letter-spacing:0.12em !important;
    text-transform:uppercase !important;
    color:#64748b !important;
}}

/* ── ALERT BOXES ── */
div[data-testid="stSuccess"],div[data-testid="stWarning"],div[data-testid="stError"] {{
    border-radius:14px !important;
    animation:fadeUp 0.5s ease;
}}
div[data-testid="stSuccess"] {{ background:rgba(6,95,70,0.12)!important; border:1px solid rgba(16,185,129,0.4)!important; }}
div[data-testid="stSuccess"] p {{ color:#6ee7b7!important; font-weight:600; }}
div[data-testid="stWarning"] {{ background:rgba(146,64,14,0.12)!important; border:1px solid rgba(245,158,11,0.4)!important; }}
div[data-testid="stWarning"] p {{ color:#fde68a!important; font-weight:600; }}
div[data-testid="stError"]   {{ background:rgba(153,27,27,0.12)!important; border:1px solid rgba(239,68,68,0.4)!important; }}
div[data-testid="stError"] p {{ color:#fca5a5!important; font-weight:600; }}

/* ── HR ── */
hr {{ border:none!important; border-top:1px solid rgba(14,165,233,0.18)!important; margin:2rem 0!important; }}

/* ── GLASS CARD ── */
.glass-box {{
    background:linear-gradient(135deg,rgba(255,255,255,0.055),rgba(255,255,255,0.028));
    backdrop-filter:blur(22px) saturate(1.3);
    -webkit-backdrop-filter:blur(22px);
    border-radius:22px;
    padding:clamp(20px,4vw,38px);
    border:1px solid rgba(255,255,255,0.10);
    box-shadow:0 10px 40px rgba(0,0,0,0.38);
    margin-bottom:28px;
    transition:all 0.35s cubic-bezier(.2,.8,.2,1);
    position:relative; overflow:hidden;
}}
.glass-box::before {{
    content:'';
    position:absolute; top:0; left:15%; right:15%; height:1px;
    background:linear-gradient(90deg,transparent,rgba(125,211,252,0.4),transparent);
}}
.glass-box:hover {{
    transform:translateY(-5px);
    box-shadow:0 20px 50px rgba(14,165,233,0.2);
    border-color:rgba(125,211,252,0.25);
}}

/* ── GRADIENT RESULT BORDER ── */
.gradient-result {{
    position:relative;
    background:rgba(10,18,44,0.82);
    border-radius:20px;
    padding:clamp(16px,3vw,28px);
    box-shadow:0 12px 40px rgba(0,0,0,0.5);
    margin-bottom:24px;
    backdrop-filter:blur(16px);
}}
.gradient-result::before {{
    content:'';
    position:absolute; top:-2px; left:-2px; right:-2px; bottom:-2px;
    background:linear-gradient(135deg,#0ea5e9,#6366f1,#8b5cf6,#0ea5e9);
    border-radius:22px; z-index:-1;
    background-size:300% 300%;
    animation:shimmer 4s linear infinite;
}}

/* ── GAUGE GLOW ── */
.gauge-glow {{ position:relative; }}
.gauge-glow::after {{
    content:'';
    position:absolute; top:50%; left:50%;
    transform:translate(-50%,-50%);
    width:200px; height:200px;
    background:radial-gradient(circle,rgba(56,189,248,0.18) 0%,transparent 65%);
    z-index:-1; border-radius:50%;
    animation:glowPulse 3s ease infinite;
}}

/* ── PLOTLY CHARTS ── */
div[data-testid="stPlotlyChart"] {{
    transition:transform 0.3s ease,filter 0.3s ease;
    border-radius:16px; overflow:hidden;
}}
div[data-testid="stPlotlyChart"]:hover {{
    transform:scale(1.015);
    filter:drop-shadow(0 12px 24px rgba(14,165,233,0.18));
}}

/* ── SPINNER ── */
.stSpinner > div > div {{
    border-top-color:#38bdf8 !important;
    border-right-color:#0ea5e9 !important;
}}

/* ═══════════════════════════════════════
   RESPONSIVE DESIGN
═══════════════════════════════════════ */
/* Desktop large (1440px+) */
@media (min-width:1440px) {{
    .glass-box {{ padding:44px; }}
    h1 {{ font-size:2.8rem !important; }}
}}
/* Tablet (768–1024px) */
@media (max-width:1024px) {{
    .glass-box,.gradient-result {{ padding:20px; border-radius:18px; }}
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {{ font-size:1.8rem !important; }}
    section[data-testid="stSidebar"] {{ width:280px !important; }}
}}
/* Mobile (max 768px) */
@media (max-width:768px) {{
    .glass-box,.gradient-result {{ padding:16px; border-radius:16px; }}
    h1 {{ font-size:1.5rem !important; letter-spacing:-0.01em !important; }}
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{ font-size:12px !important; }}
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {{ font-size:1.5rem !important; }}
    div[data-testid="metric-container"] {{ padding:12px !important; }}
}}
/* Very small screens (max 480px) */
@media (max-width:480px) {{
    .glass-box {{ padding:14px !important; }}
    h1 {{ font-size:1.3rem !important; }}
    hr {{ margin:1.2rem 0 !important; }}
}}
/* Touch devices */
@media (hover:none) and (pointer:coarse) {{
    .glass-box:hover,
    div[data-testid="metric-container"]:hover {{ transform:none !important; }}
    div[data-testid="stPlotlyChart"]:hover {{ transform:none !important; filter:none !important; }}
    section[data-testid="stSidebar"] div[data-baseweb="slider"] [role="slider"]:hover {{
        transform:translateY(-50%) !important;
    }}
}}
/* Print media */
@media print {{
    .stApp::before, section[data-testid="stSidebar"] {{ display:none !important; }}
    .glass-box {{ border:1px solid #e2e8f0 !important; background:white !important; }}
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

    age    = st.sidebar.number_input("Age", 21, 100, 30)
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

    # ── MAIN AREA ────────────────────────────────────────────
    st.title("🩺 Diabetes Prediction System")
    st.markdown("AI-Powered Diabetes Risk Assessment Tool")

    if st.session_state.show_success:
        st.success("✅ Registration Successful!")
        st.session_state.show_success = False

    st.markdown("""
    <div class="glass-box section-gap">
        <h3 style="margin-top:0;">📋 About This System</h3>
        <p>This Diabetes Prediction System is an AI-powered medical risk assessment tool designed to estimate the likelihood of diabetes based on key health parameters such as glucose level, BMI, blood pressure, age, and family history.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── PREDICTION LOGIC ─────────────────────────────────────
    if predict_btn:
        with st.spinner("Analyzing risk factors..."):
            time.sleep(0.8)

            if "_id" in info:
                users_collection.update_one(
                    {"_id": info["_id"]}, {"$set": {"gender": gender}})

            input_data  = np.array([[pregnancies, glucose, bp, skin,
                                      insulin, bmi, dpf, age]])
            input_std   = scaler.transform(input_data)
            prediction  = model.predict(input_std)[0]
            probability = model.predict_proba(input_std)[0]

            prob_negative = probability[0] * 100
            prob_positive = probability[1] * 100

            if prob_positive < 30:    risk_label = "Low Risk"
            elif prob_positive < 70:  risk_label = "Moderate Risk"
            else:                     risk_label = "High Risk"

            ist          = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)

            predictions_collection.insert_one({
                "patient_id":     info["_id"],
                "patient_name":   info["name"],
                "age":            age,
                "gender":         gender,
                "glucose":        glucose,
                "blood_pressure": bp,
                "bmi":            bmi,
                "prediction":     risk_label,
                "probability":    round(prob_positive, 2),
                "created_at":     current_time.strftime("%d-%m-%Y %H:%M:%S")
            })

            # ── RESULTS UI ───────────────────────────────────
            st.markdown("---")
            st.header("Prediction Results")

            st.markdown('<div class="gradient-result">', unsafe_allow_html=True)
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
                st.markdown('<div class="gauge-glow">', unsafe_allow_html=True)
                gauge_color = ("#22c55e" if prob_positive < 30 else
                               "#f59e0b" if prob_positive < 70 else "#ef4444")
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=prob_positive,
                    number={"suffix": "%", "font": {"color": "white",
                                                     "size": 30, "family": "Outfit"}},
                    title={"text": "Risk Level",
                           "font": {"color": "#94a3b8", "size": 12}},
                    gauge={
                        "axis": {"range": [0, 100],
                                 "tickcolor": "rgba(255,255,255,0.18)",
                                 "tickwidth": 1},
                        "bar":  {"color": gauge_color, "thickness": 0.24},
                        "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
                        "steps": [
                            {"range": [0,  30], "color": "rgba(34,197,94,0.16)"},
                            {"range": [30, 70], "color": "rgba(245,158,11,0.16)"},
                            {"range": [70,100], "color": "rgba(239,68,68,0.16)"},
                        ],
                        "threshold": {"line": {"color": gauge_color, "width": 3},
                                      "thickness": 0.82, "value": prob_positive},
                    }
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                    height=260,
                    margin=dict(l=16, r=16, t=28, b=8),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── RISK FACTOR ANALYSIS ─────────────────────────
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

            # ── RECOMMENDATIONS ──────────────────────────────
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

            # ── CHARTS (UI) ──────────────────────────────────
            st.markdown('<div class="glass-box section-gap">', unsafe_allow_html=True)
            st.subheader("📊 Causes of Diabetes (Risk Contribution Analysis)")

            c_col1, c_col2 = st.columns([1, 1])
            cause_labels, cause_values = [], []

            if glucose >= 126: cause_labels.append("High Glucose");       cause_values.append(min(glucose / 2, 100))
            if bmi > 30:       cause_labels.append("High BMI");           cause_values.append(min(bmi * 2, 100))
            if age > 45:       cause_labels.append("Age Factor");         cause_values.append(min(age, 100))
            if bp > 120:       cause_labels.append("High Blood Pressure"); cause_values.append(min(bp, 100))
            if dpf > 0.5:      cause_labels.append("Genetic Risk (DPF)"); cause_values.append(min(dpf * 100, 100))
            if not cause_labels:
                cause_labels  = ["Healthy Indicators"]
                cause_values  = [100]

            scr_colors = ["#dc2626","#d97706","#2563eb","#7c3aed","#047857"]
            bar_col = [scr_colors[i % len(scr_colors)] for i in range(len(cause_labels))]

            bar_fig = go.Figure(go.Bar(
                x=cause_labels, y=cause_values,
                text=[f"{v:.1f}" for v in cause_values], textposition="auto",
                marker=dict(color=bar_col,
                            line=dict(color="rgba(255,255,255,0.18)", width=1.5)),
                textfont=dict(color="white", size=14, family="Outfit"),
            ))
            bar_fig.update_layout(
                title="Risk Factor Severity",
                xaxis_title="Causes", yaxis_title="Severity Level",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Outfit"),
                autosize=True, margin=dict(l=20, r=20, t=50, b=20),
            )
            bar_fig.update_xaxes(tickfont=dict(color="#94a3b8", size=13),
                                 showline=True, linecolor="rgba(255,255,255,0.12)")
            bar_fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.07)",
                                 zerolinecolor="rgba(255,255,255,0.12)")
            with c_col1:
                st.plotly_chart(bar_fig, use_container_width=True,
                                config={"responsive": True})

            pie_fig = go.Figure(data=[go.Pie(
                labels=cause_labels, values=cause_values, hole=0.48,
                marker=dict(colors=bar_col,
                            line=dict(color="rgba(0,0,0,0.3)", width=2)),
                textfont=dict(color="white", size=12, family="Outfit"),
            )])
            pie_fig.update_layout(
                title="Percentage Contribution",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Outfit"),
                autosize=True, margin=dict(l=20, r=20, t=50, b=20),
            )
            with c_col2:
                st.plotly_chart(pie_fig, use_container_width=True,
                                config={"responsive": True})
            st.markdown("</div>", unsafe_allow_html=True)

            # ── PDF ──────────────────────────────────────────
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
                file_name=f"Diabetes_Report_{info.get('name','Patient')}.pdf",
                mime="application/pdf",
            )

            st.markdown("---")
            st.warning("⚠️ Medical Disclaimer:\nThis tool does NOT replace professional medical advice.")


# ╔══════════════════════════════════════════════════════════════╗
# ║                      NAVIGATION                              ║
# ╚══════════════════════════════════════════════════════════════╝
if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
