import streamlit as st
import requests
import json
from datetime import datetime

# --- LAPAS KONFIGURĀCIJA ---
st.set_page_config(page_title="Inquiry Auditor", page_icon="🔍", layout="centered")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password")
    st.info(f"Current Year: {datetime.now().year}")
    st.divider()

# --- FUNCTIONS ---
def get_available_model(api_key):
    for version in ["v1", "v1beta"]:
        url = f"https://generativelanguage.googleapis.com/{version}/models?key={api_key}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', []) if 'gemini' in m['name']]
                for m in models:
                    if "1.5-flash" in m: return m, version
                if models: return models[0], version
        except: continue
    return None, None

def audit_email(api_key, text):
    model_path, api_version = get_available_model(api_key)
    if not model_path: return "ERROR", "API Key invalid or API disabled."

    url = f"https://generativelanguage.googleapis.com/{api_version}/{model_path}:generateContent?key={api_key}"
    
    prompt = f"""
    You are a professional travel coordinator. 
    Analyze the email below and check for these 8 requirements:
    1. Exact dates and times of the requested service.
    2. Number of passengers (sometimes only an estimate is given).
    3. Pick-up and drop-off locations (addresses, hotels, or landmarks).
    4. Type of vehicle preferred (standard coach, minibus, luxury van, etc.).
    5. Luggage requirements (especially for airport transfers).
    6. Service duration (daily disposals or tours).
    7. Any additional needs (guide, multiple stops, special requests).
    8. Driver accommodation & meals (for multi-day tours, clarify if client provides or included).

    --- TASK ---
    1. Identify what is MISSING from the 8 points above.
    2. Draft a polite response email. 
       - If dates, times, or addresses are missing, use: "Could you please provide an exact itinerary, with dates, times, and location addresses?"
       - If it's a tour and hours are missing, use: "For day tours, I need to know how many hours per day you need the services and how many days in each country/city."
       - For airport transfers, use: "For the airport transfers, I need to know the pick-up times."
    
    Current Year: {datetime.now().year}
    
    --- EMAIL TO AUDIT ---
    {text}
    """

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return "SUCCESS", result['candidates'][0]['content']['parts'][0]['text'].replace("**", "")
        else: return "ERROR", f"Google Error {response.status_code}"
    except Exception as e: return "ERROR", str(e)

# --- CLEAR TEXT LOGIKA ---
def clear_audit_input():
    st.session_state["audit_input"] = ""

# --- UI ---
st.title("🔍 Email Inquiry Auditor")
st.markdown("Scans for missing logistics and drafts a professional reply.")

# Ievades lauks ar atslēgu "audit_input"
email_input = st.text_area("Paste the customer's email here:", 
                           height=300, 
                           key="audit_input")

col1, col2 = st.columns([1, 4])
with col1:
    st.button("Clear Text", on_click=clear_audit_input)
with col2:
    audit_btn = st.button("Audit & Draft Reply", type="primary")

if audit_btn:
    if not api_key: st.error("Please enter your API Key!")
    elif not st.session_state["audit_input"]: st.warning("Please paste an email first.")
    else:
        with st.spinner("Auditing missing information..."):
            status, result = audit_email(api_key, st.session_state["audit_input"])
            if status == "SUCCESS":
                st.success("Analysis Complete")
                st.markdown("---")
                st.markdown("### 📋 AI Analysis & Draft Response")
                st.write(result)
            else:
                st.error("Audit failed.")
                st.code(result)
