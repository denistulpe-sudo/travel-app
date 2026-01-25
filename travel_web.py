import streamlit as st
import requests
import json
from datetime import datetime

# --- LAPAS KONFIGURĀCIJA ---
st.set_page_config(page_title="Travel Formatter", page_icon="🚐", layout="centered")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password")
    st.info(f"Current Year: {datetime.now().year}")

# --- FUNCTIONS ---
def get_available_model(api_key):
    # Pārbauda pieejamos modeļus (v1 un v1beta)
    for version in ["v1", "v1beta"]:
        url = f"https://generativelanguage.googleapis.com/{version}/models?key={api_key}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Prioritāte gemini-1.5-flash, ja nav - ņemam pirmo Gemini
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
    
    # --- STIPRI UZLABOTS PROMPT ---
    prompt = f"""
    You are a logistics dispatcher. Convert travel text into a VERTICAL list.
    
    Current Year is {current_year}. If the year is missing in text, use {current_year}.
    
    --- STRIKTIE NOTEIKUMI ---
    1. HEADER: [DD.MM.YYYY], [Pax] pax, [Start City]
    2. PICK-UP LINE: Start with a hyphen "- ". Then "Pick-up [24h Time] [Location]".
    3. DROP-OFF LINE: Start with a hyphen "- ". Then "Drop-off [Location]".
    4. FLIGHT INFO: ONLY add flight info in brackets () if it exists. If no flight mentioned, DO NOT write empty brackets ().
    5. VERTICAL LAYOUT: Every bullet point MUST be on a NEW LINE.
    6. SPACING: Add one empty line between different dates.
    7. NO BOLD: Do not use **.
    
    --- PIEMĒRS ---
    23.06.2026, 20 pax, Glasgow
    - Pick-up 10:00 Glasgow Airport (Arrival 09:30)
    - Drop-off Leonardo Hotel, Belfast
    *Small hand luggage
    
    --- IEVADE ---
    {text}
    """

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            output = result['candidates'][0]['content']['parts'][0]['text']
            # Python līmeņa tīrīšana
            clean_output = output.replace("**", "").replace("##", "").strip()
            return "SUCCESS", clean_output
        else:
            return "ERROR", f"Google Error {response.status_code}"
    except Exception as e:
        return "ERROR", str(e)

# --- UI ---
st.title("🚐 Travel Route Formatter")
raw_text = st.text_area("Paste messy email here:", height=200)

if st.button("Format Now", type="primary"):
    if not api_key:
        st.error("Please enter your API Key!")
    elif not raw_text:
        st.warning("Please enter text.")
    else:
        with st.spinner("Processing..."):
            status, result = call_google_ai(api_key, raw_text)
            if status == "SUCCESS":
                st.success("Done!")
                # Lietojam st.code, lai saglabātu rindu pārejas un būtu vieglāk kopēt
                st.code(result, language=None)
            else:
                st.error("Failed.")
                st.code(result)
