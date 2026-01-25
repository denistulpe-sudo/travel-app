import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Inquiry Auditor Pro", page_icon="🔍", layout="centered")

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
    
    # --- COLOR-CODED PROMPT ---
    prompt = f"""
    You are a professional travel auditor. Analyze this email.
    Today's Date: {current_date}.

    --- 8 REQUIREMENTS ---
    1. Dates/Times (Must include Month/Year).
    2. Pax Count (Must be specific number of people, not vehicle seats).
    3. Locations (Pick-up/Drop-off).
    4. Vehicle Type.
    5. Luggage.
    6. Duration.
    7. Extras (Guide/Stops).
    8. Driver Meals/Accom.

    --- FORMATTING INSTRUCTIONS ---
    1. PART 1: "📊 Analysis"
       - Go through the 8 points.
       - If a point is MET, write it like this: :green[✅ **[Requirement Name]**: [Details found]]
       - If a point is MISSING or VAGUE (like missing month or pax), write it like this: :red[❌ **[Requirement Name]**: [What is missing]]
       - Put every point on a new line.

    2. PART 2: "✉️ Draft Reply"
       - Write a polite professional email asking ONLY for the items marked with ❌.
       - Use standard phrases: "Could you please provide an exact itinerary...", "As soon as I have all the information..."

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
st.markdown("Highlights met requirements in :green[Green] and missing ones in :red[Red].")

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
        with st.spinner("Checking requirements..."):
            status, result = audit_email(api_key, st.session_state["audit_input"])
            if status == "SUCCESS":
                st.success("Analysis Complete")
                # Using st.markdown allows the colors to render correctly
                st.markdown(result)
            else:
                st.error("Audit failed.")
                st.code(result)
