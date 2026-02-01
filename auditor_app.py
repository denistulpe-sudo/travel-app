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
    
    # --- PROMPT WITH STRICT TIME CHECK ---
    prompt = f"""
    You are a professional logistics auditor. Analyze this inquiry strictly against 7+1 requirements.
    Today's Date: {current_date_str}.

    --- REQUIREMENTS & LOGIC ---
    1. Dates and times: 
       - Rule: Must include EXACT Date AND EXACT Time.
       - Logic: 
         - If Time is missing (e.g. "May 14th" but no hour) -> :red[❌ Dates/Times: Specific pick-up time missing].
         - If Month missing -> :red[❌].
         - If Year missing -> :green[✅ (Assumed {current_year_str})].

    2. Number of passengers: 
       - Must be specific number. "8-seater" is NOT a pax count -> :red[❌].

    3. Pick-up and drop-off locations: 
       - Vague/Ambiguous -> :red[❌]. Specific -> :green[✅].

    4. Type of vehicle preferred: 
       - "Budget/Standard/Cheapest" -> :green[✅ Standard (Implied)]. No mention -> :red[❌].

    5. Luggage requirements: 
       - MANDATORY for Airport & City-to-City transfers. 
       - SKIP if "Shuttle" or "Sightseeing" (Contextual Intelligence).

    6. Service duration: 
       - Necessary for tours. Point-to-Point -> :green[✅ N/A].

    7. Additional needs: 
       - Guides, stops, child seats.

    8. Driver accommodation: 
       - Only for multi-day overnight trips. Short trip -> :green[✅ N/A].

    --- OUTPUT FORMAT ---
    PART 1: "📊 8-Point Logistics Audit"
    - Use a NUMBERED list (1., 2., 3.).
    - Structure: "1. [Green/Red Icon] **[Category Name]**: [Result]"

    ***SEPARATOR***

    PART 2: "✉️ Draft Reply"
    - Intro: "Dear Client,\n\nThank you for your inquiry."
    - Transition: "To provide you with an accurate quote, could you please clarify the following details:"
    - Body: List the questions for MISSING (:red[❌]) items.
    - STRICT LIST FORMAT: You must prefix the question with the category name.
      - GOOD: "- Pick-up time: Could you please specify the exact time you wish to depart?"
      - GOOD: "- Luggage requirements: Could you please specify the total number and size of luggage?"
    - Closing: "We look forward to hearing from you." (Do not add extra context).

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
        with st.spinner("Analyzing Dates & Times..."):
            status, result = audit_email(api_key, st.session_state["audit_input"])
            
            if status == "SUCCESS":
                st.success("Audit Complete")
                
                if "***SEPARATOR***" in result:
                    analysis_part, reply_part = result.split("***SEPARATOR***")
                    
                    st.markdown(analysis_part)
                    st.markdown("---")
                    st.subheader("✉️ Draft Reply")
                    
                    clean_reply = reply_part.replace('PART 2: "✉️ Draft Reply"', "").strip()
                    st.code(clean_reply, language=None)
                else:
                    st.markdown(result)
            else:
                st.error("Audit failed.")
                st.code(result)
