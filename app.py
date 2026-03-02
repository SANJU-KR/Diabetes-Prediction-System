# ================================================================
# DIABETES PREDICTION SYSTEM — Complete Professional Rebuild
# Clean PDF (1-2 pages) · Creative Matplotlib Backgrounds
# Fully Responsive All OS/Screens · White+Blue Sliders
# ================================================================
import streamlit as st
import numpy as np
import joblib
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import base64, re, time
import pycountry, phonenumbers

from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import mm
from io import BytesIO
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import uuid, pytz

# ── MongoDB ──────────────────────────────────────────────────────
uri = ("mongodb+srv://diabetes_user:Diabetes%40123@"
       "diabetescluster.oxegep6.mongodb.net/"
       "?retryWrites=true&w=majority")
client    = MongoClient(uri, server_api=ServerApi("1"))
db        = client["diabetes_app"]
users_col = db["registered_users"]
preds_col = db["predictions"]

st.set_page_config(page_title="Diabetes Prediction System",
                   page_icon="🩺", layout="wide")

for k, v in [("registered", False), ("patient_info", {}), ("show_success", False)]:
    if k not in st.session_state:
        st.session_state[k] = v


# ════════════════════════════════════════════════════════════════
# BACKGROUND IMAGE GENERATORS (matplotlib → base64 PNG)
# ════════════════════════════════════════════════════════════════
def _fig_b64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=72, bbox_inches="tight", pad_inches=0)
    plt.close(fig); buf.seek(0)
    return base64.b64encode(buf.read()).decode()

@st.cache_data
def reg_background():
    """Registration page: deep-space DNA + ECG + glow orbs + hex grid"""
    rng = np.random.default_rng(42)
    fig, ax = plt.subplots(figsize=(22, 13))
    fig.patch.set_facecolor("#02081a")
    ax.set_facecolor("#02081a"); ax.set_xlim(0, 22); ax.set_ylim(0, 13); ax.axis("off")

    # ─ glowing radial blobs ─
    for cx, cy, r, col, al in [
        (18, 10, 6.5,"#0e7490", .13), (2,  3,  5.0,"#7c3aed", .11),
        (11, 12, 5.5,"#0891b2", .09), (0,  8,  4.0,"#6366f1", .10),
        (20,  1, 4.0,"#0d9488", .11), (8,  5,  8.0,"#0284c7", .06)]:
        ax.add_patch(plt.Circle((cx, cy), r, color=col, alpha=al))

    # ─ DNA double helix (left) ─
    t  = np.linspace(0, 6*np.pi, 500)
    xh = np.linspace(0.3, 7, 500)
    y1 = 6.5 + 2.4*np.sin(t); y2 = 6.5 - 2.4*np.sin(t)
    ax.plot(xh, y1, color="#38bdf8", alpha=.32, lw=2.2, ls="--")
    ax.plot(xh, y2, color="#a78bfa", alpha=.32, lw=2.2, ls="--")
    for i in range(0, 500, 28):
        ax.plot([xh[i], xh[i]], [y1[i], y2[i]], color="#67e8f9", alpha=.24, lw=1.3)
    ax.scatter(xh[::28], y1[::28], s=24, color="#67e8f9", alpha=.55, zorder=3)
    ax.scatter(xh[::28], y2[::28], s=24, color="#c4b5fd", alpha=.55, zorder=3)

    # ─ small DNA (right corner) ─
    t2 = np.linspace(0, 4*np.pi, 280)
    xh2 = np.linspace(15, 21.5, 280)
    y1b = 10 + 1.4*np.sin(t2); y2b = 10 - 1.4*np.sin(t2)
    ax.plot(xh2, y1b, color="#0ea5e9", alpha=.20, lw=1.6, ls="--")
    ax.plot(xh2, y2b, color="#818cf8", alpha=.20, lw=1.6, ls="--")
    for i in range(0, 280, 32):
        ax.plot([xh2[i], xh2[i]], [y1b[i], y2b[i]], color="#7dd3fc", alpha=.18, lw=1)

    # ─ ECG heartbeat strip ─
    ex = np.linspace(6, 21.5, 720); ey = np.ones(720)*2.2
    for s in range(0, 720, 144):
        seg = slice(s, min(s+144, 720))
        xs  = np.linspace(0, 1, min(144, 720-s))
        beat = (np.exp(-((xs-.30)**2)/.005)*3.0
               -np.exp(-((xs-.50)**2)/.0028)*2.2
               +np.exp(-((xs-.68)**2)/.005)*1.1)
        ey[seg] += beat[:len(ey[seg])]
    ax.plot(ex, ey, color="#22d3ee", alpha=.30, lw=2.2)

    # ─ medical cross symbols ─
    for px, py, fs, al in [(14, 10, 110, .06), (2, 0.5, 80, .07), (20, 5, 65, .06)]:
        ax.text(px, py, "+", fontsize=fs, color="#0891b2", alpha=al,
                ha="center", va="center", fontweight="bold")

    # ─ dot grid ─
    for xi in np.arange(.7, 22, 1.4):
        for yi in np.arange(.7, 13, 1.4):
            ax.plot(xi, yi, ".", color="#1e3a5f", ms=2.5, alpha=.45)

    # ─ hex grid overlay ─
    for hx in np.arange(8, 16, 2.4):
        for hy in np.arange(8.5, 13, 1.8):
            pts = [(hx + .55*np.cos(np.pi/3*k), hy + .55*np.sin(np.pi/3*k)) for k in range(6)]
            ax.add_patch(plt.Polygon(pts, fill=False, edgecolor="#164e63", lw=.65, alpha=.38))

    # ─ floating particles ─
    px = rng.uniform(0, 22, 90); py = rng.uniform(0, 13, 90)
    ps = rng.uniform(5, 22, 90); pa = rng.uniform(.04, .22, 90)
    ax.scatter(px, py, s=ps, color="#38bdf8", alpha=pa, zorder=2)

    plt.tight_layout(pad=0)
    return _fig_b64(fig)


