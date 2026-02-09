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
    
    # --- PROMPT: CLEAN DATES + GLOBAL SUMMARY ---
    prompt = f"""
    Task: Convert travel text into a LOGISTICS ITINERARY with a CONSOLIDATED SUMMARY.
    Current Year: {current_year} (Use this if year is missing).

    --- PART 1: DATE BLOCKS (Keep these CLEAN) ---
    For every date mentioned, generate ONLY:
    1. HEADER: [DD.MM.YYYY], [Pax] pax, [Start City] – [Dest City] ([Return/One-way])
    2. TIMELINE: 
       - Format: -[HH:MM]: [Action] – [Location]
       - If no specific time, use "-" without a time.
    
    CRITICAL RULE FOR DATES: Do NOT put *Vehicle, *Notes, or *Price inside the date blocks. Keep them strictly for movements.

    --- PART 2: TRIP SUMMARY (At the very bottom, ONCE) ---
    After all dates are listed, add a separator "--- TRIP DETAILS ---" and list:
    
    *Vehicles: [Summarize total vehicle needs for the whole trip. E.g., "1x Bus (40 pax) for Team 2, 1x Bus (35 pax) for Team 1"].
    *Notes: [Consolidate ALL warnings, flight info, TBCs, and team split details here].
    *Price Request: [Summarize the costing request].

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
        with st.spinner("Formatting (Global Summary)..."):
            status, result = call_google_ai(api_key, st.session_state["main_input"])
            if status == "SUCCESS":
                st.success("Formatted!")
                st.text_area("Result:", value=result, height=400)
            else:
                st.error("Failed.")
                st.code(result)
