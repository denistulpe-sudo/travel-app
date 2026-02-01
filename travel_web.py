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
    
    # --- PROMPT WITH CLEAN CITY HEADERS ---
    prompt = f"""
    Task: Convert travel text into a vertical logistics manifest.
    Year: {current_year}. 

    --- CRITICAL FORMATTING RULES ---
    1. SYMBOLS: Use ONLY hyphens (-) for lists. Do NOT use * or •.

    2. HEADER FORMAT (City Only): 
       - Format: [DD.MM.YYYY], [Pax] pax, [CITY/TOWN NAME ONLY]
       - Do NOT put the specific hotel or station name in the header.
       - BAD: 06.04.2026, 14 pax, Lille Europe Train Station
       - GOOD: 06.04.2026, 14 pax, Lille
       - GOOD: 11.04.2026, 14 pax, Paris (or Marne La Vallee)

    3. SEPARATION: 
       - Insert a DOUBLE EMPTY LINE between every transfer block.
       - This is critical to prevent text squashing.

    4. TIME (24H): 
       - Convert 3.30pm -> 15:30. 12pm -> 12:00.

    5. LINES: 
       - Pick-up and Drop-off must be on separate lines starting with a hyphen -.
       - Include the Specific Name here (e.g. "- Pick-up 15:30 Lille Europe...").

    6. NOTES & LUGGAGE: 
       - Keep client notes (e.g. "arriving on Eurostar") in brackets on the same line.
       - Extract luggage/extras to the bottom of the block with a hyphen -.

    --- EXPECTED OUTPUT ---
    06.04.2026, 14 pax, Lille
    - Pick-up 15:30 Lille Europe train station (arriving on the Eurostar)
    - Drop-off Holiday Inn Express Marne La Vallee

    11.04.2026, 14 pax, Paris
    - Pick-up 12:00 Newport Bay Disney Hotel
    - Drop-off Lille Europe train station

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
        with st.spinner("Formatting (City Headers + 24h)..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Formatted!")
                st.code(result, language=None)
            else:
                st.error("Failed.")
                st.code(result)