@st.cache_data
def pred_background():
    """Prediction page: circuit board + scan rings + ECG + nodes"""
    rng = np.random.default_rng(7)
    fig, ax = plt.subplots(figsize=(22, 13))
    fig.patch.set_facecolor("#050e1f")
    ax.set_facecolor("#050e1f"); ax.set_xlim(0, 22); ax.set_ylim(0, 13); ax.axis("off")

    # ─ glow orbs ─
    for cx, cy, r, col, al in [
        (11, 6.5, 8.0,"#0e7490", .11), (1, 12, 5,"#4f46e5", .10),
        (21, .5,  6,"#0891b2",   .11), (4,  0,  4.5,"#0d9488", .09),
        (20, 12,  4,"#7c3aed",   .09)]:
        ax.add_patch(plt.Circle((cx, cy), r, color=col, alpha=al))

    # ─ concentric scan rings ─
    for r, al in [(2.8,.26),(4.5,.18),(6.2,.13),(8.0,.08),(10,.04)]:
        ax.add_patch(plt.Circle((11, 6.5), r, fill=False,
                                 edgecolor="#0891b2", lw=1.0, alpha=al, ls="--"))

    # ─ circuit board traces ─
    hl = [(0,2,14,2),(0,5.5,9,5.5),(13,9.5,22,9.5),(0,11,7.5,11),(14.5,3,22,3),(0,7.5,5,7.5)]
    vl = [(6.5,0,6.5,5),(14.5,0,14.5,3.5),(4,7,4,13),(17,9.5,17,13),(9,5.5,9,9),(12,2,12,9.5)]
    for x0,y0,x1,y1 in hl:
        ax.plot([x0,x1],[y0,y1], color="#164e63", lw=1.1, alpha=.55)
    for x0,y0,x1,y1 in vl:
        ax.plot([x0,x1],[y0,y1], color="#155e75", lw=1.1, alpha=.55)

    # ─ circuit nodes ─
    for nx, ny in [(6.5,2),(14.5,2),(6.5,5.5),(9,5.5),(14.5,9.5),(4,9.5),
                    (17,9.5),(9,9),(4,11),(17,3),(12,5.5),(12,9.5)]:
        ax.add_patch(plt.Circle((nx, ny), .24, color="#0ea5e9", alpha=.62))
        ax.add_patch(plt.Circle((nx, ny), .12, color="#e0f2fe", alpha=.78))

    # ─ ECG across middle ─
    ex = np.linspace(0, 22, 950); ey = np.ones(950)*6.5
    for s in range(0, 950, 190):
        seg = slice(s, min(s+190, 950))
        xs  = np.linspace(0, 1, min(190, 950-s))
        beat = (np.exp(-((xs-.25)**2)/.004)*3.4
               -np.exp(-((xs-.45)**2)/.0022)*2.6
               +np.exp(-((xs-.62)**2)/.004)*1.4)
        ey[seg] += beat[:len(ey[seg])]
    ax.plot(ex, ey, color="#22d3ee", alpha=.24, lw=2.0)

    # ─ DNA bottom-left ─
    t = np.linspace(0, 4*np.pi, 240)
    xd = np.linspace(0.3, 6, 240)
    y1d = 3.0 + 1.4*np.sin(t); y2d = 3.0 - 1.4*np.sin(t)
    ax.plot(xd, y1d, color="#38bdf8", alpha=.22, lw=1.6, ls="--")
    ax.plot(xd, y2d, color="#818cf8", alpha=.22, lw=1.6, ls="--")
    for i in range(0, 240, 36):
        ax.plot([xd[i], xd[i]], [y1d[i], y2d[i]], color="#67e8f9", alpha=.18, lw=1)

    # ─ hex accent (top right) ─
    for hx in np.arange(14.5, 22, 1.9):
        for hy in np.arange(.5, 3.5, 1.6):
            pts = [(hx + .5*np.cos(np.pi/3*k), hy + .5*np.sin(np.pi/3*k)) for k in range(6)]
            ax.add_patch(plt.Polygon(pts, fill=False, edgecolor="#155e75", lw=.65, alpha=.40))

    # ─ particles ─
    px = rng.uniform(0, 22, 70); py = rng.uniform(0, 13, 70)
    ps = rng.uniform(6, 28, 70); pa = rng.uniform(.04, .20, 70)
    ax.scatter(px, py, s=ps, color="#38bdf8", alpha=pa, zorder=2)

    plt.tight_layout(pad=0)
    return _fig_b64(fig)


# ════════════════════════════════════════════════════════════════
# PDF COLOUR PALETTE
# ════════════════════════════════════════════════════════════════
P = {
    "navy":    rl_colors.HexColor("#0b1f3a"),
    "teal":    rl_colors.HexColor("#0e7490"),
    "teal2":   rl_colors.HexColor("#0891b2"),
    "ice":     rl_colors.HexColor("#e0f2fe"),
    "icedk":   rl_colors.HexColor("#bae6fd"),
    "white":   rl_colors.white,
    "offwh":   rl_colors.HexColor("#f8fafc"),
    "slate":   rl_colors.HexColor("#334155"),
    "grey":    rl_colors.HexColor("#64748b"),
    "divider": rl_colors.HexColor("#e2e8f0"),
    "row_alt": rl_colors.HexColor("#f1f5f9"),
    "row_nor": rl_colors.HexColor("#f0f9ff"),
    "cyan":    rl_colors.HexColor("#7dd3fc"),
    # risk colours
    "green":   rl_colors.HexColor("#047857"),
    "greenb":  rl_colors.HexColor("#ecfdf5"),
    "greendk": rl_colors.HexColor("#14532d"),
    "amber":   rl_colors.HexColor("#b45309"),
    "amberb":  rl_colors.HexColor("#fef9c3"),
    "amberdk": rl_colors.HexColor("#713f12"),
    "red":     rl_colors.HexColor("#b91c1c"),
    "redb":    rl_colors.HexColor("#fff1f2"),
    "reddk":   rl_colors.HexColor("#7f1d1d"),
}

