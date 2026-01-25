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
    st.info(f"Today's Date: {datetime.now().strftime('%d.%m.%Y')}")
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
    
    # --- UPDATED "SKEPTICAL" PROMPT ---
    prompt = f"""
    Task: Convert travel text into a vertical logistics manifest.
    Year: {current_year}. 

    --- CRITICAL SAFETY RULES (ANTI-GUESSING) ---
    1. DATE: If the month is not explicitly mentioned (e.g., "Monday the 13th"), do NOT guess the month. Use ".MM." or "TBC" for the month (e.g., 13.MM.{current_year}).
    2. PAX: Do NOT assume the number of passengers based on the vehicle requested. If the email asks for "8-seat minivan prices," but doesn't say "we are 8 people," set Pax to "TBC".
    3. VEHICLE OPTIONS: If the client is asking for multiple pricing options, list them under the * bullet point at the bottom.
    4. NO CALCULATIONS: Use the times exactly as written.

    --- FORMAT RULES ---
    - Header: [DD.MM.YYYY], [Pax] pax, [Start City]
    - Lines: Every Pick-up and Drop-off on its own NEW line.
    - Notes: Every note or vehicle request on its own line starting with *.
    - Spacing: Double blank line between different dates.
    - No Bold: Do not use **.

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
        with st.spinner("Analyzing data (strictly)..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Manifest generated (No assumptions made)!")
                st.code(result, language=None)
            else:
                st.error("Failed.")
                st.code(result)
