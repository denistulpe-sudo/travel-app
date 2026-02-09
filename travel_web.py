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
    
    # --- PROMPT: STRICT MANIFEST FORMATTER ---
    prompt = f"""
    You are a strict Logistics Data Extractor. 
    Task: Convert the input text into a vertical logistics manifest.
    Current Year: {current_year}. 

    --- CRITICAL RULES (NO HALLUCINATIONS) ---
    1. DATES: 
       - Extract dates strictly. If year is missing, assume {current_year}.
       - Format: [DD.MM.YYYY]
    
    2. TIMES (STRICT):
       - If a specific time is written (e.g., "14:00", "2pm"), write it.
       - If NO time is written, you MUST write "TBC". 
       - If vague text is used (e.g., "Morning"), write "TBC (Morning)".
       - NEVER invent a time like "09:00" or "12:00" if it is not explicitly in the text.

    3. HEADER FORMAT: 
       - [DD.MM.YYYY], [Pax] pax, [Main City/Location]

    4. ACTION LINES (Use Hyphens -):
       - Format: "- Pick-up [Time] [Location]"
       - Format: "- Drop-off [Location]"
       - Format: "- Stop [Time] [Location]" (For lunches/visits)
       - Do not omit any stops mentioned in the text.

    5. EXTRAS (Use Asterisks *):
       - Capture ALL additional details found in the text for that specific day.
       - Include: Flight numbers, Luggage counts, Contacts, Special requests (Walkers, Child seats), Vehicle types requested.
       - Format: "* [Detail]"

    6. SEPARATION: 
       - Insert a DOUBLE EMPTY LINE between every date block.

    --- EXPECTED OUTPUT EXAMPLE ---
    06.04.2026, 14 pax, Lille
    - Pick-up 15:30 Lille Europe train station
    - Drop-off Holiday Inn Marne La Vallee
    * Arriving on Eurostar ES9010
    * 14 suitcases + 14 carry-ons

    10.05.2026, 5 pax, Riga
    - Pick-up TBC Radisson Blu Latvija
    - Drop-off Riga Airport
    * Flight BT102 departing at 18:00
    * Client requests water on board

    --- INPUT TEXT ---
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
        with st.spinner("Formatting (Strict Logic)..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Formatted!")
                st.code(result, language=None)
            else:
                st.error("Failed.")
                st.code(result)
