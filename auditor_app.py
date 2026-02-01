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
    
    # --- PROMPT WITH STRICT LUGGAGE CONTEXT ---
    prompt = f"""
    You are a professional logistics auditor. Analyze this inquiry strictly against 8 requirements.
    Today's Date: {current_date_str}.

    --- 1. DATES & TIMES ---
    - Rule: Must be exact.
    - Logic: 
      - If Month missing -> :red[❌ Dates: Missing Month].
      - If Year missing -> :green[✅ Dates: (Assumed {current_year_str})].

    --- 2. PASSENGER COUNT ---
    - Rule: Must be a specific number.
    - Logic: "8-seater" or "Large bus" is NOT a pax count. Mark as :red[❌ Pax: Not specified] if only vehicle is mentioned.

    --- 3. LOCATIONS ---
    - Rule: Specific addresses or searchable landmarks.
    - Logic: "Hotel in City Center" is Vague (:red[❌]). "Radisson Blu Riga" is Specific (:green[✅]).

    --- 4. VEHICLE PREFERENCE ---
    - Rule: Explicit or Implied.
    - Logic: "Budget/Standard/Cheapest" -> :green[✅ Vehicle: Standard (Implied)]. No mention -> :red[❌ Vehicle: Type not specified].

    --- 5. LUGGAGE (CONTEXTUAL INTELLIGENCE) ---
    - Rule: Confirming luggage is mandatory for safety/weight, EXCEPT in 3 cases.
    - Logic:
      1. GREEN :green[✅]: If client explicitly stated count/size (e.g., "small bags only").
      2. GREEN :green[✅]: If "Shuttle" service (Hotel <-> Restaurant/Gala/Conference) where luggage is impossible.
      3. GREEN :green[✅]: If "Day Sightseeing" (Loop tour starting/ending at same hotel).
      4. RED :red[❌]: ALL Airport transfers (MANDATORY).
      5. RED :red[❌]: ALL City-to-City transfers (MANDATORY).

    --- 6. DURATION ---
    - Rule: Necessary for tours/disposals.
    - Logic: If Point-to-Point transfer -> :green[✅ N/A (Transfer)]. If Tour -> Check hours.

    --- 7. EXTRAS ---
    - Rule: Check for guides, stops, child seats.

    --- 8. DRIVER ACCOMMODATION ---
    - Rule: Only for multi-day overnight trips.
    - Logic: Short trip/One day -> :green[✅ N/A (Short trip)]. Overnight -> Check if included.

    --- OUTPUT FORMAT ---
    PART 1: "📊 8-Point Logistics Audit"
    - List the 8 points vertically, numbered 1 to 8.
    - Use format: "1. [Green/Red Icon] **[Requirement Name]**: [Result]"

    PART 2: "✉️ Draft Reply"
    - Subject: Short & Professional (e.g. "Re: Transport Request").
    - Intro: "Dear Client,\n\nThank you for your inquiry." (No summary).
    - Body: Ask ONLY for the :red[❌] items. 
    - Logic: Do NOT ask for luggage if it is marked Green. Do NOT ask for Driver Accom if it is a short trip.

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
        with st.spinner("Analyzing logistics & Context..."):
            status, result = audit_email(api_key, st.session_state["audit_input"])
            if status == "SUCCESS":
                st.success("Audit Complete")
                st.markdown(result)
            else:
                st.error("Audit failed.")
                st.code(result)
