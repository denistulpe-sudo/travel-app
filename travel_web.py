import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Travel Formatter Minimal", page_icon="🚐", layout="centered")

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
    
    # --- MINIMALIST VERTICAL PROMPT ---
    prompt = f"""
    Task: Convert travel text into a vertical manifest.
    Year: {current_year}. 

    --- STRICT RULES ---
    1. NO CALCULATIONS: Do not subtract or add time. Use the times provided in the text.
    2. NOTES: If the client provides suggestions like "(drop-off 1.5/2h before?)", keep that text EXACTLY. 
    3. VERTICALITY: 
       - Header on its own line.
       - Every "- Pick-up" on its own line.
       - Every "- Drop-off" on its own line.
       - Empty line between different dates.
    4. HEADER: [DD.MM.YYYY], [Total Pax] pax, [Start City]
    5. NO BOLD: Do not use any ** symbols.
    6. CLEANLINESS: No extra "AI chatter" or explanations like "calculated as...".

    --- EXAMPLE OUTPUT ---
    05.02.2026, 23 pax, Munich Airport
    - Pick-up 19:35 Munich Airport
    - Drop-off Lebenberg Schosshotel, Kitzbuhel

    07.02.2026, 4 pax, Kitzbuhel
    - Pick-up Lebenberg Schosshotel
    - Drop-off Munich Airport (Flight 19:30) (drop-off 1.5/2h before?)

    --- INPUT ---
    {text}
    """

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            output = result['candidates'][0]['content']['parts'][0]['text']
            # Final cleanup to force verticality if the AI fails
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
        with st.spinner("Formatting..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Itinerary generated!")
                # Using st.code ensures line breaks are strictly respected and copyable
                st.code(result, language=None)
            else:
                st.error("Failed.")
                st.code(result)
