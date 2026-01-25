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
    
    current_date_str = datetime.now().strftime('%A, %d.%m.%Y')
    current_year_str = str(datetime.now().year)
    
    # --- PROMPT WITH FORMATTING RULES ---
    prompt = f"""
    You are a professional travel auditor. Analyze this email.
    Today's Date: {current_date_str}.

    --- ANALYSIS RULES ---
    1. DATES: Missing Month -> :red[❌]. Missing Year -> :green[✅ (Assumed {current_year_str})].
    2. PAX: "8-seater" is NOT a pax count -> :red[❌].
    3. LOCATION: Vague/Ambiguous -> :red[❌]. Specific -> :green[✅].
    4. VEHICLE: "Budget" implies Standard -> :green[✅].
    5. DRIVER ACCOM: Short trip -> :green[✅ N/A].

    --- OUTPUT FORMATTING ---
    PART 1: "📊 8-Point Analysis"
    - You must list the 8 requirements vertically, numbered 1 to 8.
    - Structure: "1. [Green/Red Icon] **[Requirement Name]**: [Result]"
    
    PART 2: "✉️ Draft Reply"
    - Subject Line: Short and relevant (e.g. "Re: Transfer Request - [Location]").
    - Opening: KEEP IT SHORT. Do NOT summarize the full details. 
      - BAD: "Thank you for your request for 18 people from A to B on Date X..."
      - GOOD: "Dear Client,\n\nThank you for your transfer request."
    - Body: Ask ONLY for the items marked with :red[❌]. 
    - Tone: Helpful and professional.

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
        with st.spinner("Analyzing requirements..."):
            status, result = audit_email(api_key, st.session_state["audit_input"])
            if status == "SUCCESS":
                st.success("Audit Complete")
                st.markdown(result)
            else:
                st.error("Audit failed.")
                st.code(result)
