import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Travel Formatter Pro", page_icon="🚐", layout="centered")

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

def call_google_ai(api_key, text):
    model_path, api_version = get_available_model(api_key)
    if not model_path: return "ERROR", "API Key invalid or API disabled."

    url = f"https://generativelanguage.googleapis.com/{api_version}/{model_path}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    current_year = datetime.now().year
    
    # --- DUPLICATION PROMPT ---
    prompt = f"""
    Task: Convert travel text into a vertical logistics manifest.
    Year: {current_year}. 

    --- STRIKTIE NOTEIKUMI (STRICT RULES) ---
    1. DUPLICATE FOR DIFFERENT TIMES: If a date has multiple flight/service times (e.g., 17:00 and 20:00), you MUST create a completely separate block of lines for each time. 
       - DO NOT use commas to list times (e.g., No "17:00, 20:00").
       - REPEAT the "- Pick-up" and "- Drop-off" lines for every single time found.
    
    2. TWO LINES PER TRIP: Every single transfer must consist of exactly:
       - One line starting with "- Pick-up"
       - One line starting with "- Drop-off"

    3. HEADER: [DD.MM.YYYY], [Total Pax for that date] pax, [Start City]
    
    4. NOTES: Keep suggestions like "(drop-off 1.5/2h before?)" exactly as written next to the relevant time.
    
    5. VERTICALITY: Every single element must be on a new line. 
    
    6. SPACING: Add a double blank line between different dates.

    --- EXAMPLE OF DUPLICATION ---
    08.02.2026, 19 pax, Kitzbuhel
    - Pick-up Lebenberg Schosshotel
    - Drop-off Munich Airport (Flight 17:00) (drop-off 1.5/2h before?)

    - Pick-up Lebenberg Schosshotel
    - Drop-off Munich Airport (Flight 20:00) (drop-off 1.5/2h before?)

    --- INPUT ---
    {text}
    """

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            output = result['candidates'][0]['content']['parts'][0]['text']
            return "SUCCESS", output.replace("**", "").strip()
        else: return "ERROR", f"Google Error {response.status_code}"
    except Exception as e: return "ERROR", str(e)

def clear_text_area():
    st.session_state["main_input"] = ""

# --- UI ---
st.title("🚐 Travel Route Formatter")

raw_text = st.text_area("Paste email here:", height=300, key="main_input")

col1, col2 = st.columns([1, 4])
with col1:
    st.button("Clear Text", on_click=clear_text_area)
with col2:
    process_btn = st.button("Format Now", type="primary")

if process_btn:
    if not api_key: st.error("Please enter your API Key!")
    elif not st.session_state["main_input"]: st.warning("Please paste text.")
    else:
        with st.spinner("Processing duplicated time blocks..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Itinerary generated!")
                st.code(result, language=None)
            else:
                st.error("Failed.")
                st.code(result)