# ════════════════════════════════════════════════════════════════
# CHART IMAGE GENERATORS FOR PDF (matplotlib → PNG bytes)
# ════════════════════════════════════════════════════════════════
_CHART_COLS = ["#0891b2","#f59e0b","#ef4444","#8b5cf6","#10b981","#f97316"]

def _pdf_bar_chart(labels, values):
    """Horizontal bar chart — clean, white bg, colored bars."""
    n    = len(labels)
    h_in = max(1.6, n * 0.38)
    fig, ax = plt.subplots(figsize=(4.5, h_in), dpi=180)
    fig.patch.set_facecolor("white"); ax.set_facecolor("#f8fafc")
    cols  = [_CHART_COLS[i % len(_CHART_COLS)] for i in range(n)]
    bars  = ax.barh(range(n), values, color=cols, edgecolor="white",
                    linewidth=0.8, height=0.55, zorder=3)
    ax.set_yticks(range(n)); ax.set_yticklabels(labels, fontsize=8, color="#334155")
    ax.set_xlim(0, max(values) * 1.3 if values else 110)
    ax.set_xlabel("Severity Level (0–100)", fontsize=7.5, color="#64748b", labelpad=4)
    ax.set_title("Risk Factor Severity", fontsize=9.5, fontweight="bold",
                 color="#0b1f3a", pad=6, loc="left")
    for bar, val in zip(bars, values):
        ax.text(val + max(values)*0.02, bar.get_y()+bar.get_height()/2,
                f"{val:.0f}", va="center", fontsize=7.5, fontweight="bold",
                color="#334155")
    ax.tick_params(axis="x", labelsize=7.5, colors="#94a3b8")
    ax.tick_params(axis="y", length=0)
    ax.spines[["top","right","left"]].set_visible(False)
    ax.spines["bottom"].set_color("#e2e8f0")
    ax.xaxis.grid(True, color="#e2e8f0", lw=0.5, ls="--", zorder=0)
    ax.set_axisbelow(True)
    ax.invert_yaxis()
    plt.tight_layout(pad=0.5)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig); buf.seek(0); return buf


def _pdf_pie_chart(labels, values):
    """Donut pie chart — clean, white bg, legend below."""
    fig, ax = plt.subplots(figsize=(3.8, 3.4), dpi=180)
    fig.patch.set_facecolor("white")
    cols   = [_CHART_COLS[i % len(_CHART_COLS)] for i in range(len(labels))]
    wedges, texts, autos = ax.pie(
        values, labels=None, colors=cols,
        autopct="%1.0f%%", startangle=140,
        wedgeprops=dict(width=0.55, edgecolor="white", linewidth=1.5),
        pctdistance=0.78, textprops={"fontsize": 7.5})
    for at in autos:
        at.set_fontweight("bold"); at.set_color("white"); at.set_fontsize(7.5)
    ax.set_title("Risk Contribution", fontsize=9.5, fontweight="bold",
                 color="#0b1f3a", pad=6)
    ax.legend(wedges, labels, loc="lower center",
              bbox_to_anchor=(0.5, -0.12), ncol=2,
              fontsize=7, frameon=False,
              labelcolor="#334155")
    plt.tight_layout(pad=0.4)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig); buf.seek(0); return buf


# ════════════════════════════════════════════════════════════════
# PDF BUILDER — Professional hospital report with charts (1-2 pages)
# ════════════════════════════════════════════════════════════════
def build_pdf(info, age, gender, glucose, bp, skin, insulin, bmi, dpf,
              pregnancies, prob_pos, risk_label, now, recs, risk_fs, pos_fs,
              cause_labels=None, cause_values=None):




# ════════════════════════════════════════════════════════════════
# SHARED CSS (responsive all screens / OS / devices)
# ════════════════════════════════════════════════════════════════
FONTS = ("@import url('https://fonts.googleapis.com/css2?family=Inter:"
         "wght@300;400;500;600;700&family=Syne:wght@700;800&"
         "family=JetBrains+Mono:wght@400;600&display=swap');")

