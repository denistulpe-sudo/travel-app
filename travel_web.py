import streamlit as st
import requests
import json

# --- PAGE SETUP ---
st.set_page_config(page_title="Travel Formatter", page_icon="✈️", layout="centered")
st.title("✈️ Travel Logistics Converter")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password", help="Paste your AIza... key here")
    st.info("If it fails, create a NEW key at aistudio.google.com")

# --- INPUT ---
raw_text = st.text_area("Paste text here:", height=150)

# --- DEBUGGING FUNCTION ---
def call_google_ai_debug(api_key, text):
    # We will try the standard model first
    model = "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    Task: Convert text into a strict "Pick-up / Drop-off" manifest.
    --- RULES ---
    1. HEADER: [DD.MM.YYYY], [Pax] pax, [Start City] (No times in header)
    2. FORMAT:
       - Pick-up [HH:MM] [Location] ([Flight])
       - Drop-off [Location] ([Flight])
       *[Notes/Luggage]
    3. CLEANUP: No bold text (**). 24h format.
    --- INPUT ---
    {text}
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        # Send request
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        # IF SUCCESS (200 OK)
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result:
                return "SUCCESS", result['candidates'][0]['content']['parts'][0]['text']
            else:
                return "ERROR", f"Google blocked the content. Raw response: {result}"
        
        # IF FAIL (400, 403, 404, 500)
        else:
            return "ERROR", f"Google Error Code: {response.status_code}\nMessage: {response.text}"

    except Exception as e:
        return "ERROR", f"Connection Failed: {str(e)}"

# --- BUTTON ---
if st.button("Convert Format", type="primary"):
    if not api_key:
        st.error("Please enter your API Key!")
    elif not raw_text:
        st.warning("Please enter text.")
    else:
        with st.spinner("Connecting to Google..."):
            status, result = call_google_ai_debug(api_key, raw_text)
            
            if status == "SUCCESS":
                st.success("Done!")
                # Clean bold text just in case
                clean_result = result.replace("**", "").replace("##", "")
                st.text_area("Result:", value=clean_result, height=300)
            else:
                # SHOW THE REAL ERROR
                st.error("Something went wrong!")
                st.code(result, language="json")
                st.warning("Please copy the error message above and send it to me.")
