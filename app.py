# ============================================================
# DIABETES PREDICTION SYSTEM
# Multi-page PDF · Full Responsive UI (any screen/OS)
# ============================================================
import streamlit as st
import numpy as np
import joblib
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import base64, re, math, time
import pycountry, phonenumbers

from reportlab.pdfgen    import canvas as rl_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib       import colors as rl_colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from io import BytesIO

from pymongo.mongo_client import MongoClient
from pymongo.server_api   import ServerApi
from datetime import datetime
import uuid, pytz

# ── MongoDB ──────────────────────────────────────────────────
uri = "mongodb+srv://diabetes_user:Diabetes%40123@diabetescluster.oxegep6.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db     = client["diabetes_app"]
users_collection       = db["registered_users"]
predictions_collection = db["predictions"]

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="Diabetes Prediction System",
                   page_icon="🩺", layout="wide")

for k, v in [("registered", False), ("patient_info", {}), ("show_success", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ──────────────────────────────────────────────────
def get_b64(path):
    try:
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except FileNotFoundError: return ""


# ============================================================
# PDF — COLOUR PALETTE (shared across all pages)
# ============================================================
C = {
    "navy":     rl_colors.HexColor("#0b1f3a"),
    "teal":     rl_colors.HexColor("#0e7490"),
    "teal2":    rl_colors.HexColor("#0891b2"),
    "teallt":   rl_colors.HexColor("#cffafe"),
    "tealice":  rl_colors.HexColor("#e0f2fe"),
    "white":    rl_colors.white,
    "offwhite": rl_colors.HexColor("#f8fafc"),
    "slate":    rl_colors.HexColor("#334155"),
    "grey":     rl_colors.HexColor("#475569"),
    "grylbl":   rl_colors.HexColor("#64748b"),
    "grydiv":   rl_colors.HexColor("#e2e8f0"),
    "gryrow":   rl_colors.HexColor("#f1f5f9"),
    "tblkey":   rl_colors.HexColor("#f0f9ff"),
    "tblval":   rl_colors.HexColor("#ffffff"),
    "green":    rl_colors.HexColor("#047857"),
    "greenb":   rl_colors.HexColor("#ecfdf5"),
    "greendk":  rl_colors.HexColor("#14532d"),
    "amber":    rl_colors.HexColor("#b45309"),
    "amberb":   rl_colors.HexColor("#fffbeb"),
    "red":      rl_colors.HexColor("#b91c1c"),
    "redb":     rl_colors.HexColor("#fef2f2"),
    "reddk":    rl_colors.HexColor("#7f1d1d"),
    "purple":   rl_colors.HexColor("#7c3aed"),
    "blue":     rl_colors.HexColor("#2563eb"),
    "cyan":     rl_colors.HexColor("#7dd3fc"),
}

_BAR_COLORS = ["#dc2626","#d97706","#2563eb","#7c3aed","#047857","#0891b2"]


# ============================================================
# CHART GENERATORS  (higher resolution for PDF)
# ============================================================
def _bar_buf(labels, values, title="Risk Factor Severity"):
    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=200)
    fig.patch.set_facecolor("white"); ax.set_facecolor("#f8fafc")
    cols = [_BAR_COLORS[i % len(_BAR_COLORS)] for i in range(len(labels))]
    bars = ax.bar(labels, values, color=cols, edgecolor="white",
                  linewidth=1.8, zorder=3, width=0.6)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1.5,
                f"{val:.0f}", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color="#1e293b")
    ax.set_ylim(0, max(values)*1.4 if values else 110)
    ax.set_title(title, fontsize=12, fontweight="bold", color="#0f172a", pad=10)
    ax.set_xlabel("Risk Factors", fontsize=9, color="#64748b", labelpad=5)
    ax.set_ylabel("Severity Level (0–100)", fontsize=9, color="#64748b", labelpad=5)
    ax.tick_params(axis="x", labelsize=8.5, colors="#64748b", rotation=12)
    ax.tick_params(axis="y", labelsize=8.5, colors="#64748b")
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#e2e8f0")
    ax.yaxis.grid(True, color="#e2e8f0", linewidth=0.6, linestyle="--", zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout(pad=1.0)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=200, facecolor="white")
    plt.close(fig); buf.seek(0); return buf

def _pie_buf(labels, values):
    fig, ax = plt.subplots(figsize=(5.5, 4.0), dpi=200)
    fig.patch.set_facecolor("white")
    cols = [_BAR_COLORS[i % len(_BAR_COLORS)] for i in range(len(labels))]
    wedges, _, autos = ax.pie(
        values, labels=None, colors=cols, autopct="%1.1f%%",
        startangle=140, wedgeprops=dict(width=0.6, edgecolor="white", linewidth=2.2),
        pctdistance=0.78)
    for at in autos: at.set_fontsize(8.5); at.set_fontweight("bold"); at.set_color("white")
    ax.legend(wedges, labels, loc="lower center",
              bbox_to_anchor=(0.5,-0.14), ncol=2, fontsize=8, frameon=False)
    ax.set_title("Contribution to Overall Risk", fontsize=12,
                 fontweight="bold", color="#0f172a", pad=10)
    plt.tight_layout(pad=1.0)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=200, facecolor="white")
    plt.close(fig); buf.seek(0); return buf

def _gauge_buf(prob):
    fig, ax = plt.subplots(figsize=(5.5, 3.2), dpi=200,
                            subplot_kw=dict(polar=False))
    fig.patch.set_facecolor("white")
    color = "#22c55e" if prob < 30 else "#f59e0b" if prob < 70 else "#ef4444"
    # draw semicircle gauge using wedges
    import numpy as np2
    theta = np2.linspace(0, np2.pi, 300)
    zones = [(0,30,"#dcfce7"),(30,70,"#fef9c3"),(70,100,"#fee2e2")]
    for lo,hi,zc in zones:
        t0 = np2.pi*(1 - lo/100); t1 = np2.pi*(1 - hi/100)
        th = np2.linspace(t1,t0,100)
        ax.fill_between(np2.cos(th), np2.sin(th)*0.55, np2.sin(th), alpha=0.9, color=zc)
    # needle
    angle = np2.pi*(1 - prob/100)
    ax.annotate("", xy=(np2.cos(angle)*0.72, np2.sin(angle)*0.72),
                xytext=(0,0), arrowprops=dict(arrowstyle="-|>", color=color, lw=2.5,
                mutation_scale=18))
    ax.set_xlim(-1.1,1.1); ax.set_ylim(-0.15,1.05)
    ax.axis("off")
    ax.text(0,-0.08, f"{prob:.1f}%", ha="center", va="bottom",
            fontsize=22, fontweight="bold", color=color)
    ax.text(-0.95,0.05,"0%",fontsize=8,color="#64748b",ha="center")
    ax.text(0,1.02,"50%",fontsize=8,color="#64748b",ha="center")
    ax.text(0.95,0.05,"100%",fontsize=8,color="#64748b",ha="center")
    ax.set_title("Diabetes Risk Probability", fontsize=11,
                 fontweight="bold", color="#0f172a", pad=4)
    plt.tight_layout(pad=0.5)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=200, facecolor="white")
    plt.close(fig); buf.seek(0); return buf


