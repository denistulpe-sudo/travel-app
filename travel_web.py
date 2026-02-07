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
    
    # --- PROMPT WITH TBC TIME & ASTERISK EXTRAS ---
    prompt = f"""
    Task: Convert travel text into a vertical logistics manifest.
    Current Year: {current_year}. 

    --- CRITICAL RULES ---
    1. HEADER FORMAT: [DD.MM.YYYY], [Pax] pax, [CITY/TOWN NAME ONLY]
       - If year is missing in text, use {current_year}.
       - Do NOT invent addresses.

    2. TRANSFER LINES (Use Hyphens -):
       - Format: "- Pick-up [Time] [Location]"
       - Format: "- Drop-off [Location]"
       
    3. TIME RULES (Strict):
       - If a specific time is given, convert to 24h (e.g., 15:30).
       - If NO time is given, strictly write "TBC". 
       - NEVER invent a time like "09:00" if it is not in the text.

    4. EXTRAS & LUGGAGE (Use Asterisks *):
       - Place all additional info (Luggage, Flight numbers, Guides, Notes) at the bottom of the specific transfer block.
       - Prefix these lines with an asterisk (*).
       - Example: "* Large luggage included"

    5. SEPARATION: Insert a DOUBLE EMPTY LINE between every transfer block.

    --- EXPECTED OUTPUT EXAMPLE ---
    06.04.2026, 14 pax, Lille
    - Pick-up 15:30 Lille Europe train station
    - Drop-off Holiday Inn Marne La Vallee
    * Arriving on Eurostar
    * 14 suitcases + 14 carry-ons

    10.05.2026, 5 pax, Riga
    - Pick-up TBC Radisson Blu Latvija
    - Drop-off Riga Airport
    * Flight BT102

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
        with st.spinner("Formatting (TBC Times & * Extras)..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Formatted!")
                st.code(result, language=None)
            else:
                st.error("Failed.")
                st.code(result)
