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
    
    # --- PROMPT WITH LUGGAGE RULES ---
    prompt = f"""
    Task: Convert travel text into a vertical logistics manifest.
    Year: {current_year}. 

    --- CRITICAL FORMATTING RULES ---
    1. SEPARATION: Insert a DOUBLE EMPTY LINE between every transfer block.
    
    2. HEADER: [DD.MM.YYYY], [Pax] pax, [Specific Start Point]
       - If start is Munich Airport, write "Munich Airport".
    
    3. TIME (24H): Convert to 24h format (e.g. 19:35). Use "(Time TBC)" if unknown.

    4. PRESERVE IN-LINE NOTES: Keep suggestions like "(drop-off 2h before)" on the same line as the drop-off.

    5. LUGGAGE & EXTRAS (BOTTOM): 
       - Extract ALL requirements that are not time/location related (e.g., "Small hand luggage", "Child seat needed", "English speaking driver", "Water included").
       - Place them at the very bottom of the relevant transfer block.
       - Start each note with a single * symbol.
       - Example: * 20x Large Suitcases + 10x Carry-ons

    6. NO BOLD: Do not use **.

    --- EXPECTED OUTPUT FORMAT ---
    05.02.2026, 13 pax, Munich Airport
    - Pick-up 19:35 Munich Airport (Flight arrival 19:35)
    - Drop-off Lebenberg Schosshotel
    * Large luggage + Skis
    * Guide requested

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
        with st.spinner("Formatting manifest..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Formatted with Notes!")
                st.code(result, language=None)
            else:
                st.error("Failed.")
                st.code(result)