# ============================================================
# PDF BUILDER  — Professional multi-page A4 Hospital Report
# ============================================================
def build_hospital_pdf(info, age, gender, glucose, bp, skin, insulin, bmi, dpf,
                        pregnancies, prob_positive, risk_label, current_time,
                        cause_labels, cause_values, recs_for_pdf,
                        risk_factors, positive_factors):

    W, H = A4
    M    = 17 * mm
    CW   = W - 2 * M
    TOTAL_PAGES = 3

    buf = BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)

    # ── Shared date/time string ───────────────────────────────
    dt_str = current_time.strftime("%d %B %Y  |  %I:%M:%S %p IST")

    # ────────────────────────────────────────────────────────
    # HELPER FUNCTIONS
    # ────────────────────────────────────────────────────────
    def page_header(page_num, subtitle=""):
        """Dark navy header on every page."""
        BH = 24 * mm
        c.setFillColor(C["navy"]); c.rect(0, H-BH, W, BH, fill=1, stroke=0)
        c.setFillColor(C["teal"]);  c.rect(0, H-2.5*mm, W, 2.5*mm, fill=1, stroke=0)
        # Left
        c.setFillColor(C["white"]); c.setFont("Helvetica-Bold", 13.5)
        c.drawString(M, H-9*mm, "Diabetes Prediction System")
        c.setFillColor(C["cyan"]); c.setFont("Helvetica", 7.2)
        sub = subtitle if subtitle else "Clinical AI Risk Assessment  ·  Confidential Medical Document"
        c.drawString(M, H-15.5*mm, sub)
        # Right
        pid = info.get("_id","N/A").replace("-","")
        c.setFillColor(C["cyan"]); c.setFont("Helvetica-Bold", 7.2)
        c.drawRightString(W-M, H-9*mm,  f"Patient ID:  {pid}")
        c.setFont("Helvetica", 7)
        c.drawRightString(W-M, H-15.5*mm, dt_str)
        c.drawRightString(W-M, H-21*mm, f"Page {page_num} of {TOTAL_PAGES}")
        return H - BH - 6*mm

    def page_footer():
        """Light footer band at bottom of every page."""
        FH = 14*mm
        c.setFillColor(C["gryrow"]); c.rect(0, 0, W, FH, fill=1, stroke=0)
        c.setStrokeColor(C["teal"]); c.setLineWidth(0.7); c.line(0, FH, W, FH)
        c.setFillColor(C["grey"]); c.setFont("Helvetica-Oblique", 6)
        c.drawString(M, 9.5*mm,
            "MEDICAL DISCLAIMER: This AI-generated report is for informational "
            "purposes only and does not replace professional medical advice.")
        c.setFont("Helvetica", 6)
        c.drawString(M, 5.2*mm,
            "Consult a qualified healthcare professional for clinical diagnosis, "
            "interpretation, and treatment.")
        c.setFont("Helvetica-Bold", 6)
        c.drawRightString(W-M, 7*mm, "Diabetes Prediction System  ·  CONFIDENTIAL")
        return FH + 5*mm   # y start for content above footer

    def sec_head(y, label, icon=""):
        """Full-width teal section header bar."""
        SH = 7.5*mm
        c.setFillColor(C["teal"]); c.rect(M, y-SH, CW, SH, fill=1, stroke=0)
        # left accent stripe
        c.setFillColor(C["teal2"]); c.rect(M, y-SH, 3*mm, SH, fill=1, stroke=0)
        c.setFillColor(C["white"]); c.setFont("Helvetica-Bold", 9)
        txt = f"  {icon}  {label}".strip() if icon else f"  {label}"
        c.drawString(M+5*mm, y-5*mm, txt.upper())
        return y - SH

    def kv_table(y, rows, key_w, row_h=9*mm):
        """Key | Value table, auto-shrink value text, returns bottom y."""
        val_w = CW - key_w
        for i, (k, v) in enumerate(rows):
            ry  = y - (i+1)*row_h
            alt = (i % 2 == 0)
            c.setFillColor(C["gryrow"] if alt else C["tblkey"])
            c.rect(M, ry, key_w, row_h, fill=1, stroke=0)
            c.setFillColor(C["offwhite"] if alt else C["tblval"])
            c.rect(M+key_w, ry, val_w, row_h, fill=1, stroke=0)
            c.setStrokeColor(C["grydiv"]); c.setLineWidth(0.3)
            c.line(M, ry, M+CW, ry)
            c.line(M+key_w, ry, M+key_w, ry+row_h)
            # key
            c.setFillColor(C["grylbl"]); c.setFont("Helvetica-Bold", 7.5)
            c.drawString(M+3.5*mm, ry+3.2*mm, str(k))
            # value — auto-fit
            vstr = str(v); avail = val_w - 6*mm; fs = 8.5
            c.setFont("Helvetica-Bold", fs)
            while c.stringWidth(vstr,"Helvetica-Bold",fs) > avail and fs > 6:
                fs -= 0.2
            if c.stringWidth(vstr,"Helvetica-Bold",fs) > avail:
                while c.stringWidth(vstr+"…","Helvetica-Bold",fs) > avail and len(vstr)>2:
                    vstr = vstr[:-1]
                vstr += "…"
            c.setFillColor(C["navy"]); c.setFont("Helvetica-Bold", fs)
            c.drawString(M+key_w+3.5*mm, ry+3.2*mm, vstr)
        th = len(rows)*row_h
        c.setStrokeColor(C["teal"]); c.setLineWidth(1.0)
        c.rect(M, y-th, CW, th, fill=0, stroke=1)
        c.setLineWidth(2); c.line(M, y, M+CW, y)
        return y - th

    def risk_banner(y, prob):
        if prob < 30:   BC,BG,BT,BI = C["green"],C["greenb"],"LOW RISK","Diabetes Unlikely"
        elif prob < 70: BC,BG,BT,BI = C["amber"],C["amberb"],"MODERATE RISK","Possible Diabetes"
        else:           BC,BG,BT,BI = C["red"],C["redb"],"HIGH RISK","Diabetes Likely"
        BH2 = 22*mm
        c.setFillColor(BC);  c.rect(M, y-BH2, 5*mm, BH2, fill=1, stroke=0)
        c.setFillColor(BG);  c.rect(M+5*mm, y-BH2, CW-5*mm, BH2, fill=1, stroke=0)
        c.setStrokeColor(BC); c.setLineWidth(1.2)
        c.rect(M, y-BH2, CW, BH2, fill=0, stroke=1)
        c.setFillColor(BC); c.setFont("Helvetica-Bold", 16)
        c.drawString(M+9*mm, y-8*mm, BT)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(M+9*mm, y-15*mm, BI)
        c.setFillColor(C["slate"]); c.setFont("Helvetica", 7.5)
        c.drawRightString(W-M-4*mm, y-10*mm, "Probability Score")
        c.setFillColor(BC); c.setFont("Helvetica-Bold", 20)
        c.drawRightString(W-M-4*mm, y-20*mm, f"{prob:.1f}%")
        return y - BH2

    def stat_box(x, y, w, h, label, value, unit, color):
        """Small stat highlight box."""
        c.setFillColor(C["offwhite"]); c.rect(x, y, w, h, fill=1, stroke=0)
        c.setStrokeColor(color); c.setLineWidth(0.8)
        c.rect(x, y, w, h, fill=0, stroke=1)
        c.setFillColor(color); c.rect(x, y+h-2*mm, w, 2*mm, fill=1, stroke=0)
        c.setFillColor(C["grylbl"]); c.setFont("Helvetica-Bold", 6.5)
        c.drawCentredString(x+w/2, y+h-8*mm, label.upper())
        c.setFillColor(C["navy"]); c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(x+w/2, y+h//2-2*mm, str(value))
        c.setFillColor(C["grylbl"]); c.setFont("Helvetica", 6.5)
        c.drawCentredString(x+w/2, y+3*mm, unit)

    # ════════════════════════════════════════════════════════
    # PAGE 1 — Cover + Patient Profile + Clinical Summary
    # ════════════════════════════════════════════════════════
    y = page_header(1, "Patient Registration & Clinical Data Summary")

    # Report title block
    c.setFillColor(C["tealice"]); c.rect(M, y-18*mm, CW, 18*mm, fill=1, stroke=0)
    c.setStrokeColor(C["teal"]); c.setLineWidth(1.5)
    c.rect(M, y-18*mm, CW, 18*mm, fill=0, stroke=1)
    c.setFillColor(C["navy"]); c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(W/2, y-8*mm, "DIABETES RISK PREDICTION REPORT")
    c.setFillColor(C["teal"]); c.setFont("Helvetica", 9)
    c.drawCentredString(W/2, y-14.5*mm,
        f"Generated:  {current_time.strftime('%A, %d %B %Y  at  %I:%M:%S %p')}  (IST)")
    y -= 18*mm + 7*mm

    # ── Patient Profile ───────────────────────────────────
    y = sec_head(y, "Patient Profile", "👤")
    pid_clean = info.get("_id","N/A").replace("-","")
    patient_rows = [
        ("Patient ID",    pid_clean),
        ("Full Name",     info.get("name",    "N/A")),
        ("Phone Number",  info.get("phone",   "N/A")),
        ("Email Address", info.get("email",   "N/A")),
        ("Country",       info.get("country", "N/A")),
        ("Address",       info.get("address", "N/A")),
        ("Gender",        gender),
        ("Registration Date", info.get("created_at","N/A")),
    ]
    y = kv_table(y, patient_rows, 48*mm)
    y -= 6*mm

    # ── Clinical Inputs ───────────────────────────────────
    y = sec_head(y, "Clinical Input Parameters", "🔬")
    clinical_rows = [
        ("Age",                          f"{age} years"),
        ("Gender",                        gender),
        ("Glucose Level",               f"{glucose} mg/dL"),
        ("Blood Pressure",              f"{bp} mmHg"),
        ("Skin Thickness",              f"{skin} mm"),
        ("Insulin Level",               f"{insulin} µIU/mL"),
        ("Body Mass Index (BMI)",       f"{bmi:.1f} kg/m²"),
        ("Diabetes Pedigree Function",   f"{dpf:.3f}"),
    ]
    if gender == "Female":
        clinical_rows.insert(2, ("Number of Pregnancies", str(pregnancies)))
    y = kv_table(y, clinical_rows, 62*mm)
    y -= 6*mm

    # ── Quick stats row ───────────────────────────────────
    y = sec_head(y, "Key Metrics at a Glance", "📊")
    y -= 2*mm
    BOX_W = CW/4 - 2*mm; BOX_H = 20*mm
    stats = [
        ("Glucose","mg/dL", glucose, C["red"]   if glucose>=126 else C["amber"] if glucose>=100 else C["green"]),
        ("BMI","kg/m²", f"{bmi:.1f}", C["red"]  if bmi>30 else C["green"]),
        ("Blood Pressure","mmHg", bp, C["red"]  if bp>130 else C["amber"] if bp>120 else C["green"]),
        ("DPF Score","index", f"{dpf:.2f}", C["red"] if dpf>0.5 else C["green"]),
    ]
    for i,(lbl,unit,val,col) in enumerate(stats):
        stat_box(M + i*(BOX_W+2.5*mm), y-BOX_H, BOX_W, BOX_H, lbl, val, unit, col)
    y -= BOX_H + 4*mm

    page_footer()
    c.showPage()   # ── end page 1 ──

    # ════════════════════════════════════════════════════════
    # PAGE 2 — Risk Assessment + Charts + Visualisations
    # ════════════════════════════════════════════════════════
    y = page_header(2, "Risk Assessment Results & Data Visualisation")

    # ── Risk result banner ────────────────────────────────
    y = sec_head(y, "AI Risk Assessment Result", "🤖")
    y -= 2*mm
    y = risk_banner(y, prob_positive)
    y -= 6*mm

    # ── Probability breakdown (two stat boxes) ────────────
    y = sec_head(y, "Probability Analysis", "📈")
    y -= 2*mm
    PBOX_W = CW/2 - 3*mm; PBOX_H = 18*mm
    # Non-diabetic
    c.setFillColor(C["greenb"]); c.rect(M, y-PBOX_H, PBOX_W, PBOX_H, fill=1, stroke=0)
    c.setStrokeColor(C["green"]); c.setLineWidth(1); c.rect(M, y-PBOX_H, PBOX_W, PBOX_H, fill=0, stroke=1)
    c.setFillColor(C["green"]); c.setFont("Helvetica-Bold", 7); c.drawCentredString(M+PBOX_W/2, y-5*mm, "NON-DIABETIC PROBABILITY")
    c.setFont("Helvetica-Bold", 20); c.drawCentredString(M+PBOX_W/2, y-14*mm, f"{100-prob_positive:.1f}%")
    # Diabetic
    dx = M + PBOX_W + 6*mm
    if prob_positive < 30:   dc,db = C["green"],C["greenb"]
    elif prob_positive < 70: dc,db = C["amber"],C["amberb"]
    else:                    dc,db = C["red"],C["redb"]
    c.setFillColor(db); c.rect(dx, y-PBOX_H, PBOX_W, PBOX_H, fill=1, stroke=0)
    c.setStrokeColor(dc); c.setLineWidth(1); c.rect(dx, y-PBOX_H, PBOX_W, PBOX_H, fill=0, stroke=1)
    c.setFillColor(dc); c.setFont("Helvetica-Bold", 7); c.drawCentredString(dx+PBOX_W/2, y-5*mm, "DIABETIC PROBABILITY")
    c.setFont("Helvetica-Bold", 20); c.drawCentredString(dx+PBOX_W/2, y-14*mm, f"{prob_positive:.1f}%")
    y -= PBOX_H + 6*mm

    # ── Gauge chart ───────────────────────────────────────
    y = sec_head(y, "Risk Probability Gauge", "🎯")
    y -= 2*mm
    GAUGE_H = 65*mm
    c.setFillColor(C["offwhite"]); c.rect(M, y-GAUGE_H, CW, GAUGE_H, fill=1, stroke=0)
    c.setStrokeColor(C["teal"]); c.setLineWidth(0.8)
    c.rect(M, y-GAUGE_H, CW, GAUGE_H, fill=0, stroke=1)
    g_img = ImageReader(_gauge_buf(prob_positive))
    g_w   = CW * 0.55
    c.drawImage(g_img, M + (CW-g_w)/2, y-GAUGE_H+2*mm,
                width=g_w, height=GAUGE_H-4*mm,
                preserveAspectRatio=True, anchor="c")
    y -= GAUGE_H + 6*mm

    # ── Bar chart ─────────────────────────────────────────
    y = sec_head(y, "Risk Factor Severity — Bar Chart", "📊")
    y -= 2*mm
    BCH = 75*mm
    c.setFillColor(C["offwhite"]); c.rect(M, y-BCH, CW, BCH, fill=1, stroke=0)
    c.setStrokeColor(C["teal"]); c.setLineWidth(0.8)
    c.rect(M, y-BCH, CW, BCH, fill=0, stroke=1)
    bar_img = ImageReader(_bar_buf(cause_labels, cause_values))
    c.drawImage(bar_img, M+2*mm, y-BCH+2*mm, width=CW-4*mm, height=BCH-4*mm,
                preserveAspectRatio=True, anchor="c")
    y -= BCH + 6*mm

    # ── Pie chart ─────────────────────────────────────────
    y = sec_head(y, "Risk Contribution — Pie Chart", "🥧")
    y -= 2*mm
    PCH = 75*mm
    c.setFillColor(C["offwhite"]); c.rect(M, y-PCH, CW, PCH, fill=1, stroke=0)
    c.setStrokeColor(C["teal"]); c.setLineWidth(0.8)
    c.rect(M, y-PCH, CW, PCH, fill=0, stroke=1)
    pie_img = ImageReader(_pie_buf(cause_labels, cause_values))
    c.drawImage(pie_img, M+2*mm, y-PCH+2*mm, width=CW-4*mm, height=PCH-4*mm,
                preserveAspectRatio=True, anchor="c")
    y -= PCH + 4*mm

    page_footer()
    c.showPage()   # ── end page 2 ──

    # ════════════════════════════════════════════════════════
    # PAGE 3 — Risk Factors + Recommendations + Summary
    # ════════════════════════════════════════════════════════
    y = page_header(3, "Clinical Analysis, Recommendations & Medical Summary")

    # ── Risk Factor Analysis ──────────────────────────────
    y = sec_head(y, "Risk Factor Analysis", "⚠️")
    y -= 1*mm
    RFH = 8*mm
    if risk_factors:
        c.setFillColor(C["redb"]); c.rect(M, y-6*mm, CW, 6*mm, fill=1, stroke=0)
        c.setFillColor(C["red"]);  c.setFont("Helvetica-Bold", 8)
        c.drawString(M+4*mm, y-4*mm, "⬤  IDENTIFIED RISK FACTORS")
        y -= 6*mm
        for item in risk_factors:
            c.setFillColor(rl_colors.HexColor("#fff5f5"))
            c.rect(M, y-RFH, CW, RFH, fill=1, stroke=0)
            c.setFillColor(C["red"]); c.rect(M, y-RFH, 3*mm, RFH, fill=1, stroke=0)
            # auto-fit text
            fs=8.5; t=f"  ✗   {item}"; c.setFont("Helvetica-Bold",fs)
            while c.stringWidth(t,"Helvetica-Bold",fs)>CW-8*mm and fs>7: fs-=0.2
            c.setFont("Helvetica-Bold",fs); c.setFillColor(C["reddk"])
            c.drawString(M+5*mm, y-RFH/2-1.5*mm, t)
            c.setStrokeColor(C["grydiv"]); c.setLineWidth(0.3)
            c.line(M, y-RFH, M+CW, y-RFH)
            y -= RFH + 0.5*mm
        y -= 2*mm

    if positive_factors:
        c.setFillColor(C["greenb"]); c.rect(M, y-6*mm, CW, 6*mm, fill=1, stroke=0)
        c.setFillColor(C["green"]);  c.setFont("Helvetica-Bold", 8)
        c.drawString(M+4*mm, y-4*mm, "⬤  POSITIVE HEALTH INDICATORS")
        y -= 6*mm
        for item in positive_factors:
            c.setFillColor(rl_colors.HexColor("#f0fdf4"))
            c.rect(M, y-RFH, CW, RFH, fill=1, stroke=0)
            c.setFillColor(C["green"]); c.rect(M, y-RFH, 3*mm, RFH, fill=1, stroke=0)
            fs=8.5; t=f"  ✓   {item}"; c.setFont("Helvetica-Bold",fs)
            while c.stringWidth(t,"Helvetica-Bold",fs)>CW-8*mm and fs>7: fs-=0.2
            c.setFont("Helvetica-Bold",fs); c.setFillColor(C["greendk"])
            c.drawString(M+5*mm, y-RFH/2-1.5*mm, t)
            c.setStrokeColor(C["grydiv"]); c.setLineWidth(0.3)
            c.line(M, y-RFH, M+CW, y-RFH)
            y -= RFH + 0.5*mm
        y -= 2*mm

    c.setStrokeColor(C["teal"]); c.setLineWidth(0.8)
    y -= 5*mm

    # ── Medical Recommendations ───────────────────────────
    y = sec_head(y, "Medical Recommendations", "💊")
    y -= 1*mm
    # intro note
    c.setFillColor(C["tealice"]); c.rect(M, y-7*mm, CW, 7*mm, fill=1, stroke=0)
    c.setStrokeColor(C["teal"]); c.setLineWidth(0.4)
    c.rect(M, y-7*mm, CW, 7*mm, fill=0, stroke=1)
    c.setFillColor(C["navy"]); c.setFont("Helvetica-Bold", 7.5)
    c.drawString(M+4*mm, y-4.8*mm,
        "Based on the AI risk assessment, the following clinical recommendations are advised:")
    y -= 7*mm + 1*mm
    for idx, r in enumerate(recs_for_pdf):
        c.setFillColor(C["tealice"] if idx%2==0 else C["offwhite"])
        c.rect(M, y-RFH, CW, RFH, fill=1, stroke=0)
        c.setFillColor(C["teal"]); c.circle(M+4.5*mm, y-RFH/2, 2*mm, fill=1, stroke=0)
        c.setFillColor(C["white"]); c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(M+4.5*mm, y-RFH/2-1*mm, str(idx+1))
        fs=8.5; t=str(r); c.setFont("Helvetica",fs)
        while c.stringWidth(t,"Helvetica",fs)>CW-12*mm and fs>7: fs-=0.2
        c.setFont("Helvetica",fs); c.setFillColor(C["navy"])
        c.drawString(M+9.5*mm, y-RFH/2-1.5*mm, t)
        c.setStrokeColor(C["grydiv"]); c.setLineWidth(0.3)
        c.line(M, y-RFH, M+CW, y-RFH)
        y -= RFH + 0.5*mm
    c.setStrokeColor(C["teal"]); c.setLineWidth(0.8)
    c.rect(M, y, CW, (len(recs_for_pdf)*(RFH+0.5*mm))+7*mm+2*mm, fill=0, stroke=1)
    y -= 7*mm

    # ── Clinical Summary Table ─────────────────────────────
    y = sec_head(y, "Clinical Summary & Report Details", "📋")
    summary_rows = [
        ("Report Generated",     current_time.strftime("%d %B %Y  at  %I:%M:%S %p IST")),
        ("Patient Name",         info.get("name","N/A")),
        ("Patient ID",           info.get("_id","N/A").replace("-","")),
        ("AI Prediction",        risk_label),
        ("Risk Probability",     f"{prob_positive:.2f}%"),
        ("Prediction Confidence",f"{100-abs(50-prob_positive)*0.5:.1f}%  (SVM Model)"),
        ("Model Architecture",   "Support Vector Machine (RBF Kernel)"),
        ("Report Status",        "CONFIDENTIAL — FOR CLINICAL USE ONLY"),
    ]
    y = kv_table(y, summary_rows, 58*mm, row_h=8.5*mm)
    y -= 6*mm

    # ── Important Notice box ──────────────────────────────
    NOTICE_H = 24*mm
    c.setFillColor(C["amberb"]); c.rect(M, y-NOTICE_H, CW, NOTICE_H, fill=1, stroke=0)
    c.setFillColor(C["amber"]); c.rect(M, y-NOTICE_H, 4*mm, NOTICE_H, fill=1, stroke=0)
    c.setStrokeColor(C["amber"]); c.setLineWidth(1)
    c.rect(M, y-NOTICE_H, CW, NOTICE_H, fill=0, stroke=1)
    c.setFillColor(C["amber"]); c.setFont("Helvetica-Bold", 9)
    c.drawString(M+7*mm, y-6*mm, "⚠  IMPORTANT MEDICAL NOTICE")
    notice_lines = [
        "This report has been generated by an AI-powered diabetes prediction system using a trained",
        "Support Vector Machine model. The results are indicative and NOT a definitive medical diagnosis.",
        "Always consult a qualified healthcare professional before making any medical decisions.",
        "Early detection and regular monitoring are key to effective diabetes management.",
    ]
    c.setFillColor(C["slate"]); c.setFont("Helvetica", 7)
    for i, line in enumerate(notice_lines):
        c.drawString(M+7*mm, y-12*mm - i*4.5*mm, line)
    y -= NOTICE_H + 4*mm

    # ── Signature / authentication block ──────────────────
    SIG_H = 18*mm
    c.setFillColor(C["gryrow"]); c.rect(M, y-SIG_H, CW, SIG_H, fill=1, stroke=0)
    c.setStrokeColor(C["grydiv"]); c.setLineWidth(0.5)
    c.rect(M, y-SIG_H, CW, SIG_H, fill=0, stroke=1)
    # Left sig
    c.setFillColor(C["grydiv"]); c.setLineWidth(0.4)
    c.line(M+10*mm, y-8*mm, M+65*mm, y-8*mm)
    c.setFillColor(C["grylbl"]); c.setFont("Helvetica", 6.5)
    c.drawString(M+10*mm, y-13*mm, "Authorised Healthcare Professional Signature")
    # Right sig
    c.line(M+CW-65*mm, y-8*mm, M+CW-10*mm, y-8*mm)
    c.drawRightString(M+CW-10*mm, y-13*mm, "Date & Stamp")
    # Centre stamp
    c.setFillColor(C["teal"]); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(W/2, y-6*mm, "AI-GENERATED REPORT")
    c.setFont("Helvetica", 6); c.setFillColor(C["grylbl"])
    c.drawCentredString(W/2, y-11*mm, f"Report ID: {info.get('_id','N/A').replace('-','')}-{current_time.strftime('%Y%m%d%H%M%S')}")

    page_footer()
    c.save()
    return buf.getvalue()


# ============================================================
# CSS HELPERS
# ============================================================
COMMON_FONTS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Syne:wght@700;800&family=JetBrains+Mono:wght@400;600&display=swap');
"""

RESPONSIVE_CSS = """
/* ═══════════════════════════════════════════════════════════
   FULLY RESPONSIVE  —  Mobile · Tablet · Desktop · All OS
   ══════════════════════════════════════════════════════════ */

/* 1. CSS custom properties — single source of truth */
:root {
  --accent:     #0891b2;
  --accent-dk:  #0e7490;
  --accent-lt:  #67e8f9;
  --navy:       #0b1f3a;
  --card-bg:    rgba(255,255,255,0.05);
  --card-bdr:   rgba(255,255,255,0.10);
  --radius-lg:  18px;
  --radius-md:  12px;
  --radius-sm:  8px;
  --shadow-md:  0 8px 32px rgba(0,0,0,0.35);
  --shadow-lg:  0 16px 48px rgba(0,0,0,0.5);
  --transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}

/* 2. Base reset for consistent cross-OS rendering */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }
body { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }

