import streamlit as st
import requests
import json
import time
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Travel Formatter", page_icon="✈️", layout="centered")
st.title("✈️ Travel Logistics Converter")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password")
    st.info(f"Current Year: {datetime.now().year}")

# --- INPUT ---
raw_text = st.text_area("Paste messy email/text here:", height=200)

# --- FUNCTIONS ---
def call_google_ai_stable(api_key, text):
    # Mēs mēģināsim šos trīs modeļus pēc kārtas. 
    # Ja pirmais neiet, automātiski mēģinās nākamo.
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    current_year = datetime.now().year
    
    prompt = f"""
    You are a travel logistics assistant.
    Task: Convert text into a strict "Pick-up / Drop-off" manifest.
    Current Year: {current_year} (Use this if year is missing).

    --- RULES ---
    1. HEADER: [DD.MM.YYYY], [Pax] pax, [Start City]
    2. FORMAT:
       - Pick-up [HH:MM] [Location] ([Flight Info])
       - Drop-off [Location] ([Flight Info])
       *[Luggage info or Notes]
    3. CLEANUP: No bold text (**). Convert 12h to 24h.
    
    --- INPUT TEXT ---
    {text}
    """

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                clean_text = result['candidates'][0]['content']['parts'][0]['text']
                return "SUCCESS", clean_text.replace("**", ""), model
            elif response.status_code == 429:
                return "RATE_LIMIT", "Too many requests. Please wait 15 seconds.", model
        except:
            continue
            
    return "ERROR", "All models failed. Check your API key and permissions.", "None"

# --- INTERFACE ---
if st.button("Convert Format", type="primary"):
    if not api_key:
        st.error("Please enter your API Key!")
    elif not raw_text:
        st.warning("Please enter text.")
    else:
        with st.spinner("Processing..."):
            status, result, used_model = call_google_ai_stable(api_key, raw_text)
            
            if status == "SUCCESS":
                st.success(f"Success! (Model: {used_model})")
                st.text_area("Result:", value=result, height=400)
            elif status == "RATE_LIMIT":
                st.warning(result)
            else:
                st.error(result)