def responsive_css(bg_b64, overlay="rgba(2,8,23,.72)"):
    return f"""
<style>
{FONTS}
/* ── Base reset (cross-browser/OS) ── */
*,*::before,*::after{{box-sizing:border-box;}}
html{{scroll-behavior:smooth;-webkit-text-size-adjust:100%;text-size-adjust:100%;}}
body{{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;}}
::-webkit-scrollbar{{width:4px;height:4px;}}
::-webkit-scrollbar-thumb{{background:rgba(14,116,144,.4);border-radius:99px;}}

/* ── CSS variables ── */
:root{{
  --teal:#0e7490;--teal2:#0891b2;--sky:#38bdf8;--navy:#0b1f3a;
  --r-lg:20px;--r-md:12px;--r-sm:8px;
  --sh:0 8px 32px rgba(0,0,0,.4);
  --tr:all .22s cubic-bezier(.4,0,.2,1);
}}

/* ── Background ── */
.stApp{{
  background:url("data:image/png;base64,{bg_b64}") center/cover fixed!important;
  font-family:'Inter',sans-serif!important;
}}
.stApp::before{{
  content:"";position:fixed;inset:0;
  background:{overlay};z-index:0;pointer-events:none;
}}

/* ── Typography ── */
h1,h2,h3,h4{{color:#fff!important;font-family:'Syne',sans-serif!important;letter-spacing:-.02em;}}
p,li{{color:#e2e8f0!important;}}
ul{{line-height:1.9;}}

/* ── Entry animation ── */
@keyframes fadeUp{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
.stApp>header+div{{animation:fadeUp .5s ease-out;}}

/* ── Glass card ── */
.glass{{
  background:rgba(255,255,255,.05);
  backdrop-filter:blur(20px) saturate(1.3);
  -webkit-backdrop-filter:blur(20px) saturate(1.3);
  border-radius:var(--r-lg);
  padding:clamp(16px,3vw,32px);
  border:1px solid rgba(255,255,255,.09);
  box-shadow:var(--sh);
  margin-bottom:clamp(14px,2vw,24px);
  transition:var(--tr);
}}
.glass:hover{{transform:translateY(-3px);box-shadow:0 16px 48px rgba(14,116,144,.22);border-color:rgba(56,189,248,.25);}}

/* ── Gradient border result card ── */
.gcard{{position:relative;background:rgba(11,31,58,.85);border-radius:var(--r-lg);padding:clamp(14px,2.5vw,26px);margin-bottom:20px;}}
.gcard::before{{content:"";position:absolute;inset:-2px;background:linear-gradient(135deg,#0891b2,#3b82f6,#8b5cf6);border-radius:calc(var(--r-lg)+2px);z-index:-1;background-size:200% 200%;animation:gb 3s ease infinite;}}
@keyframes gb{{0%,100%{{background-position:0 50%}}50%{{background-position:100% 50%}}}}

/* ══ SIDEBAR ══ */
section[data-testid="stSidebar"]{{
  background:rgba(2,8,23,.96)!important;
  backdrop-filter:blur(28px)!important;-webkit-backdrop-filter:blur(28px)!important;
  border-right:1px solid rgba(14,116,144,.16)!important;
  box-shadow:6px 0 40px rgba(0,0,0,.6)!important;
}}
section[data-testid="stSidebar"]>div{{padding-top:12px!important;}}
section[data-testid="stSidebar"] hr{{border-top:1px dashed rgba(14,116,144,.35)!important;margin:1.1rem 0!important;}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3{{color:#e2e8f0!important;font-family:'Syne',sans-serif!important;font-weight:700!important;}}
section[data-testid="stSidebar"] label{{
  color:#64748b!important;font-family:'JetBrains Mono',monospace!important;
  font-size:clamp(9px,1vw,11px)!important;letter-spacing:.13em!important;
  text-transform:uppercase!important;font-weight:600!important;
}}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"]{{color:#94a3b8!important;font-size:clamp(12px,1.3vw,14px)!important;}}

/* Sidebar inputs */
section[data-testid="stSidebar"] div[data-baseweb="input"]>div,
section[data-testid="stSidebar"] div[data-baseweb="select"]>div{{
  background:#dde8f5!important;border-radius:var(--r-sm)!important;
  border:1.5px solid #8ba4c8!important;transition:var(--tr);min-height:42px;
}}
section[data-testid="stSidebar"] div[data-baseweb="input"]>div:focus-within,
section[data-testid="stSidebar"] div[data-baseweb="select"]>div:focus-within{{
  border-color:var(--sky)!important;
  box-shadow:0 0 10px rgba(56,189,248,.6),0 0 0 1px var(--sky)!important;
}}
section[data-testid="stSidebar"] div[data-baseweb="input"] input{{
  color:#0f172a!important;-webkit-text-fill-color:#0f172a!important;
  font-family:'JetBrains Mono',monospace!important;font-weight:600!important;
  font-size:clamp(12px,1.3vw,14px)!important;
}}
section[data-testid="stSidebar"] div[data-baseweb="select"] span{{color:#0f172a!important;font-weight:700!important;}}
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button{{-webkit-appearance:none;margin:0;}}
input[type="number"]{{-moz-appearance:textfield;}}

/* ══ SLIDERS — Blue filled, WHITE unfilled ══ */
/* Thumb handle */
section[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"]{{
  background:var(--sky)!important;
  border:2.5px solid #ffffff!important;
  box-shadow:0 0 14px rgba(56,189,248,.9),0 0 4px rgba(56,189,248,.4)!important;
  width:clamp(16px,1.8vw,20px)!important;height:clamp(16px,1.8vw,20px)!important;
  cursor:grab!important;touch-action:none!important;
}}
/* Track container base */
section[data-testid="stSidebar"] [data-testid="stSlider"] div[data-baseweb="slider"] > div{{
  height:5px!important;border-radius:99px!important;
  background:#ffffff!important;
}}
/* Filled (selected) portion — sky blue */
section[data-testid="stSidebar"] [data-testid="stSlider"] div[data-baseweb="slider"] > div > div:first-child{{
  background:linear-gradient(90deg,#0ea5e9,#38bdf8)!important;
  height:5px!important;border-radius:99px!important;
}}
/* Hide default tick marks */
div[data-testid="stTickBar"]{{display:none!important;}}

/* ══ BUTTONS ══ */
section[data-testid="stSidebar"] button{{
  background:linear-gradient(135deg,#0369a1,#1e3a8a)!important;
  border-radius:var(--r-md)!important;border:1.5px solid rgba(56,189,248,.4)!important;
  color:#fff!important;-webkit-text-fill-color:#fff!important;
  font-family:'Inter',sans-serif!important;font-weight:700!important;
  font-size:clamp(13px,1.4vw,15px)!important;letter-spacing:.04em!important;
  box-shadow:0 4px 18px rgba(3,105,161,.38)!important;
  transition:var(--tr)!important;min-height:44px!important;
  text-shadow:0 1px 4px rgba(0,0,0,.5)!important;touch-action:manipulation!important;
}}
section[data-testid="stSidebar"] button:hover{{
  background:linear-gradient(135deg,#0891b2,#2563eb)!important;
  transform:translateY(-2px)!important;box-shadow:0 8px 26px rgba(14,116,144,.5)!important;
  border-color:rgba(103,232,249,.8)!important;
}}
section[data-testid="stSidebar"] button:active{{transform:scale(.96)!important;}}
/* Logout */
section[data-testid="stSidebar"] button:last-of-type{{
  background:rgba(30,41,59,.92)!important;border:1.5px solid rgba(100,116,139,.4)!important;
  color:#cbd5e1!important;-webkit-text-fill-color:#cbd5e1!important;
  box-shadow:0 2px 10px rgba(0,0,0,.3)!important;text-shadow:none!important;
}}
section[data-testid="stSidebar"] button:last-of-type:hover{{
  background:rgba(51,65,85,.95)!important;color:#f1f5f9!important;-webkit-text-fill-color:#f1f5f9!important;
}}
/* Download */
div.stDownloadButton>button{{
  background:linear-gradient(135deg,#059669,#047857)!important;width:100%!important;
  color:#fff!important;-webkit-text-fill-color:#fff!important;
  border-radius:var(--r-md)!important;border:none!important;
  font-family:'Inter',sans-serif!important;font-weight:700!important;
  font-size:clamp(13px,1.4vw,16px)!important;padding:12px 20px!important;
  min-height:48px!important;box-shadow:0 4px 18px rgba(5,150,105,.35)!important;
  transition:var(--tr)!important;touch-action:manipulation!important;
}}
div.stDownloadButton>button:hover{{transform:translateY(-2px)!important;box-shadow:0 8px 28px rgba(5,150,105,.5)!important;}}

/* Dropdown */
div[data-baseweb="popover"]{{background:#0f172a!important;border:1px solid rgba(14,116,144,.22);border-radius:var(--r-md);}}
ul[role="listbox"]{{background:#0f172a!important;}}
li[role="option"]{{background:transparent!important;color:#94a3b8!important;font-weight:600!important;min-height:40px!important;}}
li[role="option"]:hover{{background:rgba(14,116,144,.14)!important;color:#67e8f9!important;}}

/* Metrics */
div[data-testid="metric-container"]{{
  background:rgba(14,116,144,.08)!important;border:1px solid rgba(14,116,144,.22)!important;
  border-radius:var(--r-md)!important;padding:clamp(10px,1.6vw,16px)!important;
}}
@keyframes cUp{{from{{opacity:0;transform:scale(.8)}}to{{opacity:1;transform:scale(1)}}}}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{{
  font-family:'Syne',sans-serif!important;font-size:clamp(1.3rem,2.8vw,2rem)!important;
  color:#67e8f9!important;animation:cUp .7s ease;
}}
div[data-testid="metric-container"] [data-testid="stMetricLabel"]{{
  font-family:'JetBrains Mono',monospace!important;font-size:clamp(9px,.9vw,11px)!important;
  letter-spacing:.10em!important;text-transform:uppercase!important;color:#64748b!important;
}}

/* Alerts */
div[data-testid="stSuccess"]{{background:rgba(4,120,87,.10)!important;border:1px solid rgba(4,120,87,.36)!important;border-radius:var(--r-md)!important;}}
div[data-testid="stSuccess"] p{{color:#6ee7b7!important;font-weight:600;}}
div[data-testid="stWarning"]{{background:rgba(180,83,9,.10)!important;border:1px solid rgba(180,83,9,.36)!important;border-radius:var(--r-md)!important;}}
div[data-testid="stWarning"] p{{color:#fcd34d!important;font-weight:600;}}
div[data-testid="stError"]{{background:rgba(185,28,28,.10)!important;border:1px solid rgba(185,28,28,.36)!important;border-radius:var(--r-md)!important;}}
div[data-testid="stError"] p{{color:#fca5a5!important;font-weight:600;}}
hr{{border-color:rgba(14,116,144,.18)!important;margin:2rem 0!important;}}
div[data-testid="stPlotlyChart"]{{transition:transform .3s,filter .3s;}}
div[data-testid="stPlotlyChart"]:hover{{transform:scale(1.012);filter:drop-shadow(0 8px 18px rgba(14,116,144,.15));z-index:10;}}

/* ══ RESPONSIVE BREAKPOINTS ══ */
/* Tablet */
@media screen and (max-width:1024px){{
  section[data-testid="stSidebar"]{{min-width:230px!important;}}
  .glass,.gcard{{padding:18px!important;}}
  div[data-testid="metric-container"] [data-testid="stMetricValue"]{{font-size:1.5rem!important;}}
}}
/* Mobile */
@media screen and (max-width:768px){{
  .glass,.gcard{{padding:14px!important;border-radius:14px!important;}}
  div[data-testid="metric-container"] [data-testid="stMetricValue"]{{font-size:1.3rem!important;}}
  div[data-testid="metric-container"]{{padding:10px!important;}}
  section[data-testid="stSidebar"] button{{min-height:50px!important;}}
  div[data-testid="stPlotlyChart"]:hover{{transform:none!important;}}
}}
/* Small phones */
@media screen and (max-width:480px){{
  h1{{font-size:clamp(1.3rem,5.5vw,2rem)!important;}}
  h2{{font-size:clamp(1rem,4.5vw,1.4rem)!important;}}
  .glass{{padding:12px!important;border-radius:12px!important;}}
}}
/* Touch devices */
@media (hover:none) and (pointer:coarse){{
  section[data-testid="stSidebar"] button,div.stDownloadButton>button{{min-height:52px!important;}}
  section[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"]{{width:26px!important;height:26px!important;}}
  li[role="option"]{{padding:12px 16px!important;}}
}}
/* Retina / HiDPI */
@media (-webkit-min-device-pixel-ratio:2),(min-resolution:192dpi){{
  .glass{{backdrop-filter:blur(24px)!important;}}
}}
/* Safe area (iPhone notch / Android cutout) */
@supports (padding:env(safe-area-inset-bottom)){{
  section[data-testid="stSidebar"]>div{{padding-bottom:env(safe-area-inset-bottom)!important;}}
}}
/* Landscape phone */
@media screen and (max-height:500px) and (orientation:landscape){{
  .glass{{margin-bottom:10px!important;}}
}}
/* Print */
@media print{{
  section[data-testid="stSidebar"]{{display:none!important;}}
  .stApp{{background:white!important;}}
  .glass{{box-shadow:none!important;border:1px solid #e2e8f0!important;}}
}}
#MainMenu,footer,header,.stDeployButton{{display:none!important;}}
</style>"""