/* 3. Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(8,145,178,.4); border-radius: 99px; }

/* 4. Page entry animation */
@keyframes fadeUp { from{opacity:0;transform:translateY(18px)} to{opacity:1;transform:translateY(0)} }
.stApp > header + div { animation: fadeUp 0.5s ease-out; }

/* 5. Global text */
h1,h2,h3,h4 { color: white !important; font-family: 'Syne',sans-serif !important; letter-spacing:-0.02em; }
p,li,span { color: #e2e8f0 !important; }
ul { line-height: 1.85; }

/* 6. Glass card utility */
.glass-box {
  background: var(--card-bg);
  backdrop-filter: blur(20px) saturate(1.3);
  -webkit-backdrop-filter: blur(20px) saturate(1.3);
  border-radius: var(--radius-lg);
  padding: clamp(18px, 3vw, 36px);
  border: 1px solid var(--card-bdr);
  box-shadow: var(--shadow-md);
  margin-bottom: clamp(16px, 2vw, 28px);
  transition: var(--transition);
}
.glass-box:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: rgba(103,232,249,0.28);
}

/* 7. Gradient-border result card */
.gradient-result {
  position: relative;
  background: rgba(15,23,42,0.82);
  border-radius: var(--radius-lg);
  padding: clamp(16px, 2.5vw, 28px);
  box-shadow: var(--shadow-lg);
  margin-bottom: clamp(12px, 2vw, 24px);
}
.gradient-result::before {
  content:"";
  position:absolute; inset:-2px;
  background:linear-gradient(135deg,#0891b2,#3b82f6,#8b5cf6);
  border-radius:calc(var(--radius-lg) + 2px); z-index:-1;
  background-size:200% 200%;
  animation: gradBdr 3s ease infinite;
}
@keyframes gradBdr { 0%,100%{background-position:0 50%} 50%{background-position:100% 50%} }

/* 8. Gauge glow wrapper */
.gauge-glow::after {
  content:''; position:absolute; top:50%;left:50%;
  transform:translate(-50%,-50%);
  width:min(220px,40vw); height:min(220px,40vw);
  background:radial-gradient(circle,rgba(103,232,249,.18) 0%,transparent 65%);
  z-index:-1; border-radius:50%;
}

/* ══════════════════════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
  background: rgba(2,6,18,0.95) !important;
  backdrop-filter: blur(28px) !important;
  -webkit-backdrop-filter: blur(28px) !important;
  border-right: 1px solid rgba(8,145,178,0.14) !important;
  box-shadow: 6px 0 40px rgba(0,0,0,0.55) !important;
}
section[data-testid="stSidebar"] > div { padding-top: 12px !important; }
section[data-testid="stSidebar"] hr {
  border-top: 1px dashed rgba(8,145,178,0.35) !important;
  margin: 1.2rem 0 !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  color: #e2e8f0 !important;
  font-family: 'Syne',sans-serif !important;
  font-weight: 700 !important;
}
section[data-testid="stSidebar"] label {
  color: #64748b !important;
  font-family: 'JetBrains Mono',monospace !important;
  font-size: clamp(9px, 1.1vw, 11px) !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  font-weight: 600 !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
  color: #94a3b8 !important;
  font-size: clamp(12px,1.4vw,14px) !important;
}

/* Sidebar number/select inputs */
section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
  background: #dde8f5 !important;
  border-radius: var(--radius-sm) !important;
  border: 1.5px solid #8ba4c8 !important;
  transition: var(--transition);
}
section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {
  border-color: var(--accent-lt) !important;
  box-shadow: 0 0 10px rgba(103,232,249,.7), 0 0 0 1px var(--accent-lt) !important;
}
section[data-testid="stSidebar"] div[data-baseweb="input"] input {
  color: #0f172a !important;
  -webkit-text-fill-color: #0f172a !important;
  font-family: 'JetBrains Mono',monospace !important;
  font-weight: 600 !important;
  font-size: clamp(12px,1.3vw,14px) !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] span {
  color: #0f172a !important;
  font-weight: 700 !important;
}

