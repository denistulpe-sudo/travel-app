import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="OsaBus Comm Translator", page_icon="↔️", layout="centered")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password")
    st.divider()
    st.info("🔄 Two-Way Translator\n\nTab 1: Ask Supplier for things.\nTab 2: Give bad/good news to Client.")

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

def generate_translation(api_key, input_text, mode):
    model_path, api_version = get_available_model(api_key)
    if not model_path: return "ERROR", "API Key invalid or API disabled."

    url = f"https://generativelanguage.googleapis.com/{api_version}/{model_path}:generateContent?key={api_key}"
    
    # --- PROMPTS ---
    if mode == "client_to_supplier":
        # OPERATIONAL TONE
        prompt = f"""
        You are a Logistics Dispatcher.
        Task: Convert this CLIENT REQUEST into a SUPPLIER INQUIRY.
        
        Input Text: "{input_text}"
        
        Rules:
        1. Tone: Direct, operational, "Business-to-Business".
        2. Goal: Ask if it's possible + Ask for cost.
        3. Structure:
           - Start: "Hello!"
           - Body: "The client has requested..."
           - Question: "Is this possible? What is the extra cost?"
           - End: "Looking forward to your response." / "Best regards,"
        """
        
    else: # supplier_to_client
        # POLITE CUSTOMER SERVICE TONE
        prompt = f"""
        You are a Customer Service Agent for OsaBus.
        Task: Convert this ROUGH SUPPLIER UPDATE into a POLITE CLIENT EMAIL.
        
        Input Text: "{input_text}"
        
        Rules:
        1. Tone: Very polite, professional, apologetic (if bad news), helpful.
        2. Goal: Inform the client clearly without sounding rude or blaming the driver.
        3. Structure:
           - Start: "Dear Client,"
           - Context: "Regarding your request for..."
           - The Update: Rephrase the supplier's text nicely.
             - Example: "Driver says no" -> "Unfortunately, the transport provider has informed us that this request cannot be accommodated."
             - Example: "50 euro extra" -> "The transport provider can arrange this for an additional fee of 50 EUR."
           - Next Step: "Please let us know if you would like to proceed."
           - End: "Best regards," / "OsaBus Team"
        """

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return "SUCCESS", result['candidates'][0]['content']['parts'][0]['text']
        else: return "ERROR", f"Google Error {response.status_code}"
    except Exception as e: return "ERROR", str(e)

def clear_input():
    st.session_state["input_text"] = ""

# --- UI ---
st.title("↔️ OsaBus Comm Translator")

# TABS FOR MODES
tab1, tab2 = st.tabs(["Client ➡ Supplier", "Supplier ➡ Client"])

# --- TAB 1: CLIENT TO SUPPLIER ---
with tab1:
    st.markdown("Use this when the client asks for weird stuff (water, stops, decorations).")
    c_input = st.text_area("Client's Request:", height=150, key="c_input")
    
    if st.button("Draft Supplier Email", type="primary"):
        if not api_key: st.error("Add API Key in sidebar")
        elif not c_input: st.warning("Paste text first")
        else:
            with st.spinner("Translating to Dispatch-Speak..."):
                status, res = generate_translation(api_key, c_input, "client_to_supplier")
                if status == "SUCCESS":
                    st.text_area("Copy for Supplier:", value=res, height=250)
                else: st.error(res)

# --- TAB 2: SUPPLIER TO CLIENT ---
with tab2:
    st.markdown("Use this when the supplier replies with short/rude text.")
    s_input = st.text_area("Supplier's Rough Reply:", height=150, key="s_input", 
                           placeholder="Example: 'No water. Driver busy. Extra stop 50 eur.'")
    
    if st.button("Draft Client Email", type="primary"):
        if not api_key: st.error("Add API Key in sidebar")
        elif not s_input: st.warning("Paste text first")
        else:
            with st.spinner("Polishing for Client..."):
                status, res = generate_translation(api_key, s_input, "supplier_to_client")
                if status == "SUCCESS":
                    st.text_area("Copy for Client:", value=res, height=250)
                else: st.error(res)
