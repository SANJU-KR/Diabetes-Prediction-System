# -----------------------------
# Import Required Libraries
# -----------------------------
#from anyio import current_time
import streamlit as st
import numpy as np
import joblib
import plotly.graph_objects as go
import base64
import re
import pycountry
import phonenumbers

def get_base64_image(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def country_to_flag(country_code):
    return "".join(chr(127397 + ord(char)) for char in country_code.upper())

# ✅ ADDED FOR PDF GENERATION ONLY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO


# -----------------------------
# MongoDB Connection
# -----------------------------

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# -----------------------------
# MongoDB Connection
# -----------------------------
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import uuid
import pytz

#  my string
uri = "mongodb+srv://project00067:Project123@cluster0.vzzvdti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

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
   
    # Convert image to base64
    def get_base64_image(image_file):
        with open(image_file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()

    img = get_base64_image("health.png")   #image name

    st.markdown(f"""
    <style>
    /* Full Background */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.10), rgba(0,0,0,0.10)),
                    url("data:image/jpg;base64,{img}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Segoe UI', sans-serif;
    }}
   


   /* Center the form - Glass Effect */
div[data-testid="stForm"] {{
    background: rgba(255, 255, 255, 0.10);
    backdrop-filter: blur(.2px);
    border-radius: 25px;
    padding: 40px;

    width: 100%;
    max-width: 700px;
    margin: 5vh auto;

    border: 1px solid rgba(255,255,255,0.25);
    box-shadow: 0 10px 50px rgba(0,0,0,0.3);
}}

    /* Title styling */
    h1 {{
        color: white !important;
        text-align: center;
        font-weight: 700;
        font-size: 40px;
        margin-bottom: 10px;
    }}

    /* Subtitle text */
    .stMarkdown p {{
        color: #f1f1f1 !important;
        text-align: center;
        font-size: 18px;
        font-weight: 500;
    }}

/* ===== TRUE GLASS INPUT STYLE ===== */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div {{

    background: rgba(255, 255, 255, 0.08) !important;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);

    border-radius: 18px !important;
    border: 1.5px solid rgba(255, 255, 255, 0.35) !important;

    box-shadow: inset 0 0 12px rgba(255,255,255,0.15);
    transition: all 0.3s ease;
}}

/* Focus Glow Effect */
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="textarea"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within {{

    border: 1.5px solid rgba(255,255,255,0.8) !important;
    box-shadow: 0 0 20px rgba(255,255,255,0.6);
}}

input, textarea {{
    color: black !important;
    font-weight: 500 !important;
}}



     /* Make form labels more visible */
    label {{
        color: #ffffff !important;
        font-size: 19px !important;
        font-weight: 800 !important;
        letter-spacing: 0.6px;
        text-shadow: 0px 2px 6px rgba(0,0,0,0.7);
    }}



    /* Placeholder text visibility */
    input::placeholder, textarea::placeholder {{
        color: #555 !important;
        font-weight: 500 !important;
    }}

    


    /* Button Styling */
    div[data-testid="stForm"] button {{
        background: linear-gradient(90deg, #1f8ef1, #005bea);
        color: white !important;
        border-radius: 12px !important;
        height: 50px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: 0.3s ease-in-out;
    }}

    div[data-testid="stForm"] button:hover {{
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0,91,234,0.6);
    }}
   
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
<style>
@media (max-width: 768px) {

    div[data-testid="stForm"] {
        padding: 25px !important;
        margin-top: 20px !important;
    }

    h1 {
        font-size: 28px !important;
    }

}
             @media (max-width: 768px) {
    div[data-testid="stForm"] {
        padding: 20px !important;
        margin-top: 30px !important;
    }

    h1 {
        font-size: 26px !important;
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
        country_list = []

        for country in pycountry.countries:
         country_list.append(country.name)

        selected_country = st.selectbox("🌍 Select Country", country_list)

        # Extract country name
        country_name = selected_country
        country_obj = pycountry.countries.get(name=country_name)

        # 📞 Auto Phone Code
        country_code = phonenumbers.country_code_for_region(country_obj.alpha_2)

        #st.write(f"📞 Phone Code: +{country_code}")

        phone = st.text_input("Enter Phone Number (without country code)")

       
        email = st.text_input("Email Address")
        address = st.text_area("Address")

        submit = st.form_submit_button("Register")

        if submit:

            # -----------------------------
        # Clean Inputs
        # -----------------------------
         name = name.strip()
         phone = phone.strip()
         email = email.strip()
         address = address.strip()

        if not name or not phone or not email or not address:
            st.error("❌ Please fill all fields properly")
            return

        # -----------------------------
        # Email Validation
        # -----------------------------
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            st.error("❌ Please enter a valid email address")
            return
        # -----------------------------
        # Country & Phone Validation
        # -----------------------------
        country_obj = pycountry.countries.get(name=selected_country)

        if not country_obj:
            st.error("❌ Invalid country selected")
            return

        region_code = country_obj.alpha_2

        try:
            parsed_number = phonenumbers.parse(phone, region_code)

            if not phonenumbers.is_valid_number(parsed_number):
                st.error("❌ Invalid phone number for selected country")
                return

            formatted_phone = phonenumbers.format_number(
                parsed_number,
                phonenumbers.PhoneNumberFormat.E164
            )

        except:
            st.error("❌ Invalid phone number format")
            return        
              # -----------------------------
        # Create Patient Record
        # -----------------------------
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


           # if st.button("Register"):
                
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
       
      
         
       # ✅ THEN load model

       model, scaler = load_model()

       if not st.session_state.patient_info:
         st.session_state.registered = False
         st.stop()


       # ✅ Background Image for Prediction Page
       img = get_base64_image("health22.png")  # your image name

       st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,.23), rgba(0,0,0,.23)),
                        url("data:image/png;base64,{img}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
      """, unsafe_allow_html=True)
  
      

       st.markdown("""
        <style>

   /* Glass effect content area */


     h1, h2, h3 {
     color: white !important;
       }

     p, li {
      color: #f1f1f1 !important;
    /* font-size: 25px; */
      font-size:clamp(16px,2vw,22px)             
      }

      ul {
      line-height: 1.8;
      }

     </style>
    """, unsafe_allow_html=True)
       
    

  

    # -----------------------------
    # Sidebar Styling (FIXED)
    # -----------------------------

 # -----------------------------
    # Glass Sidebar Styling
    # -----------------------------
       st.markdown("""
            <style>
            section[data-testid="stSidebar"] {
            background: rgba(300,300,300,0.10) !important;
            backdrop-filter: blur(7px);
           -webkit-backdrop-filter: blur(25px);
            border-right: 1px solid rgba(300,300,300,0.1o);
            box-shadow: 4px 0 30px rgba(0,0,0,0.4);
            padding: 25px;
           }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p {
        color: white !important;
        font-weight: 600;
        }

        section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background: rgba(255,255,255,255.10) !important;
        backdrop-filter: blur(15px);
        border-radius: 14px !important;
        border: 1.5px solid rgba(255,255,255,0.35) !important;
        color: white !important;
        }

        section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {
        border: 1.5px solid rgba(255,255,255,0.8) !important;
        box-shadow: 0 0 15px rgba(255,255,255,0.6);
        }

        section[data-testid="stSidebar"] button {
        background: rgba(255,255,255,0.15) !important;
        backdrop-filter: blur(15px);
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.4) !important;
        color: white !important;
        font-weight: 600 !important;
        transition: 0.3s ease;
        }

        section[data-testid="stSidebar"] button:hover {
        background: rgba(255,255,255,0.25) !important;
        transform: scale(1.03);
        }

       </style>
       """, unsafe_allow_html=True)

       st.markdown("""
<style>

/* Dropdown popup background */
div[data-baseweb="popover"] {
    background: midnightblue  !important;
    backdrop-filter: blur(20px);
}

/* Dropdown list container */
ul[role="listbox"] {
    background: midnightblue !important;
}

/* Each dropdown option */
li[role="option"] {
    background: #1e2a4a !important;
    color: white !important;
    font-weight: 600 !important;
}

/* Hover effect */
li[role="option"]:hover {
    background: #00d4ff !important;
    color: black !important;
}

</style>
""", unsafe_allow_html=True)
       
       st.markdown("""
<style>

/* Selected dropdown value text */
section[data-testid="stSidebar"] div[data-baseweb="select"] span {
    color: black !important;
    font-weight: 600 !important;
}

/* Dropdown input box background */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #f1f5f9 !important;   /* light gray */
    color: black !important;
}

</style>
""", unsafe_allow_html=True) 
       
       st.markdown("""
<style>

/* ===== FIX DOWNLOAD BUTTON VISIBILITY ===== */
div.stDownloadButton > button {
    background-color: #0f172a !important;   /* dark navy */
    color: white !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 10px 20px !important;
    border: 1px solid #00d4ff !important;
}

/* Hover effect */
div.stDownloadButton > button:hover {
    background-color: #00d4ff !important;
    color: black !important;
    transform: scale(1.03);
}

</style>
""", unsafe_allow_html=True)
       
       st.markdown("""
<style>
.glass-box {
     background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(25px);
    -webkit-backdrop-filter: blur(25px);
    border-radius: 20px;
    padding: 40px;
    border: 1px solid rgba(255,255,255,0.25);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    margin-bottom: 40px;
}
                   

                   @media (max-width: 992px) {
    section[data-testid="stSidebar"] {
        width: 100% !important;
    }
}
</style>
""", unsafe_allow_html=True)

            

    # -----------------------------
    # Load Model
    # -----------------------------

    
   



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

       age = st.sidebar.slider("Age", 21, 100, 30)

       gender = st.sidebar.selectbox(
        "Gender",
        ["Male", "Female"]
    )
   

# Pregnancy input only for female
       if gender == "Female":
        pregnancies = st.sidebar.number_input(
            "Number of Pregnancies",
            min_value=0,
            max_value=20,
            value=0
        )
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

       #if st.sidebar.button("Logout"):
        #st.session_state.registered = False
        #st.rerun()
       logout_btn = st.sidebar.button("Logout")

       if logout_btn:
         st.session_state.registered = False
         st.session_state.patient_info = {}
         st.session_state.show_success = False
         st.rerun() 

    # -----------------------------
    # Main Title
    # -----------------------------
       st.title("🩺 Diabetes Prediction System")
       st.markdown("AI-Powered Diabetes Risk Assessment Tool")

       if st.session_state.show_success:
        st.success("✅ Registration Successful!")
        st.session_state.show_success = False

    # -----------------------------
    # About System
    # -----------------------------
       st.markdown("""
    ### 📋 About This System

    This Diabetes Prediction System is an AI-powered medical risk assessment tool designed to estimate the likelihood of diabetes based on key health parameters such as glucose level, BMI, blood pressure, age, and family history.

    The system uses a trained Machine Learning model to analyze patterns in medical data and provide an instant risk classification (Low, Moderate, or High). In addition to prediction, it also highlights potential risk factors, positive health indicators, and personalized recommendations to support preventive care.
    ### 🧭 How to Use

    • Enter patient details in sidebar  
    • Click Predict  
    • View results and recommendations  
    """)

    # -----------------------------
    # Prediction
    # -----------------------------
       if predict_btn:
         #update gender in mongodb
        if "_id" in info:
         users_collection.update_one(
              {"_id":info["_id"]},
                {"$set":{"gender":gender}}
        ) 
         
         input_data = np.array([[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]])
         input_std = scaler.transform(input_data)
         prediction = model.predict(input_std)[0]
         probability = model.predict_proba(input_std)[0]

         prob_negative = probability[0] * 100
         prob_positive = probability[1] * 100

        # ✅ ADD HERE (SAVE TO DATABASE)
        # -----------------------------
        # Determine Risk Label

         if prob_positive<30:
            risk_label="Low Risk"
         elif prob_positive<70:
            risk_label="Moderate Risk"
         else:
            risk_label="High Risk"

        # Indian Time
         ist = pytz.timezone('Asia/Kolkata')
         current_time = datetime.now(ist)    

        # Save prediction to MongoDB
         prediction_data = {
    "patient_id": info["_id"],
    "patient_name": info["name"],
    "age": age,
    "gender": gender,
    "glucose": glucose,
    "blood_pressure": bp,
    "bmi": bmi,
    "prediction": risk_label,
    "probability": round(prob_positive, 2),
    "created_at": current_time.strftime("%d-%m-%Y %H:%M:%S")
}

                 
         predictions_collection.insert_one(prediction_data)

      
         st.markdown("---")
         st.header("Prediction Results")
         
         st.markdown(f"""
        **Patient:** {info.get('name','')}  
        **Age:** {age}  
        **Gender:** {gender}  
         """)

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
            c2.metric("Diabetic", f"{prob_positive:.1f}%")

         with col2:

            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prob_positive,
                number={"suffix": "%"},
                title={"text": "Risk Level"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "steps": [
                        {"range": [0, 30], "color": "green"},
                        {"range": [30, 70], "color": "yellow"},
                        {"range": [70, 100], "color": "red"}
                    ]
                }
            ))

            st.plotly_chart(fig, use_container_width=True)

 
        # -----------------------------
        # Risk Factor Analysis
        # -----------------------------
         st.markdown("---")
         st.subheader("Risk Factor Analysis")

         risk_factors = []
         positive_factors = []

        # Glucose
         if glucose >= 126:
            risk_factors.append("High Glucose Level (≥126 mg/dL)")
         elif 100 <= glucose < 126:
             risk_factors.append("Prediabetic Glucose Level (100–125 mg/dL)")
         else:
            positive_factors.append("Normal Glucose Level(<100 mg/dL)")    

         if bmi > 30:
            risk_factors.append("High BMI (Obesity)")
         elif 18.5 <= bmi <= 24.9:
            positive_factors.append("Healthy BMI")

         if age > 45:
            risk_factors.append("Age above 45")

         if bp > 120:
            risk_factors.append("High Blood Pressure (>120 mmHg)")
         elif 90 <= bp <= 120:
             positive_factors.append("Normal Blood Pressure")


         if dpf > 0.5:
            risk_factors.append("Higher Genetic Risk")

         if risk_factors:
            st.warning("Identified Risk Factors:")
            for factor in risk_factors:
                st.markdown(f"- {factor}")

         if positive_factors:
            st.success("Positive Health Indicators:")
            for factor in positive_factors:
                st.markdown(f"- {factor}")

        # -----------------------------
        # Recommendations
        # -----------------------------
         st.markdown("---")
         st.subheader("Recommendations")

         if prob_positive >= 70:
            st.error("""
- Consult a healthcare professional immediately
- Get complete diabetes screening
- Monitor blood sugar regularly
- Improve diet and physical activity
""")
         elif prob_positive >= 30:
            st.warning("""
- Maintain healthy diet
- Increase physical activity
- Monitor glucose periodically
""")
         else:
            st.success("""
- Continue healthy lifestyle
- Exercise regularly
- Routine health check-ups
""")
            
           # -----------------------------
        # COMPLETE PROFESSIONAL PDF REPORT
        # -----------------------------
         buffer = BytesIO()
         doc = SimpleDocTemplate(buffer)
         elements = []
         styles = getSampleStyleSheet()
 
        # Title
         elements.append(Paragraph("Diabetes Prediction Report", styles["Heading1"]))
         elements.append(Spacer(1, 0.3 * inch))

        # Risk Level
         if prob_positive < 30:
            risk_level = "LOW RISK - Diabetes Unlikely"
         elif prob_positive < 70:
            risk_level = "MODERATE RISK - Possible Diabetes"
         else:
            risk_level = "HIGH RISK - Diabetes Likely"

         elements.append(Paragraph(f"<b>Overall Risk Level:</b> {risk_level}", styles["Normal"]))
         elements.append(Paragraph(f"<b>Risk Percentage:</b> {prob_positive:.1f}%", styles["Normal"]))
         elements.append(Spacer(1, 0.3 * inch))

        # Patient Info Table
         patient_table = [
            ["Name", info.get("name","")],
            ["Age", str(age)],
            ["Gender", gender],
            ["Phone", info.get("phone","")],
            ["Email", info.get("email","")],
        ]

         table = Table(patient_table, colWidths=[2.2*inch, 3*inch])
         table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 1, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ]))

         elements.append(Paragraph("Patient Information", styles["Heading2"]))
         elements.append(Spacer(1, 0.2 * inch))
         elements.append(table)
         elements.append(Spacer(1, 0.4 * inch))

        # Risk Factors Section
         elements.append(Paragraph("Risk Factor Analysis", styles["Heading2"]))
         elements.append(Spacer(1, 0.2 * inch))

         if risk_factors:
             elements.append(Paragraph("<b>Identified Risk Factors:</b>", styles["Normal"]))
             elements.append(Spacer(1, 0.1 * inch))
             risk_list = [ListItem(Paragraph(factor, styles["Normal"])) for factor in risk_factors]
             elements.append(ListFlowable(risk_list, bulletType='bullet'))
             elements.append(Spacer(1, 0.3 * inch))

         if positive_factors:
            elements.append(Paragraph("<b>Positive Health Indicators:</b>", styles["Normal"]))
            elements.append(Spacer(1, 0.1 * inch))
            positive_list = [ListItem(Paragraph(factor, styles["Normal"])) for factor in positive_factors]
            elements.append(ListFlowable(positive_list, bulletType='bullet'))
            elements.append(Spacer(1, 0.3 * inch))



                # -----------------------------
        # Diabetes Causes Visualization
        # -----------------------------

         st.markdown('<div class="glass-box">', unsafe_allow_html=True)
         st.markdown("---")
         st.subheader("📊 Causes of Diabetes (Risk Contribution Analysis)")

         col1, col2 = st.columns([1,1])

         cause_labels = []
         cause_values = []

        # Assign contribution scores based on medical thresholds

         if glucose >= 126:
            cause_labels.append("High Glucose")
            cause_values.append(min(glucose / 2, 100))

         if bmi > 30:
            cause_labels.append("High BMI (Obesity)")
            cause_values.append(min(bmi * 2, 100))

         if age > 45:
            cause_labels.append("Age Factor")
            cause_values.append(min(age, 100))

         if bp > 120:
            cause_labels.append("High Blood Pressure")
            cause_values.append(min(bp, 100))

         if dpf > 0.5:
            cause_labels.append("Genetic Risk (DPF)")
            cause_values.append(min(dpf * 100, 100))

        # If no major risk factors
         if not cause_labels:
            cause_labels = ["Healthy Indicators"]
            cause_values = [100]

        # -----------------------------
        # BAR CHART
        # -----------------------------
         bar_fig = go.Figure()

         bar_fig.add_trace(go.Bar(
            x=cause_labels,
            y=cause_values,
            text=[f"{v:.1f}" for v in cause_values],
            textposition='auto',

            marker=dict(
            color=cause_values,      # Color intensity based on value
            colorscale="Reds",       # Red gradient
             line=dict(color="white", width=2)
            ),

            textfont=dict(
            color="white",
            size=16
)
        ))

         bar_fig.update_layout(
            title="Risk Factor Severity",
            xaxis_title="Causes",
            yaxis_title="Severity Level",

             paper_bgcolor="rgba(0,0,0,0)",   # Removes white background
            plot_bgcolor="rgba(0,0,0,0)",    # Removes inner white area

            font=dict(color="white"),        # Makes text visible
            autosize=True,
           # height=400,
            margin=dict(l=20, r=20, t=50, b=20),
        )

         bar_fig.update_xaxes(tickfont=dict(color="white", size=14),
                              
               title_font=dict(color="white", size=16),
              showline=True,
              linecolor="white")
         bar_fig.update_yaxes(tickfont=dict(color="white", size=14),
                title_font=dict(color="white", size=16),
              showgrid=True,
               gridcolor="rgba(255,255,255,0.25)",
                zerolinecolor="white"
                )


         with col1:
          st.plotly_chart(bar_fig, use_container_width=True, config={"responsive": True})

        # -----------------------------
        # PIE CHART
        # -----------------------------
         pie_fig = go.Figure(data=[go.Pie(
            labels=cause_labels,
            values=cause_values,
            hole=0.4
        )])

         pie_fig.update_layout(
            title="Percentage Contribution of Each Risk Factor",

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",

            font=dict(color="white"),
            autosize=True,
            #height=400,
            margin=dict(l=20, r=20, t=50, b=20),
        )

         with col2:
            st.plotly_chart(pie_fig, use_container_width=True, config={"responsive": True})

         st.markdown('</div>', unsafe_allow_html=True)
 

        # Recommendations Section
         elements.append(Paragraph("Recommendations", styles["Heading2"]))
         elements.append(Spacer(1, 0.2 * inch))
 
         if prob_positive >= 70:
            recs = [
                "Consult a healthcare professional immediately",
                "Get complete diabetes screening",
                "Monitor blood sugar regularly",
                "Improve diet and physical activity"
            ]
         elif prob_positive >= 30:
            recs = [
                "Maintain healthy diet",
                "Increase physical activity",
                "Monitor glucose periodically"
            ]
         else:
            recs = [
                "Continue healthy lifestyle",
                "Exercise regularly",
                "Routine health check-ups"
            ]

         rec_list = [ListItem(Paragraph(r, styles["Normal"])) for r in recs]
         elements.append(ListFlowable(rec_list, bulletType='bullet'))

         elements.append(Spacer(1, 0.5 * inch))

        # Disclaimer
         elements.append(Paragraph(
            "Medical Disclaimer: This report is AI-generated and does not replace professional medical advice.",
            styles["Normal"]
        ))

         doc.build(elements)
         pdf = buffer.getvalue()
         buffer.close()
 
         st.download_button(
            label="📄 Download Full Medical Report (PDF)",
            data=pdf,
            file_name="diabetes_prediction_report.pdf",
            mime="application/pdf"
        )
         

   


         
         

        # -----------------------------
        # Disclaimer
        # -----------------------------
         st.markdown("---")
         st.warning("""
⚠️ Medical Disclaimer:  
This tool does NOT replace professional medical advice.
""")


# =====================================================
# Navigation
# =====================================================
if not st.session_state.registered:
    registration_page()
else:
    prediction_page()
