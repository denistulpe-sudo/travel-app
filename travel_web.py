import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Travel Formatter", page_icon="🚐", layout="centered")

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
                models = [m['name'] for m in data.get('models', []) if 'gemini' in m['name'] and 'generateContent' in m['supportedGenerationMethods']]
                for m in models:
                    if "1.5-flash" in m: return m, version
                if models: return models[0], version
        except: continue
    return None, None

def call_google_ai(api_key, text):
    model_path, api_version = get_available_model(api_key)
    if not model_path:
        return "ERROR", "API Key invalid or 'Generative Language API' disabled."

    url = f"https://generativelanguage.googleapis.com/{api_version}/{model_path}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    current_year = datetime.now().year
    prompt = f"""
    You are a logistics dispatcher. Convert travel text into a VERTICAL list.
    Current Year is {current_year}. If the year is missing in text, use {current_year}.
    
    --- RULES ---
    1. HEADER: [DD.MM.YYYY], [Pax] pax, [Start City]
    2. PICK-UP LINE: Start with "- Pick-up [24h Time] [Location]".
    3. DROP-OFF LINE: Start with "- Drop-off [Location]".
    4. FLIGHT INFO: ONLY in brackets () if it exists.
    5. VERTICAL: Every point on a NEW LINE. Empty line between different dates.
    6. NO BOLD: Do not use **.
    
    Input: {text}
    """

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            output = result['candidates'][0]['content']['parts'][0]['text']
            return "SUCCESS", output.replace("**", "").strip()
        else:
            return "ERROR", f"Google Error {response.status_code}"
    except Exception as e:
        return "ERROR", str(e)

# --- CLEAR LOGIC ---
# This function now specifically targets the widget key "main_input"
def clear_text_area():
    st.session_state["main_input"] = ""

# --- UI ---
st.title("🚐 Travel Route Formatter")

# The text_area is linked to the key "main_input"
raw_text = st.text_area("Paste messy email here:", 
                        height=250, 
                        key="main_input")

col1, col2 = st.columns([1, 4])

with col1:
    # Clicking this calls the clear function and then reruns the app
    st.button("Clear Text", on_click=clear_text_area)

with col2:
    process_btn = st.button("Format Now", type="primary")

if process_btn:
    if not api_key:
        st.error("Please enter your API Key!")
    elif not st.session_state["main_input"]:
        st.warning("Please paste text.")
    else:
        with st.spinner("Processing..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Done!")
                st.code(result, language=None)
            else:
                st.error("Failed.")
                st.code(result)
