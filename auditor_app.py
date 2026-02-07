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
    
    # --- PROMPT WITH SMART CONTEXT & CONCISE REPLY ---
    prompt = f"""
    You are a professional logistics auditor. Analyze this inquiry.
    Today's Date: {current_date_str}.
    Current Year: {current_year}.

    --- ANALYSIS RULES (STRICT AUDIT VS PRAGMATIC REPLY) ---
    
    1. Dates & Times:
       - Logic: Dates present but Time missing? -> Audit: :red[❌ Pick-up Time]. Reply: ASK.
       - Logic: Dates missing? -> Audit: :red[❌ Dates]. Reply: ASK.

    2. Passenger Count (Smart Logic):
       - Exact ("30 pax") -> Audit: :green[✅]. Reply: SKIP.
       - Estimate ("up to 10", "approx 15") -> Audit: :orange[⚠️ Estimated]. Reply: SKIP (Do not ask, unless completely missing).
       - Missing ("Group", "Bus needed") -> Audit: :red[❌]. Reply: ASK.

    3. Locations:
       - Logic: Specific Hotel/Address -> :green[✅].
       - Logic: Vague ("Hotel in Riga") -> :red[❌ Specific Address]. Reply: ASK.

    4. Vehicle:
       - Logic: Explicit or Implied (Budget/Standard) -> :green[✅]. Missing -> :red[❌]. Reply: ASK.

    5. Luggage (Contextual Skip):
       - ASK IF: Airport Transfer, City-to-City, Multi-day Tour.
       - SKIP IF: Dinner transfer, Wedding shuttle, School day trip, Nightlife/Party.
       - Logic: If context suggests "Dinner/Wedding/School/Party" -> Audit: :green[✅ N/A (Context)]. Reply: SKIP.

    6. Itinerary/Stops (Contextual Skip):
       - ASK IF: Sightseeing Tour, "Disposal" service.
       - SKIP IF: Point-to-Point Transfer, Airport Transfer, Shuttle Loop.

    7. Flight Numbers:
       - ASK IF: Airport Pick-up.
       - SKIP IF: Airport Drop-off, Train Station, City Transfer.

    8. Driver Accommodation:
       - ASK IF: Multi-day tour away from base city.
       - SKIP IF: Single-day service (Start/End same day), Local transfers (even if multi-day).

    --- OUTPUT FORMAT ---
    PART 1: "📊 Logistics Audit"
    - List the status of requirements using :green[✅], :orange[⚠️], :red[❌].
    - Be brief.

    ***SEPARATOR***

    PART 2: "✉️ Draft Reply"
    - Tone: Professional, polite, but VERY CONCISE.
    - Rule: Do not write long paragraphs. 
    - Intro: "Dear Client,\n\nThank you for your inquiry."
    - Body: "To provide an accurate quote, could you please clarify:"
    - List: Bullet points ONLY for the :red[❌] items (and :red[❌] Time).
    - EXCEPTION: Do NOT ask for "Passengers" if Audit is :orange[⚠️ Estimated].
    - EXCEPTION: Do NOT ask for "Luggage" if Context is Dinner/Wedding/School.
    - Closing: "Best regards,"

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
st.markdown("Highlights met requirements in :green[Green], estimates in :orange[Orange], missing in :red[Red].")

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
        with st.spinner("Analyzing Logistics & Context..."):
            status, result = audit_email(api_key, st.session_state["audit_input"])
            
            if status == "SUCCESS":
                st.success("Audit Complete")
                
                if "***SEPARATOR***" in result:
                    analysis_part, reply_part = result.split("***SEPARATOR***")
                    
                    # 1. Analysis Part
                    st.markdown(analysis_part)
                    
                    st.markdown("---")
                    st.subheader("✉️ Draft Reply")
                    
                    # 2. Reply Part
                    clean_reply = reply_part.replace('PART 2: "✉️ Draft Reply"', "").strip()
                    st.code(clean_reply, language=None)
                else:
                    st.markdown(result)
            else:
                st.error("Audit failed.")
                st.code(result)
