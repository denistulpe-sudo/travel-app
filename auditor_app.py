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
    current_year = datetime.now().year
    
    # --- PROMPT WITH SPLIT DATE/TIME LOGIC ---
    prompt = f"""
    You are a professional logistics auditor. Analyze this inquiry STRICTLY against 8 requirements.
    Today's Date: {current_date_str}.
    Current Year: {current_year}.

    --- STRICT ANALYSIS RULES ---
    1. Dates and Times: 
       - Rule: Must include Day, Month, and Hour.
       - Logic (Year): If Year missing -> Assume next occurrence ({current_year} or {current_year + 1}). Mark as :green[✅].
       - Logic (Time): 
         - If Dates are present but TIME is missing -> :red[❌ Pick-up Times: Specific time missing].
         - If Dates AND Time are missing -> :red[❌ Dates & Times: Missing].
         - If valid -> :green[✅ Dates & Times: Specific].

    2. Number of Passengers: 
       - Rule: Must be a specific number.
       - Logic: "30 students + 3 profs" = 33 pax -> :green[✅].
       - "Group" or "Bus needed" -> :red[❌ Number of passengers: Exact count missing].

    3. Pick-up and Drop-off Locations: 
       - Rule: Must be a specific Hotel Name, Airport, or Address.
       - Logic: "Hotel Ibis Tallin" -> :green[✅].
       - "Hotel in Riga" -> :red[❌ Locations: Specific hotel name missing].

    4. Type of Vehicle Preferred: 
       - Rule: Must specify type (Van, Sedan) or Class.
       - Logic: If omitted -> :red[❌ Type of vehicle: Not specified].

    5. Luggage Requirements: 
       - Rule: Mandatory for Airport & City-to-City transfers.
       - Logic: If missing -> :red[❌ Luggage requirements: Count/Size missing].

    6. Service Duration: 
       - Rule: Mandatory for Hourly Disposal/Tours.
       - Logic: Point-to-Point transfers -> :green[✅ N/A (Transfer)].

    7. Additional Needs: 
       - Rule: Check for Guides, Child Seats.

    8. Driver Accommodation: 
       - Rule: Check for Multi-day Overnight trips.

    --- OUTPUT FORMAT ---
    PART 1: "📊 8-Point Logistics Audit"
    - Use a NUMBERED list (1., 2., 3.).
    - Structure: "1. [Green/Red Icon] **[Category Name]**: [Result]"

    ***SEPARATOR***

    PART 2: "✉️ Draft Reply"
    - Intro: "Dear Client,\n\nThank you for your inquiry."
    - Transition: "To provide you with an accurate quote, could you please clarify the following details:"
    - Body: List questions for MISSING (:red[❌]) items.
    - DYNAMIC CATEGORIES:
      - If only TIME is missing, write: "- Pick-up Times: Could you please specify the exact pick-up times for..."
      - Do NOT write "Dates and Times" if the dates are already there.
    - Closing: "We look forward to hearing from you."

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
        with st.spinner("Auditing..."):
            status, result = audit_email(api_key, st.session_state["audit_input"])
            
            if status == "SUCCESS":
                st.success("Audit Complete")
                
                if "***SEPARATOR***" in result:
                    analysis_part, reply_part = result.split("***SEPARATOR***")
                    
                    # 1. Analysis Part
                    st.markdown(analysis_part)
                    
                    st.markdown("---")
                    st.subheader("✉️ Draft Reply")
                    
                    # 2. Reply Part (Clean code block)
                    clean_reply = reply_part.replace('PART 2: "✉️ Draft Reply"', "").strip()
                    st.code(clean_reply, language=None)
                else:
                    st.markdown(result)
            else:
                st.error("Audit failed.")
                st.code(result)