# ════════════════════════════════════════════════════════════════
# REGISTRATION PAGE
# ════════════════════════════════════════════════════════════════
def registration_page():
    bg = reg_background()
    st.markdown(responsive_css(bg, "rgba(2,8,23,.70)"), unsafe_allow_html=True)

    # Extra form-specific styles
    st.markdown("""
<style>
div[data-testid="stForm"]{
  background:rgba(8,15,40,.88)!important;
  backdrop-filter:blur(32px) saturate(1.4);-webkit-backdrop-filter:blur(32px);
  border-radius:22px!important;
  padding:clamp(24px,4vw,48px) clamp(20px,4vw,44px)!important;
  max-width:min(680px,95vw);margin:3vh auto;
  border:1px solid rgba(56,189,248,.18)!important;
  box-shadow:0 32px 80px rgba(0,0,0,.58),0 0 0 1px rgba(255,255,255,.04);
  position:relative;overflow:hidden;
}
div[data-testid="stForm"]::before{
  content:"";position:absolute;top:0;left:20%;right:20%;height:1px;
  background:linear-gradient(90deg,transparent,rgba(56,189,248,.65),transparent);
}
div[data-testid="stForm"] label{
  color:#94a3b8!important;font-family:'JetBrains Mono',monospace!important;
  font-size:clamp(9px,1vw,11px)!important;font-weight:600!important;
  letter-spacing:.13em!important;text-transform:uppercase!important;
}
div[data-testid="stForm"] div[data-baseweb="input"]>div,
div[data-testid="stForm"] div[data-baseweb="textarea"]>div,
div[data-testid="stForm"] div[data-baseweb="select"]>div{
  background:rgba(255,255,255,.07)!important;border-radius:10px!important;
  border:1px solid rgba(255,255,255,.12)!important;transition:all .22s;min-height:44px;
}
div[data-testid="stForm"] div[data-baseweb="input"]>div:focus-within,
div[data-testid="stForm"] div[data-baseweb="textarea"]>div:focus-within,
div[data-testid="stForm"] div[data-baseweb="select"]>div:focus-within{
  border:1px solid rgba(56,189,248,.85)!important;
  box-shadow:0 0 12px rgba(56,189,248,.38),0 0 0 1px #67e8f9!important;
  background:rgba(255,255,255,.10)!important;
}
div[data-testid="stForm"] input,div[data-testid="stForm"] textarea{
  color:#e2e8f0!important;-webkit-text-fill-color:#e2e8f0!important;
  font-family:'Inter',sans-serif!important;font-size:clamp(13px,1.4vw,15px)!important;font-weight:500!important;
}
div[data-testid="stForm"] input::placeholder,div[data-testid="stForm"] textarea::placeholder{color:#475569!important;}
div[data-testid="stForm"] div[data-baseweb="select"] span{color:#e2e8f0!important;}
div[data-testid="stForm"] button{
  background:linear-gradient(135deg,#0891b2,#1d4ed8)!important;
  color:#fff!important;-webkit-text-fill-color:#fff!important;
  border-radius:10px!important;min-height:52px!important;
  font-family:'Inter',sans-serif!important;font-size:clamp(13px,1.4vw,16px)!important;
  font-weight:700!important;letter-spacing:.05em!important;border:none!important;
  box-shadow:0 4px 24px rgba(8,145,178,.4)!important;transition:all .22s!important;touch-action:manipulation!important;
}
div[data-testid="stForm"] button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 32px rgba(8,145,178,.52)!important;}
div[data-testid="stForm"] button:active{transform:scale(.97)!important;}
h1{font-size:clamp(1.9rem,4.5vw,3.2rem)!important;text-align:center;
  background:linear-gradient(110deg,#fff 10%,#67e8f9 55%,#a78bfa 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  letter-spacing:-.03em;margin-bottom:4px;}
.stMarkdown p{text-align:center;font-size:clamp(13px,1.4vw,16px)!important;color:#94a3b8!important;}
div[data-testid="stSuccess"]{background:rgba(4,120,87,.13)!important;border:1px solid rgba(4,120,87,.42)!important;border-radius:10px!important;}
div[data-testid="stSuccess"] p{color:#6ee7b7!important;font-weight:600;}
div[data-testid="stError"]{background:rgba(185,28,28,.13)!important;border:1px solid rgba(185,28,28,.42)!important;border-radius:10px!important;}
div[data-testid="stError"] p{color:#fca5a5!important;font-weight:600;}
@media(max-width:768px){div[data-testid="stForm"]{padding:20px 16px!important;}}
</style>""", unsafe_allow_html=True)

    st.title("🩺 Patient Registration")
    st.markdown("Register to access the AI-Powered Diabetes Risk Assessment System")

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("reg_form"):
            name             = st.text_input("Full Name")
            country_list     = [ct.name for ct in pycountry.countries]
            selected_country = st.selectbox("🌍 Country", country_list)
            country_obj      = pycountry.countries.get(name=selected_country)
            phone            = st.text_input("Phone Number (without country code)")
            email            = st.text_input("Email Address")
            address          = st.text_area("Address")
            submit           = st.form_submit_button("🚀  Register & Continue")

            if submit:
                name=name.strip(); phone=phone.strip(); email=email.strip(); address=address.strip()
                if not all([name, phone, email, address]):
                    st.error("❌ Please fill all fields."); return
                if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
                    st.error("❌ Invalid email address."); return
                try:
                    parsed = phonenumbers.parse(phone, country_obj.alpha_2)
                    if not phonenumbers.is_valid_number(parsed):
                        st.error("❌ Invalid phone number for selected country."); return
                    fmt = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                except Exception:
                    st.error("❌ Invalid phone number format."); return

                ist = pytz.timezone("Asia/Kolkata")
                now = datetime.now(ist)
                pid = "PAT" + str(uuid.uuid4().int)[:6]
                ud  = {"_id": pid, "name": name, "phone": fmt,
                       "country": selected_country, "email": email, "address": address,
                       "gender": "Not Selected",
                       "created_at": now.strftime("%d-%m-%Y %I:%M:%S %p IST")}
                users_col.insert_one(ud)
                st.session_state.patient_info = ud
                st.session_state.registered   = True
                st.session_state.show_success = True
                st.rerun()


