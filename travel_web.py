import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Inquiry Auditor", page_icon="🔍", layout="centered")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password")
    st.info(f"Today is: {datetime.now().strftime('%A, %d.%m.%Y')}")
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
    
    current_date = datetime.now().strftime('%A, %d.%m.%Y')
    
    # --- SMART AUDIT PROMPT ---
    prompt = f"""
    You are a professional travel auditor. Analyze this email against 8 requirements.
    Today's Date: {current_date}.

    --- CRITICAL CHECKS ---
    1. EXACT DATES: If the client says "Monday the 13th" without a month, flag it as MISSING MONTH.
    2. PAX COUNT: If the client asks for vehicle prices (e.g., "8-seater") but does not state how many people are traveling, flag it as MISSING PAX.
    3. LOCATIONS: Must have specific cities/hotels.
    4. VEHICLE: Preferred type.
    5. LUGGAGE: Amount/Type.
    6. DURATION: Hours/Days.
    7. EXTRAS: Guides/Stops.
    8. DRIVER: Meals/Lodging (if multi-day).

    --- TASK ---
    1. List what is MISSING or VAGUE.
    2. Write a polite reply. 
       - If the month is missing: "Could you please clarify which month you are traveling in?"
       - If pax are missing: "Could you please confirm the total number of passengers?"
       - Use the phrases: "Could you please provide an exact itinerary..." and "As soon as I have all the information, I will be able to calculate the costs!"

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

# --- CLEAR LOGIC ---
def clear_audit_input():
    st.session_state["audit_input"] = ""

# --- UI ---
st.title("🔍 Email Inquiry Auditor")
st.markdown("Checks for missing months, passenger counts, and logistics.")

email_input = st.text_area("Paste the customer's email here:", 
                           height=300, 
                           key="audit_input")

col1, col2 = st.columns([1, 4])
with col1:
    st.button("Clear Text", on_click=clear_audit_input)
with col2:
    audit_btn = st.button("Audit Inquiry", type="primary")

if audit_btn:
    if not api_key: st.error("Please enter your API Key!")
    elif not st.session_state["audit_input"]: st.warning("Please paste an email.")
    else:
        with st.spinner("Sherlock is investigating the details..."):
            status, result = audit_email(api_key, st.session_state["audit_input"])
            if status == "SUCCESS":
                st.success("Audit Complete")
                st.markdown("---")
                st.markdown("### 📋 Analysis & Draft Response")
                st.write(result)
            else:
                st.error("Audit failed.")
                st.code(result)
