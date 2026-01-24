import streamlit as st
import requests
import json
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="Travel Formatter", page_icon="✈️", layout="centered")
st.title("✈️ Travel Logistics Converter")
st.caption("Auto-detects the best Google Model for your Key.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password", help="Paste your AIza... key here")
    st.info("If errors persist, create a NEW key at aistudio.google.com")

# --- INPUT ---
raw_text = st.text_area("Paste messy email/text here:", height=200, placeholder="Example: 26/03/26 18 pax Kaunas to Vilnius...")

# --- FUNCTIONS ---
def find_working_model(api_key):
    """Asks Google which models are available."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        # INCREASED TIMEOUT TO 30 SECONDS
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            for model in data.get('models', []):
                if 'generateContent' in model.get('supportedGenerationMethods', []) and 'gemini' in model['name']:
                    return model['name']
        return None
    except:
        return None

def call_google_ai_auto(api_key, text):
    # 1. FIND MODEL
    model_name = find_working_model(api_key)
    
    if not model_name:
        model_name = "models/gemini-pro"
    
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"

    # 2. SEND REQUEST
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    You are a travel logistics assistant.
    Task: Convert text into a strict "Pick-up / Drop-off" manifest.

    --- RULES ---
    1. HEADER: [DD.MM.YYYY], [Pax] pax, [Start City]
       - Do NOT put times in the header.
    
    2. IF DETAILS ARE KNOWN (Specific Hotels/Times):
       - Line 1: "- Pick-up [HH:MM] [Location] ([Flight Info])"
       - Line 2: "- Drop-off [Location] ([Flight Info])"
       - Line 3: "*[Luggage info or Notes]"
       
       *Note: If specific pickup time is missing, just write "- Pick-up [Location]".*
       *Note: Put Flight Arrival/Departure info inside parenthesis at the end of the line.*

    3. IF DETAILS ARE UNKNOWN (Vague request):
       - Just write "Addresses, Times: TBC" under the header.
       - Then list the cities with hyphens.

    4. CLEANUP:
       - No bold text (**). 
       - Convert 12h times to 24h (21:45).
       - Group strictly by date.

    --- INPUT TEXT ---
    {text}
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        # INCREASED TIMEOUT TO 60 SECONDS (This is the fix!)
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result:
                clean_text = result['candidates'][0]['content']['parts'][0]['text']
                clean_text = clean_text.replace("**", "").replace("##", "")
                return "SUCCESS", clean_text, model_name
            else:
                return "ERROR", f"Blocked response. Raw: {result}", model_name
        else:
            return "ERROR", f"Google Error {response.status_code}: {response.text}", model_name

    except Exception as e:
        return "ERROR", f"Connection Failed: {str(e)}", "Unknown"

# --- INTERFACE ---
if st.button("Convert Format", type="primary"):
    if not api_key:
        st.error("Please enter your API Key!")
    elif not raw_text:
        st.warning("Please enter text.")
    else:
        with st.spinner("Finding best model & converting (might take 20s)..."):
            status, result, used_model = call_google_ai_auto(api_key, raw_text)
            
            if status == "SUCCESS":
                st.success(f"Success! (Model: {used_model})")
                st.text_area("Result:", value=result, height=450)
            else:
                st.error(f"Failed using model: {used_model}")
                st.code(result)
