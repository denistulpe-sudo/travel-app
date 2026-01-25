import streamlit as st
import requests
import json
from datetime import datetime

# --- LAPAS KONFIGURĀCIJA ---
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
    
    # --- PROMPT AR SUGGESTED TIME LOGIKU ---
    prompt = f"""
    You are a professional logistics dispatcher. Convert the travel request into a strict manifest.
    Current Year: {current_year}.

    --- TIME CALCULATION RULES ---
    1. DEPARTURES: Look for "flight departure" or "catching a flight". 
       - If the client suggests a buffer (e.g., "drop-off 2h before"), CALCULATE the Pick-up time based on that suggestion PLUS travel time (assume travel time is ~1h if cities are different).
       - If no suggestion is given, subtract 3 hours from flight time to get the Pick-up time.
       - Always mention the calculated buffer in brackets, e.g., (Pick-up calculated as 2.5h before flight).

    2. ARRIVALS: Pick-up time = Flight arrival time.

    --- FORMAT RULES ---
    1. EVERY transfer = exactly TWO lines: "- Pick-up" and "- Drop-off".
    2. HEADER: [DD.MM.YYYY], [Total Pax for that date] pax, [Start City]
    3. SUGGESTIONS: If the client made a specific note (like "drop-off 2h before"), include it at the end of the line in brackets.
    4. VERTICALITY: New line for every point. Empty line between different dates.
    5. NO BOLD: Do not use **.

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
st.title("🚐 Travel Route Formatter Pro")

raw_text = st.text_area("Paste messy email here:", height=300, key="main_input")

col1, col2 = st.columns([1, 4])
with col1:
    st.button("Clear Text", on_click=clear_text_area)
with col2:
    process_btn = st.button("Format Now", type="primary")

if process_btn:
    if not api_key: st.error("Please enter your API Key!")
    elif not st.session_state["main_input"]: st.warning("Please paste text.")
    else:
        with st.spinner("Analyzing suggestions and formatting..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Itinerary generated with suggested buffers!")
                st.code(result, language=None)
            else:
                st.error("Failed.")
                st.code(result)