/* Hide number spinners cross-browser */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button { -webkit-appearance:none; margin:0; }
input[type="number"] { -moz-appearance:textfield; }

/* ── SKY BLUE SLIDERS ── */
section[data-testid="stSidebar"] div[data-testid="stSlider"] [role="slider"] {
  background: #38bdf8 !important;
  border: 2.5px solid #ffffff !important;
  box-shadow: 0 0 14px rgba(56,189,248,.95), 0 0 4px rgba(56,189,248,.5) !important;
  width: clamp(16px,2vw,20px) !important;
  height: clamp(16px,2vw,20px) !important;
  cursor: grab !important;
}
section[data-testid="stSidebar"] div[data-testid="stSlider"] > div > div > div > div {
  background: linear-gradient(90deg,#0ea5e9,#38bdf8) !important;
  height: 4px !important;
  border-radius: 99px !important;
}
section[data-testid="stSidebar"] div[data-testid="stSlider"] > div > div > div {
  background: rgba(56,189,248,0.18) !important;
  height: 4px !important;
  border-radius: 99px !important;
}
div[data-testid="stTickBar"] { display:none !important; }

/* ── PREDICT BUTTON ── */
section[data-testid="stSidebar"] button {
  background: linear-gradient(135deg,#0369a1,#1e3a8a) !important;
  border-radius: var(--radius-md) !important;
  border: 1.5px solid rgba(56,189,248,.45) !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  font-family: 'DM Sans',sans-serif !important;
  font-weight: 700 !important;
  font-size: clamp(13px,1.5vw,15px) !important;
  letter-spacing: 0.05em !important;
  box-shadow: 0 4px 18px rgba(3,105,161,.4) !important;
  transition: var(--transition) !important;
  text-shadow: 0 1px 4px rgba(0,0,0,.55) !important;
  min-height: 44px !important;  /* touch-friendly */
  touch-action: manipulation !important;
}
section[data-testid="stSidebar"] button:hover {
  background: linear-gradient(135deg,#0891b2,#2563eb) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 28px rgba(8,145,178,.5) !important;
  border-color: rgba(103,232,249,.8) !important;
}
section[data-testid="stSidebar"] button:active { transform:scale(0.96) !important; }

/* Logout button */
section[data-testid="stSidebar"] button:last-of-type {
  background: rgba(30,41,59,0.92) !important;
  border: 1.5px solid rgba(100,116,139,.45) !important;
  color: #cbd5e1 !important;
  -webkit-text-fill-color: #cbd5e1 !important;
  box-shadow: 0 2px 10px rgba(0,0,0,.3) !important;
  text-shadow: none !important;
}
section[data-testid="stSidebar"] button:last-of-type:hover {
  background: rgba(51,65,85,0.95) !important;
  border-color: rgba(148,163,184,.6) !important;
  color: #f1f5f9 !important;
  -webkit-text-fill-color: #f1f5f9 !important;
}

/* Download button */
div.stDownloadButton > button {
  background: linear-gradient(135deg,#059669,#047857) !important;
  width: 100% !important;
  font-size: clamp(13px,1.5vw,15px) !important;
  color: white !important;
  -webkit-text-fill-color: white !important;
  border-radius: var(--radius-md) !important;
  border: none !important;
  font-family: 'DM Sans',sans-serif !important;
  font-weight: 700 !important;
  padding: 12px 20px !important;
  min-height: 48px !important;
  box-shadow: 0 4px 18px rgba(5,150,105,.35) !important;
  transition: var(--transition) !important;
  touch-action: manipulation !important;
}
div.stDownloadButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 28px rgba(5,150,105,.5) !important;
}

/* Dropdown popup */
div[data-baseweb="popover"] {
  background: #0f172a !important;
  border: 1px solid rgba(8,145,178,.22);
  border-radius: var(--radius-md);
}
ul[role="listbox"] { background: #0f172a !important; }
li[role="option"] { background:transparent !important; color:#94a3b8 !important; font-weight:600 !important; min-height:40px !important; }
li[role="option"]:hover { background:rgba(8,145,178,.12) !important; color:#67e8f9 !important; }

/* Metric cards */
div[data-testid="metric-container"] {
  background: rgba(8,145,178,.08) !important;
  border: 1px solid rgba(8,145,178,.22) !important;
  border-radius: var(--radius-md) !important;
  padding: clamp(12px,1.8vw,18px) !important;
}
@keyframes countUp { from{opacity:0;transform:scale(0.8)} to{opacity:1;transform:scale(1)} }
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-family: 'Syne',sans-serif !important;
  font-size: clamp(1.4rem,3vw,2rem) !important;
  color: #67e8f9 !important;
  animation: countUp 0.7s ease;
}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
  font-family: 'JetBrains Mono',monospace !important;
  font-size: clamp(9px,1vw,11px) !important;
  letter-spacing: 0.10em !important;
  text-transform: uppercase !important;
  color: #64748b !important;
}

/* Alerts */
div[data-testid="stSuccess"],div[data-testid="stWarning"],div[data-testid="stError"] {
  border-radius: var(--radius-md) !important;
}
div[data-testid="stSuccess"] { background:rgba(4,120,87,.10) !important; border:1px solid rgba(4,120,87,.38) !important; }
div[data-testid="stSuccess"] p { color:#6ee7b7 !important; font-weight:600; }
div[data-testid="stWarning"] { background:rgba(180,83,9,.10) !important; border:1px solid rgba(180,83,9,.38) !important; }
div[data-testid="stWarning"] p { color:#fcd34d !important; font-weight:600; }
div[data-testid="stError"]   { background:rgba(185,28,28,.10) !important; border:1px solid rgba(185,28,28,.38) !important; }
div[data-testid="stError"] p { color:#fca5a5 !important; font-weight:600; }

/* HR */
hr { border-color:rgba(8,145,178,.18) !important; margin:2rem 0 !important; }

/* Charts */
div[data-testid="stPlotlyChart"] { transition:transform .3s ease,filter .3s ease; }
div[data-testid="stPlotlyChart"]:hover { transform:scale(1.015); filter:drop-shadow(0 8px 18px rgba(8,145,178,.15)); z-index:10; }

/* ══════════════════════════════════════════════════════════
   RESPONSIVE BREAKPOINTS
   ══════════════════════════════════════════════════════════ */

/* Tablet (≤1024px) */
@media screen and (max-width:1024px) {
  section[data-testid="stSidebar"] { min-width: 240px !important; }
  .glass-box,.gradient-result { padding: 20px !important; }
  div[data-testid="metric-container"] [data-testid="stMetricValue"] { font-size:1.5rem !important; }
}

/* Mobile (≤768px) — stack layout, bigger touch targets */
@media screen and (max-width:768px) {
  .glass-box,.gradient-result { padding: 16px !important; border-radius: 14px !important; }
  div[data-testid="metric-container"] [data-testid="stMetricValue"] { font-size:1.3rem !important; }
  div[data-testid="metric-container"] { padding:10px !important; }
  section[data-testid="stSidebar"] button { min-height:50px !important; font-size:15px !important; }
  /* make charts full width */
  div[data-testid="stPlotlyChart"] { width:100% !important; }
  /* Plotly chart hover disabled on touch to avoid jitter */
  div[data-testid="stPlotlyChart"]:hover { transform:none !important; }
}

/* Small phones (≤480px) */
@media screen and (max-width:480px) {
  h1 { font-size:clamp(1.4rem,6vw,2rem) !important; }
  h2 { font-size:clamp(1.1rem,5vw,1.5rem) !important; }
  .glass-box { padding:12px !important; border-radius:12px !important; }
}

/* Touch devices — increase hit area */
@media (hover:none) and (pointer:coarse) {
  section[data-testid="stSidebar"] button,
  div.stDownloadButton > button { min-height:52px !important; }
  div[data-baseweb="slider"] [role="slider"] { width:26px !important; height:26px !important; }
  li[role="option"] { padding: 12px 16px !important; }
}

/* High DPI (Retina) — sharper rendering */
@media (-webkit-min-device-pixel-ratio:2),(min-resolution:192dpi) {
  .glass-box { backdrop-filter:blur(24px) !important; }
}

/* Safe area insets for iPhone notch / Android cutout */
@supports (padding: env(safe-area-inset-bottom)) {
  section[data-testid="stSidebar"] > div {
    padding-bottom: env(safe-area-inset-bottom) !important;
  }
}

/* Landscape phones */
@media screen and (max-height:500px) and (orientation:landscape) {
  .glass-box { margin-bottom:12px !important; }
}

/* Print (in case someone prints the webpage) */
@media print {
  section[data-testid="stSidebar"] { display:none !important; }
  .stApp { background:white !important; }
  .glass-box { box-shadow:none !important; border:1px solid #e2e8f0 !important; }
}
"""


# ============================================================
# REGISTRATION PAGE
# ============================================================
def registration_page():
    img = get_b64("health.png")
    st.markdown(f"""
<style>
{COMMON_FONTS}
.stApp {{
  background: linear-gradient(rgba(2,6,18,.74),rgba(2,6,18,.74)),
              url("data:image/jpg;base64,{img}") center/cover fixed;
  font-family:'DM Sans',sans-serif;
}}
#MainMenu,footer,header,.stDeployButton {{ display:none !important; }}
{RESPONSIVE_CSS}

/* Registration form card */
div[data-testid="stForm"] {{
  background:rgba(8,15,36,.84) !important;
  backdrop-filter:blur(28px) saturate(1.4);
  -webkit-backdrop-filter:blur(28px);
  border-radius: var(--radius-lg) !important;
  padding: clamp(24px,4vw,48px) clamp(18px,4vw,44px) !important;
  width:100%;
  max-width: min(700px, 96vw);
  margin: 4vh auto;
  border:1px solid rgba(103,232,249,.18) !important;
  box-shadow: var(--shadow-lg), 0 0 0 1px rgba(255,255,255,.04);
  position:relative; overflow:hidden;
}}
div[data-testid="stForm"]::before {{
  content:''; position:absolute; top:0; left:20%; right:20%; height:1px;
  background:linear-gradient(90deg,transparent,rgba(103,232,249,.6),transparent);
}}
div[data-testid="stForm"] label {{
  color:#94a3b8 !important;
  font-family:'JetBrains Mono',monospace !important;
  font-size:clamp(9px,1vw,11px) !important;
  font-weight:600 !important;
  letter-spacing:0.13em !important;
  text-transform:uppercase !important;
}}
div[data-testid="stForm"] div[data-baseweb="input"] > div,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div,
div[data-testid="stForm"] div[data-baseweb="select"] > div {{
  background:rgba(255,255,255,.07) !important;
  border-radius:var(--radius-md) !important;
  border:1px solid rgba(255,255,255,.11) !important;
  transition:var(--transition);
  min-height:44px;
}}
div[data-testid="stForm"] div[data-baseweb="input"] > div:focus-within,
div[data-testid="stForm"] div[data-baseweb="textarea"] > div:focus-within,
div[data-testid="stForm"] div[data-baseweb="select"] > div:focus-within {{
  border:1px solid rgba(103,232,249,.85) !important;
  box-shadow:0 0 12px rgba(103,232,249,.4),0 0 0 1px #67e8f9 !important;
  background:rgba(255,255,255,.10) !important;
}}
div[data-testid="stForm"] input,
div[data-testid="stForm"] textarea {{
  color:#e2e8f0 !important;
  -webkit-text-fill-color:#e2e8f0 !important;
  font-family:'DM Sans',sans-serif !important;
  font-size:clamp(13px,1.5vw,15px) !important;
  font-weight:500 !important;
}}
div[data-testid="stForm"] input::placeholder,
div[data-testid="stForm"] textarea::placeholder {{ color:#475569 !important; }}
div[data-testid="stForm"] div[data-baseweb="select"] span {{ color:#e2e8f0 !important; }}
div[data-testid="stForm"] button {{
  background:linear-gradient(135deg,#0891b2,#1d4ed8) !important;
  color:white !important;
  -webkit-text-fill-color:white !important;
  border-radius:var(--radius-md) !important;
  min-height:52px !important;
  font-family:'DM Sans',sans-serif !important;
  font-size:clamp(13px,1.5vw,16px) !important;
  font-weight:700 !important;
  letter-spacing:.05em !important;
  border:none !important;
  box-shadow:0 4px 24px rgba(8,145,178,.35) !important;
  transition:var(--transition) !important;
  touch-action:manipulation !important;
}}
div[data-testid="stForm"] button:hover {{
  transform:translateY(-2px) !important;
  box-shadow:0 8px 32px rgba(8,145,178,.5) !important;
}}
div[data-testid="stForm"] button:active {{ transform:scale(0.97) !important; }}
h1 {{
  background:linear-gradient(110deg,#fff 20%,#67e8f9 60%,#818cf8 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  background-clip:text;
  font-size:clamp(1.8rem,5vw,3rem) !important;
  text-align:center; margin-bottom:6px;
}}
.stMarkdown p {{ color:#94a3b8 !important; text-align:center; }}
div[data-testid="stSuccess"] {{background:rgba(4,120,87,.13)!important;border:1px solid rgba(4,120,87,.4)!important;border-radius:var(--radius-md)!important;}}
div[data-testid="stSuccess"] p {{color:#6ee7b7!important;font-weight:600;}}
div[data-testid="stError"] {{background:rgba(185,28,28,.13)!important;border:1px solid rgba(185,28,28,.4)!important;border-radius:var(--radius-md)!important;}}
div[data-testid="stError"] p {{color:#fca5a5!important;font-weight:600;}}
div[data-baseweb="popover"] {{background:#0f172a!important;border:1px solid rgba(103,232,249,.18);border-radius:var(--radius-md);}}
ul[role="listbox"] {{background:#0f172a!important;}}
li[role="option"] {{color:#94a3b8!important;}}
li[role="option"]:hover {{background:rgba(103,232,249,.10)!important;color:#67e8f9!important;}}
</style>
""", unsafe_allow_html=True)

    st.title("📝 Patient Registration")
    st.markdown("Register to access the AI Diabetes Prediction System")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("reg_form"):
            name             = st.text_input("Full Name")
            country_list     = [c.name for c in pycountry.countries]
            selected_country = st.selectbox("🌍 Country", country_list)
            country_obj      = pycountry.countries.get(name=selected_country)
            phone            = st.text_input("Phone Number (without country code)")
            email            = st.text_input("Email Address")
            address          = st.text_area("Address")
            submit           = st.form_submit_button("🚀 Register & Continue")

            if submit:
                name=name.strip(); phone=phone.strip()
                email=email.strip(); address=address.strip()
                if not all([name,phone,email,address]):
                    st.error("❌ Please fill all fields"); return
                if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                    st.error("❌ Invalid email address"); return
                try:
                    parsed = phonenumbers.parse(phone, country_obj.alpha_2)
                    if not phonenumbers.is_valid_number(parsed):
                        st.error("❌ Invalid phone number"); return
                    fmt_phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                except Exception:
                    st.error("❌ Invalid phone format"); return
                ist = pytz.timezone("Asia/Kolkata")
                now = datetime.now(ist)
                pid = "PAT" + str(uuid.uuid4().int)[:6]
                user_data = {"_id":pid,"name":name,"phone":fmt_phone,
                             "country":selected_country,"email":email,"address":address,
                             "gender":"Not Selected",
                             "created_at":now.strftime("%d-%m-%Y %I:%M:%S %p IST")}
                users_collection.insert_one(user_data)
                st.session_state.patient_info = user_data
                st.session_state.registered   = True
                st.session_state.show_success = True
                st.rerun()


# ============================================================
# PREDICTION PAGE
# ============================================================
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

    img = get_b64("health22.png")

    st.markdown(f"""
<style>
{COMMON_FONTS}
.stApp {{
  background: linear-gradient(rgba(2,6,18,.80),rgba(2,6,18,.80)),
              url("data:image/png;base64,{img}") center/cover fixed;
  font-family:'DM Sans',sans-serif;
}}
#MainMenu,footer,header,.stDeployButton {{ display:none !important; }}
{RESPONSIVE_CSS}
</style>
""", unsafe_allow_html=True)

    # ── SIDEBAR ──────────────────────────────────────────────
    info = st.session_state.patient_info
    st.sidebar.markdown("# 🏥 Patient Profile")
    st.sidebar.markdown(f"**👤 Name:** {info.get('name','')}")
    st.sidebar.markdown(f"**📞 Phone:** {info.get('phone','')}")
    st.sidebar.markdown(f"**✉️ Email:** {info.get('email','')}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔬 Clinical Inputs")

    age    = st.sidebar.number_input("Age (years)", 21, 100, 30)
    gender = st.sidebar.selectbox("Gender", ["Male", "Female"])
    if gender == "Female":
        pregnancies = st.sidebar.number_input("Pregnancies", 0, 20, 0)
    else:
        pregnancies = 0

    glucose = st.sidebar.slider("Glucose (mg/dL)",        0, 200, 120)
    bp      = st.sidebar.slider("Blood Pressure (mmHg)",  0, 130,  70)
    skin    = st.sidebar.slider("Skin Thickness (mm)",     0, 100,  20)
    insulin = st.sidebar.slider("Insulin (µIU/mL)",        0, 900,  80)
    bmi     = st.sidebar.number_input("BMI (kg/m²)",      10.0, 70.0, 25.0)
    dpf     = st.sidebar.slider("Diabetes Pedigree Function", 0.0, 2.5, 0.5)

    st.sidebar.markdown("---")
    predict_btn = st.sidebar.button("🔍 Predict Risk", use_container_width=True)
    logout_btn  = st.sidebar.button("← Logout",        use_container_width=True)

    if logout_btn:
        for k in ["registered","patient_info","show_success"]:
            st.session_state[k] = False if k=="registered" else ({} if k=="patient_info" else False)
        st.rerun()

    # ── MAIN ─────────────────────────────────────────────────
    st.title("🩺 Diabetes Prediction System")
    st.markdown("AI-Powered Clinical Risk Assessment Tool")

    if st.session_state.show_success:
        st.success("✅ Registration successful! Fill in clinical inputs and press Predict.")
        st.session_state.show_success = False

    st.markdown("""
    <div class="glass-box">
      <h3 style="margin-top:0;">📋 About This System</h3>
      <p>This AI-powered system uses a trained <strong>Support Vector Machine (SVM)</strong> model to estimate
      diabetes risk from clinical parameters including glucose level, BMI, blood pressure, age, insulin levels,
      skin thickness, diabetes pedigree function, and pregnancy history.
      Results are provided as a downloadable multi-page professional medical PDF report.</p>
    </div>
    """, unsafe_allow_html=True)

    if predict_btn:
        with st.spinner("🧠 Analysing clinical data..."):
            time.sleep(0.7)
            if "_id" in info:
                users_collection.update_one({"_id":info["_id"]},{"$set":{"gender":gender}})

            inp     = np.array([[pregnancies,glucose,bp,skin,insulin,bmi,dpf,age]])
            inp_std = scaler.transform(inp)
            prob    = model.predict_proba(inp_std)[0]
            prob_neg, prob_pos = prob[0]*100, prob[1]*100

            if prob_pos < 30:   risk_label = "Low Risk"
            elif prob_pos < 70: risk_label = "Moderate Risk"
            else:               risk_label = "High Risk"

            ist  = pytz.timezone("Asia/Kolkata")
            now  = datetime.now(ist)
            predictions_collection.insert_one({
                "patient_id":info["_id"],"patient_name":info["name"],
                "age":age,"gender":gender,"glucose":glucose,"blood_pressure":bp,
                "bmi":bmi,"prediction":risk_label,"probability":round(prob_pos,2),
                "created_at":now.strftime("%d-%m-%Y %H:%M:%S IST")
            })

            # ── cause labels/values for charts ───────────────
            cause_labels, cause_values = [], []
            if glucose >= 126: cause_labels.append("High Glucose");       cause_values.append(min(glucose/2,100))
            if bmi > 30:       cause_labels.append("High BMI");           cause_values.append(min(bmi*2,100))
            if age > 45:       cause_labels.append("Age Factor");         cause_values.append(min(age,100))
            if bp > 120:       cause_labels.append("High BP");            cause_values.append(min(bp,100))
            if dpf > 0.5:      cause_labels.append("Genetic Risk (DPF)"); cause_values.append(min(dpf*100,100))
            if not cause_labels:
                cause_labels = ["Healthy Indicators"]; cause_values = [100]

            # ── risk / positive factors ───────────────────────
            risk_factors, positive_factors = [], []
            if glucose>=126:         risk_factors.append("High Glucose Level (≥126 mg/dL)")
            elif 100<=glucose<126:   risk_factors.append("Prediabetic Glucose Level (100–125 mg/dL)")
            else:                    positive_factors.append("Normal Glucose Level (<100 mg/dL)")
            if bmi>30:               risk_factors.append("High BMI — Obesity (>30 kg/m²)")
            elif 18.5<=bmi<=24.9:    positive_factors.append("Healthy BMI (18.5–24.9 kg/m²)")
            if age>45:               risk_factors.append("Age above 45 years")
            if bp>120:               risk_factors.append("High Blood Pressure (>120 mmHg)")
            elif 90<=bp<=120:        positive_factors.append("Normal Blood Pressure (90–120 mmHg)")
            if dpf>0.5:              risk_factors.append("Elevated Genetic Risk (DPF > 0.5)")

            # ── recommendations ───────────────────────────────
            if prob_pos >= 70:
                recs = ["Consult a healthcare professional immediately",
                        "Get complete diabetes / HbA1c screening",
                        "Monitor blood sugar levels daily",
                        "Adopt a low-glycaemic diet plan",
                        "Increase physical activity to ≥150 min/week",
                        "Consider medication as advised by doctor"]
            elif prob_pos >= 30:
                recs = ["Schedule a diabetes screening test",
                        "Maintain a balanced, low-sugar diet",
                        "Exercise regularly — 30 min/day minimum",
                        "Monitor glucose levels every 3 months",
                        "Reduce BMI if above healthy range"]
            else:
                recs = ["Continue healthy lifestyle habits",
                        "Exercise regularly — 30 min/day",
                        "Maintain healthy diet and hydration",
                        "Annual routine health check-ups",
                        "Monitor weight and blood pressure"]

            # ── RESULTS UI ────────────────────────────────────
            st.markdown("---")
            st.header("📊 Prediction Results")

            st.markdown('<div class="gradient-result">', unsafe_allow_html=True)
            r1, r2 = st.columns([2,1])
            with r1:
                if prob_pos < 30:   st.success(f"✅ LOW RISK — {risk_label}")
                elif prob_pos < 70: st.warning(f"⚠️ MODERATE RISK — {risk_label}")
                else:               st.error(f"❌ HIGH RISK — {risk_label}")
                st.subheader("Probability Breakdown")
                m1, m2 = st.columns(2)
                m1.metric("Non-Diabetic", f"{prob_neg:.1f}%")
                m2.metric("Diabetic",     f"{prob_pos:.1f}%")
            with r2:
                gc = "#22c55e" if prob_pos<30 else "#f59e0b" if prob_pos<70 else "#ef4444"
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=prob_pos,
                    number={"suffix":"%","font":{"color":"white","size":28,"family":"DM Sans"}},
                    title={"text":"Risk Level","font":{"color":"#94a3b8","size":13}},
                    gauge={"axis":{"range":[0,100],"tickcolor":"rgba(255,255,255,.2)","tickwidth":1},
                           "bar":{"color":gc,"thickness":0.22},
                           "bgcolor":"rgba(0,0,0,0)","borderwidth":0,
                           "steps":[{"range":[0,30],"color":"rgba(34,197,94,.14)"},
                                    {"range":[30,70],"color":"rgba(245,158,11,.14)"},
                                    {"range":[70,100],"color":"rgba(239,68,68,.14)"}],
                           "threshold":{"line":{"color":gc,"width":3},"thickness":0.8,"value":prob_pos}}))
                fig_g.update_layout(paper_bgcolor="rgba(0,0,0,0)",font=dict(color="white"),
                                    height=250,margin=dict(l=16,r=16,t=24,b=8))
                st.plotly_chart(fig_g, use_container_width=True, config={"responsive":True,"displayModeBar":False})
            st.markdown('</div>', unsafe_allow_html=True)

            # Risk Factors
            st.markdown("---"); st.subheader("⚠️ Risk Factor Analysis")
            if risk_factors:
                st.warning("**Identified Risk Factors:**")
                for f in risk_factors: st.markdown(f"- 🔴 {f}")
            if positive_factors:
                st.success("**Positive Health Indicators:**")
                for f in positive_factors: st.markdown(f"- 🟢 {f}")

            # Recommendations
            st.markdown("---"); st.subheader("💊 Medical Recommendations")
            if prob_pos>=70:   st.error("\n".join(f"- {r}" for r in recs))
            elif prob_pos>=30: st.warning("\n".join(f"- {r}" for r in recs))
            else:              st.success("\n".join(f"- {r}" for r in recs))

            # Charts
            st.markdown('<div class="glass-box">', unsafe_allow_html=True)
            st.subheader("📊 Risk Contribution Analysis")
            scr = ["#dc2626","#d97706","#2563eb","#7c3aed","#047857","#0891b2"]
            bar_col = [scr[i%len(scr)] for i in range(len(cause_labels))]
            ch1, ch2 = st.columns(2)
            bar_f = go.Figure(go.Bar(
                x=cause_labels, y=cause_values,
                text=[f"{v:.1f}" for v in cause_values], textposition="auto",
                marker=dict(color=bar_col,line=dict(color="rgba(255,255,255,.15)",width=1.5)),
                textfont=dict(color="white",size=13,family="DM Sans")))
            bar_f.update_layout(title="Risk Factor Severity",xaxis_title="Risk Factors",yaxis_title="Severity (0-100)",
                                 paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                 font=dict(color="#94a3b8",family="DM Sans"),
                                 autosize=True,margin=dict(l=20,r=20,t=50,b=20))
            bar_f.update_xaxes(showline=True,linecolor="rgba(255,255,255,.12)")
            bar_f.update_yaxes(showgrid=True,gridcolor="rgba(255,255,255,.07)")
            with ch1: st.plotly_chart(bar_f, use_container_width=True, config={"responsive":True,"displayModeBar":False})

            pie_f = go.Figure(go.Pie(
                labels=cause_labels,values=cause_values,hole=0.45,
                marker=dict(colors=bar_col,line=dict(color="rgba(0,0,0,.35)",width=2)),
                textfont=dict(color="white",size=12,family="DM Sans")))
            pie_f.update_layout(title="Percentage Contribution",
                                  paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#94a3b8",family="DM Sans"),
                                  autosize=True,margin=dict(l=20,r=20,t=50,b=20))
            with ch2: st.plotly_chart(pie_f, use_container_width=True, config={"responsive":True,"displayModeBar":False})
            st.markdown("</div>", unsafe_allow_html=True)

            # ── PDF ───────────────────────────────────────────
            pdf_bytes = build_hospital_pdf(
                info=info, age=age, gender=gender, glucose=glucose, bp=bp,
                skin=skin, insulin=insulin, bmi=bmi, dpf=dpf,
                pregnancies=pregnancies, prob_positive=prob_pos,
                risk_label=risk_label, current_time=now,
                cause_labels=cause_labels, cause_values=cause_values,
                recs_for_pdf=recs, risk_factors=risk_factors,
                positive_factors=positive_factors)

            st.markdown("---")
            st.download_button(
                label="📄 Download Professional Medical Report (3-Page PDF)",
                data=pdf_bytes,
                file_name=f"DiabetesReport_{info.get('name','Patient').replace(' ','_')}.pdf",
                mime="application/pdf")

            st.markdown("---")
            st.warning("⚠️ **Medical Disclaimer:** This AI tool does NOT replace professional medical advice. "
                       "Consult a qualified healthcare professional for diagnosis and treatment.")


# ============================================================
# NAVIGATION
# ============================================================
if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
