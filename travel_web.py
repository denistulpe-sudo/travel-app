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
    st.info(f"Today: {datetime.now().strftime('%d.%m.%Y')}")
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
    
    # --- PROMPT WITH NOTE PRESERVATION ---
    prompt = f"""
    Task: Convert travel text into a vertical logistics manifest.
    Year: {current_year}. 

    --- CRITICAL RULES ---
    1. TIME FORMAT (24H ONLY): 
       - Convert ALL times to 24-hour format (e.g., 5pm -> 17:00).
    
    2. PRESERVE SUGGESTIONS (CRITICAL): 
       - If the client includes a note or question in brackets like "(drop-off 1.5/2h before?)" or "(estimated)", you MUST keep that text exactly as written at the end of the line. 
       - DO NOT delete client notes.

    3. DUPLICATION: If a date has multiple service times, create a completely separate Pick-up/Drop-off block for each time.
    
    4. FLIGHT INFO: Place flight info ONLY on the Airport line.
       - Pick-up [Time] [Airport] (Flight arrival [Time])
       - Drop-off [Airport] (Flight departure [Time])

    5. STRUCTURE: 
       - Header: [DD.MM.YYYY], [Pax] pax, [Start City]
       - Lines: "- Pick-up..." and "- Drop-off..." must be on separate lines.
       - Spacing: Double empty line between dates.
    
    6. NO GUESSING: If month is missing, use "TBC". If pax is missing, use "TBC".
    
    7. NO BOLD: Do not use **.

    --- EXAMPLE OUTPUT ---
    07.02.2026, 4 pax, Kitzbuhel
    - Pick-up 14:00 Lebenberg Schosshotel
    - Drop-off Munich Airport (Flight 17:00) (drop-off 1.5/2h before?)

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
        with st.spinner("Formatting (Preserving notes + 24h)..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Formatted!")
                st.code(result, language=None)
            else:
                st.error("Failed.")
                st.code(result)