# ════════════════════════════════════════════════════════════════
# PREDICTION PAGE
# ════════════════════════════════════════════════════════════════
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

    bg = pred_background()
    st.markdown(responsive_css(bg, "rgba(5,14,30,.78)"), unsafe_allow_html=True)
    st.markdown("<style>h1,h2,h3,h4{color:#fff!important;} p,li{color:#e2e8f0!important;}</style>",
                unsafe_allow_html=True)

    # ── SIDEBAR ──────────────────────────────────────────────
    info = st.session_state.patient_info
    st.sidebar.markdown("## 🏥 Patient Profile")
    st.sidebar.markdown(f"**👤** {info.get('name','')}")
    st.sidebar.markdown(f"📞 {info.get('phone','')}")
    st.sidebar.markdown(f"✉️ {info.get('email','')}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔬 Clinical Inputs")

    age    = st.sidebar.number_input("Age (years)", 21, 100, 30)
    gender = st.sidebar.selectbox("Gender", ["Male","Female"])
    pregnancies = 0
    if gender == "Female":
        pregnancies = st.sidebar.number_input("Pregnancies", 0, 20, 0)

    glucose = st.sidebar.slider("Glucose (mg/dL)",              0, 200, 120)
    bp      = st.sidebar.slider("Blood Pressure (mmHg)",        0, 130,  70)
    skin    = st.sidebar.slider("Skin Thickness (mm)",           0, 100,  20)
    insulin = st.sidebar.slider("Insulin (µIU/mL)",              0, 900,  80)
    bmi     = st.sidebar.number_input("BMI (kg/m²)",            10.0, 70.0, 25.0)
    dpf     = st.sidebar.slider("Diabetes Pedigree Function",   0.0, 2.5, 0.5)

    st.sidebar.markdown("---")
    predict_btn = st.sidebar.button("🔍  Predict Risk",  use_container_width=True)
    logout_btn  = st.sidebar.button("←  Logout",         use_container_width=True)

    if logout_btn:
        st.session_state.registered   = False
        st.session_state.patient_info = {}
        st.session_state.show_success = False
        st.rerun()

    # ── MAIN ─────────────────────────────────────────────────
    st.title("🩺 Diabetes Prediction System")
    st.markdown("AI-Powered Clinical Risk Assessment · SVM Model")

    if st.session_state.show_success:
        st.success("✅ Registration successful! Enter clinical values in the sidebar and click Predict.")
        st.session_state.show_success = False

    st.markdown("""
<div class="glass">
  <h3 style="margin-top:0;font-size:clamp(1rem,2vw,1.3rem);">📋 About This System</h3>
  <p>This system uses a trained <strong>Support Vector Machine (SVM)</strong> model to assess
  diabetes risk from clinical parameters including glucose, BMI, blood pressure, insulin, skin
  thickness, diabetes pedigree function, and age. Fill the sidebar inputs and click
  <em>Predict Risk</em> to receive an assessment with a downloadable professional medical PDF report.</p>
</div>""", unsafe_allow_html=True)

    if predict_btn:
        with st.spinner("🧠 Analysing clinical data..."):
            time.sleep(0.5)
            if "_id" in info:
                users_col.update_one({"_id": info["_id"]}, {"$set": {"gender": gender}})

            inp     = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
            inp_std = scaler.transform(inp)
            prob    = model.predict_proba(inp_std)[0]
            prob_neg, prob_pos = prob[0]*100, prob[1]*100

            if   prob_pos < 30: risk_label = "Low Risk"
            elif prob_pos < 70: risk_label = "Moderate Risk"
            else:               risk_label = "High Risk"

            ist = pytz.timezone("Asia/Kolkata")
            now = datetime.now(ist)
            preds_col.insert_one({
                "patient_id": info["_id"], "patient_name": info["name"],
                "age": age, "gender": gender, "glucose": glucose, "blood_pressure": bp,
                "bmi": bmi, "prediction": risk_label, "probability": round(prob_pos, 2),
                "created_at": now.strftime("%d-%m-%Y %H:%M:%S IST"),
            })

            # ── Risk / positive factors ──────────────────────
            risk_fs, pos_fs = [], []
            if   glucose >= 126:         risk_fs.append("High Glucose Level (≥ 126 mg/dL)")
            elif 100 <= glucose < 126:   risk_fs.append("Prediabetic Glucose (100–125 mg/dL)")
            else:                        pos_fs.append("Normal Glucose Level (< 100 mg/dL)")
            if   bmi > 30:               risk_fs.append(f"Obesity — High BMI ({bmi:.1f} kg/m²)")
            elif 18.5 <= bmi <= 24.9:    pos_fs.append(f"Healthy BMI ({bmi:.1f} kg/m²)")
            if   age > 45:               risk_fs.append(f"Age Above 45 Years ({age} yrs)")
            if   bp > 120:               risk_fs.append(f"High Blood Pressure ({bp} mmHg)")
            elif 90 <= bp <= 120:        pos_fs.append(f"Normal Blood Pressure ({bp} mmHg)")
            if   dpf > 0.5:              risk_fs.append(f"Elevated Genetic Risk (DPF {dpf:.2f})")
            if   skin > 35:              risk_fs.append(f"High Skin Fold Thickness ({skin} mm)")
            if   insulin > 300:          risk_fs.append(f"High Insulin Level ({insulin} µIU/mL)")

            # ── Recommendations ──────────────────────────────
            if prob_pos >= 70:
                recs = ["Consult a healthcare professional immediately",
                        "Get HbA1c & full diabetes screening",
                        "Monitor blood glucose levels daily",
                        "Follow a strict low-glycaemic index diet",
                        "Increase physical activity ≥ 150 min/week",
                        "Consider medication as prescribed by doctor"]
            elif prob_pos >= 30:
                recs = ["Schedule a diabetes screening test soon",
                        "Adopt a balanced, low-sugar diet",
                        "Exercise minimum 30 min/day",
                        "Monitor glucose levels every 3 months",
                        "Maintain healthy weight (BMI 18.5–24.9)"]
            else:
                recs = ["Continue healthy lifestyle habits",
                        "Exercise regularly — 30 min/day minimum",
                        "Maintain balanced diet and hydration",
                        "Annual health check-ups recommended",
                        "Monitor weight and blood pressure regularly"]

            # ── Results Display ──────────────────────────────
            st.markdown("---")
            st.header("📊 Prediction Results")

            st.markdown('<div class="gcard">', unsafe_allow_html=True)
            r1, r2 = st.columns([2, 1])
            with r1:
                if   prob_pos < 30: st.success(f"✅ LOW RISK — {risk_label}")
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
                    number={"suffix":"%","font":{"color":"white","size":28,"family":"Inter"}},
                    title={"text":"Risk Level","font":{"color":"#94a3b8","size":13}},
                    gauge={"axis":{"range":[0,100],"tickcolor":"rgba(255,255,255,.2)"},
                           "bar":{"color":gc,"thickness":0.22},"bgcolor":"rgba(0,0,0,0)","borderwidth":0,
                           "steps":[{"range":[0,30],"color":"rgba(34,197,94,.14)"},
                                    {"range":[30,70],"color":"rgba(245,158,11,.14)"},
                                    {"range":[70,100],"color":"rgba(239,68,68,.14)"}],
                           "threshold":{"line":{"color":gc,"width":3},"thickness":.8,"value":prob_pos}}))
                fig_g.update_layout(paper_bgcolor="rgba(0,0,0,0)",font=dict(color="white"),
                                    height=250,margin=dict(l=16,r=16,t=24,b=8))
                st.plotly_chart(fig_g, use_container_width=True,
                                config={"responsive":True,"displayModeBar":False})
            st.markdown('</div>', unsafe_allow_html=True)

            # Risk Factors
            st.markdown("---"); st.subheader("⚠️ Risk Factor Analysis")
            if risk_fs:
                st.warning("**Identified Risk Factors:**")
                for f in risk_fs: st.markdown(f"- 🔴 {f}")
            if pos_fs:
                st.success("**Positive Health Indicators:**")
                for f in pos_fs:  st.markdown(f"- 🟢 {f}")

            # Recommendations
            st.markdown("---"); st.subheader("💊 Medical Recommendations")
            rec_md = "\n".join(f"- {r}" for r in recs)
            if   prob_pos >= 70: st.error(rec_md)
            elif prob_pos >= 30: st.warning(rec_md)
            else:                st.success(rec_md)

            # Charts
            cause_labels, cause_values = [], []
            if glucose >= 126: cause_labels.append("High Glucose"); cause_values.append(min(glucose/2, 100))
            if bmi > 30:       cause_labels.append("High BMI");     cause_values.append(min(bmi*2, 100))
            if age > 45:       cause_labels.append("Age Factor");   cause_values.append(min(age, 100))
            if bp > 120:       cause_labels.append("High BP");      cause_values.append(min(bp, 100))
            if dpf > 0.5:      cause_labels.append("Genetics");     cause_values.append(min(dpf*100, 100))
            if not cause_labels: cause_labels = ["Healthy"]; cause_values = [100]

            scr = ["#dc2626","#d97706","#2563eb","#7c3aed","#047857","#0891b2"]
            bc2 = [scr[i%len(scr)] for i in range(len(cause_labels))]

            st.markdown('<div class="glass">', unsafe_allow_html=True)
            st.subheader("📊 Risk Contribution Analysis")
            c1, c2 = st.columns(2)
            bar_f = go.Figure(go.Bar(
                x=cause_labels, y=cause_values,
                text=[f"{v:.0f}" for v in cause_values], textposition="auto",
                marker=dict(color=bc2, line=dict(color="rgba(255,255,255,.15)", width=1.5)),
                textfont=dict(color="white", size=13, family="Inter")))
            bar_f.update_layout(
                title="Risk Factor Severity", xaxis_title="Factors", yaxis_title="Level (0-100)",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Inter"), autosize=True,
                margin=dict(l=20,r=20,t=50,b=20))
            bar_f.update_xaxes(showline=True, linecolor="rgba(255,255,255,.12)")
            bar_f.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,.07)")
            with c1:
                st.plotly_chart(bar_f, use_container_width=True,
                                config={"responsive":True,"displayModeBar":False})
            pie_f = go.Figure(go.Pie(
                labels=cause_labels, values=cause_values, hole=0.45,
                marker=dict(colors=bc2, line=dict(color="rgba(0,0,0,.3)", width=2)),
                textfont=dict(color="white", size=12, family="Inter")))
            pie_f.update_layout(
                title="Contribution %",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Inter"), autosize=True,
                margin=dict(l=20,r=20,t=50,b=20))
            with c2:
                st.plotly_chart(pie_f, use_container_width=True,
                                config={"responsive":True,"displayModeBar":False})
            st.markdown("</div>", unsafe_allow_html=True)

            # ── PDF ──────────────────────────────────────────
            pdf_bytes = build_pdf(
                info=info, age=age, gender=gender, glucose=glucose, bp=bp,
                skin=skin, insulin=insulin, bmi=bmi, dpf=dpf,
                pregnancies=pregnancies, prob_pos=prob_pos,
                risk_label=risk_label, now=now,
                recs=recs, risk_fs=risk_fs, pos_fs=pos_fs)

            st.markdown("---")
            st.download_button(
                label="📄  Download Professional Medical Report (PDF)",
                data=pdf_bytes,
                file_name=f"DiabetesReport_{info.get('name','Patient').replace(' ','_')}.pdf",
                mime="application/pdf")

            st.markdown("---")
            st.warning("⚠️ **Medical Disclaimer:** This AI tool does NOT replace professional "
                       "medical advice. Consult a qualified healthcare professional for diagnosis and treatment.")


# ════════════════════════════════════════════════════════════════
# NAVIGATION
# ════════════════════════════════════════════════════════════════
if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
