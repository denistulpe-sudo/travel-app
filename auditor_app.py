import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Inquiry Auditor", page_icon="🔍", layout="centered")
st.title("🔍 Email Inquiry Auditor")
st.markdown("Scans for missing logistics and drafts a professional reply.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password")
    st.info(f"Current Year: {datetime.now().year}")

# --- INPUT ---
email_input = st.text_area("Paste the customer's email here:", height=300, placeholder="Dear Team, we need a bus...")

# --- FUNCTIONS ---
def find_working_model(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for model in data.get('models', []):
                if 'generateContent' in model.get('supportedGenerationMethods', []) and 'gemini' in model['name']:
                    return model['name']
        return "models/gemini-1.5-flash"
    except: return "models/gemini-1.5-flash"

def audit_email(api_key, text):
    model_name = find_working_model(api_key)
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    
    # THE AUDITOR PROMPT
    prompt = f"""
    You are a professional travel coordinator. 
    Analyze the email below and check for these 8 requirements:
    1. Exact dates and times.
    2. Number of passengers.
    3. Specific Pick-up/Drop-off locations (addresses, hotels, landmarks).
    4. Vehicle type preference (coach, minibus, luxury van, etc.).
    5. Luggage requirements (especially for airport transfers).
    6. Service duration (daily disposals or tours).
    7. Additional needs (guide, multiple stops, special requests).
    8. Driver accommodation & meals (if multi-day tour).

    --- TASK ---
    1. Identify what is MISSING from the 8 points above.
    2. Draft a polite professional response email.
    3. If dates/times/addresses are missing, use the phrase: "Could you please provide an exact itinerary, with dates, times, and location addresses?"
    4. If it is a day tour and hours are missing, include: "For day tours, I need to know how many hours per day you need the services."
    5. Use a helpful, professional tone.

    --- EMAIL TO AUDIT ---
    {text}
    """

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return "SUCCESS", result['candidates'][0]['content']['parts'][0]['text'].replace("**", "")
        else:
            return "ERROR", f"API Error: {response.text}"
    except Exception as e:
        return "ERROR", str(e)

# --- UI ---
if st.button("Audit & Draft Reply", type="primary"):
    if not api_key:
        st.error("Please enter your API Key!")
    elif not email_input:
        st.warning("Please paste an email first.")
    else:
        with st.spinner("Analyzing inquiry..."):
            status, result = audit_email(api_key, email_input)
            if status == "SUCCESS":
                st.success("Analysis Complete")
                st.markdown("### 📋 AI Analysis & Draft Response")
                st.write(result)
            else:
                st.error(f"Failed: {result}")
