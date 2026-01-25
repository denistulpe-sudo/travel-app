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
    # We calculate the year here to pass it to the prompt
    current_year = datetime.now().year
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
    
    current_date_str = datetime.now().strftime('%A, %d.%m.%Y')
    current_year_str = str(datetime.now().year)
    
    # --- PROMPT WITH YEAR ASSUMPTION ---
    prompt = f"""
    You are a professional travel auditor. Analyze this email.
    Today's Date: {current_date_str}.

    --- ANALYSIS RULES ---
    1. DATES: 
       - If the Month is missing (e.g., "Monday the 13th"): Mark as :red[❌ Dates: Missing Month].
       - If the Year is missing but Day/Month are present (e.g., "15th August"): ASSUME {current_year_str}. Mark as :green[✅ Dates: [Date] (Assumed {current_year_str})].
    
    2. PAX COUNT: 
       - Must be a specific number of people. 
       - If client only asks for vehicle price (e.g., "price for 8-seater") without saying "we are 8 people": Mark as :red[❌ Pax: Not specified].
    
    3. LOCATIONS: Specific cities or hotels required.
    4. VEHICLE: Preferred type.
    5. LUGGAGE: Amount/Type.
    6. DURATION: Hours/Days.
    7. EXTRAS: Guide/Stops.
    8. DRIVER: Meals/Accom.

    --- OUTPUT FORMAT ---
    1. PART 1: "📊 Analysis"
       - Use :green[✅ **[Requirement]**: [Details]] for met requirements.
       - Use :red[❌ **[Requirement]**: [Issue]] for missing items.
       - Put every point on a new line.

    2. PART 2: "✉️ Draft Reply"
       - Write a polite email asking ONLY for the items marked with ❌.
       - If everything is Green, draft a quote confirmation saying you will calculate the price shortly.

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
                st.markdown(result)
            else:
                st.error("Audit failed.")
                st.code(result)
