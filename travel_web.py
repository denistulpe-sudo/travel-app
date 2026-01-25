import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Travel Master Tool", page_icon="🚐", layout="centered")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password")
    st.info(f"Current Year: {datetime.now().year}")

# --- FUNCTIONS ---
def get_available_model(api_key):
    """Pārbauda, kuri modeļi ir pieejami šai atslēgai."""
    # Mēģinām gan v1, gan v1beta versijas
    for version in ["v1beta", "v1"]:
        url = f"https://generativelanguage.googleapis.com/{version}/models?key={api_key}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for m in data.get('models', []):
                    # Meklējam Gemini modeļus, kas atbalsta satura ģenerēšanu
                    if 'gemini' in m['name'] and 'generateContent' in m['supportedGenerationMethods']:
                        return m['name'], version
        except:
            continue
    return None, None

def call_google_ai(api_key, text):
    # 1. Atrodam strādājošu modeli
    model_path, api_version = get_available_model(api_key)
    
    if not model_path:
        return "ERROR", "API Key invalid or 'Generative Language API' not enabled in Google Cloud Console."

    # 2. Sagatavojam pieprasījumu
    url = f"https://generativelanguage.googleapis.com/{api_version}/{model_path}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    current_year = datetime.now().year
    prompt = f"""
    Task: Convert text into a strict "Pick-up / Drop-off" manifest.
    Rules: 
    - Header: [DD.MM.YYYY], [Pax] pax, [Start City]
    - Lines: - Pick-up [HH:MM] [Location] ([Flight]). - Drop-off [Location].
    - Year: If missing, use {current_year}.
    - No bold text. 24h format.
    
    Input: {text}
    """

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            output = result['candidates'][0]['content']['parts'][0]['text']
            return "SUCCESS", output.replace("**", "")
        else:
            return "ERROR", f"Google Error {response.status_code}: {response.text}"
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
        with st.spinner("Searching for available AI model..."):
            status, result = call_google_ai(api_key, raw_text)
            if status == "SUCCESS":
                st.success("Formatted successfully!")
                st.text_area("Result:", value=result, height=400)
            else:
                st.error("Failed to connect.")
                st.code(result)
