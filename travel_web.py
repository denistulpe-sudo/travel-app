import streamlit as st
import requests
import json

# --- LAPAS KONFIGURĀCIJA ---
st.set_page_config(page_title="Travel Formatter", page_icon="✈️", layout="centered")

# --- VIRSRAKSTS ---
st.title("✈️ Travel Logistics Converter")
st.markdown("Convert messy emails into **Pick-up/Drop-off** manifests.")

# --- SĀNU JOSLA (API ATSLĒGAI) ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password", help="Paste your AIza... key here")
    st.info("Your key is safe. It is not stored anywhere.")

# --- IEVADE ---
raw_text = st.text_area("Paste the messy email/text here:", height=200, placeholder="Example: 26/03/26 18 pax Kaunas to Vilnius...")

# --- FUNKCIJAS ---
def call_google_ai(api_key, text):
    # Gudrā "Self-healing" loģika, lai atrastu strādājošu modeli
    models_to_try = ["gemini-1.5-flash", "gemini-pro", "gemini-1.5-flash-001"]
    
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        # --- TAVS PĒDĒJAIS, VISLABĀKAIS PROMPT ---
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
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                clean_text = result['candidates'][0]['content']['parts'][0]['text']
                # Noņemam bold simbolus
                return clean_text.replace("**", "").replace("##", "")
        except:
            continue # Mēģinām nākamo modeli
            
    return "Error: Could not connect to Google API. Check your Key."

# --- POGA UN REZULTĀTS ---
if st.button("Convert Format", type="primary"):
    if not api_key:
        st.error("Please enter your API Key in the sidebar!")
    elif not raw_text:
        st.warning("Please enter some text to convert.")
    else:
        with st.spinner("Processing with AI..."):
            result = call_google_ai(api_key, raw_text)
            
            st.success("Conversion Complete!")
            st.text_area("Result:", value=result, height=300)
            st.caption("You can copy the text above.")