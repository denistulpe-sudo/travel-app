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
    
    # --- PROMPT: SMART DATE PARSING ---
    prompt = f"""
    Task: Convert travel text into a detailed LOGISTICS ITINERARY.
    Current Year: {current_year} (Use this if year is missing).

    --- CRITICAL RULES ---
    1. DATE CONVERSION (The most important rule):
       - Detect dates written in ANY format (e.g., "21st February", "Feb 21", "23th March", "next Monday").
       - Convert them STRICTLY to [DD.MM.YYYY] format.
       - Example: "21st Feb" -> "21.02.{current_year}"
       - Example: "Monday 23th March" -> "23.03.{current_year}"

    2. HEADER FORMAT: 
       - [DD.MM.YYYY], [Pax] pax, [Start City] – [Dest City] ([Return/One-way])
       
    3. TIMELINE:
       - List ONLY specific actions and times found in the text.
       - Format: -[HH:MM]: [Action] – [Location]
       - If a timeframe is given (e.g. 09:00-19:00), list the start and end as separate actions.
    
    4. NO GUESSING:
       - Do NOT guess vehicle type. Write: "*Vehicle: For [Pax] pax".
       - Do NOT add adjectives unless in text.
       
    5. EXTRAS (Asterisks *):
       - *Storage: [Copy specific text regarding luggage/walkers].
       - *Price Request: [Copy specific text regarding cost].
       - *Notes: [Any other constraints].

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
        with st.spinner("Formatting Itinerary..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Formatted!")
                st.text_area("Result:", value=result, height=400)
            else:
                st.error("Failed.")
                st.code(result)
