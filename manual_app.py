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
    st.info("↔️ Two-Way Translator\n\nTab 1: Client -> Supplier (Operational)\nTab 2: Supplier -> Client (Pro Solutions)")

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
        # PRO LOGISTICS PROBLEM SOLVER
        prompt = f"""
        You are a Senior Logistics Manager for OsaBus.
        Task: Synthesize the Supplier's constraint into a Professional Client Solution.
        
        Input Text (from Supplier): "{input_text}"
        
        --- CRITICAL RULES ---
        1. IDENTITY: 
           - NEVER say "supplier", "driver", or "provider". 
           - Attribution: "Our planning team", "Local traffic regulations", "City authorities".
        
        2. PROBLEM SOLVING (The "Split Scenario" Logic):
           - If supplier says "No parking" or "Can't stop" -> Explain it as "Strict local traffic regulations".
           - If supplier says "I will get a fine" -> Explain it as "Police monitor this area closely".
           - If supplier offers a bad alternative (walking far) -> Mention it as a last resort, but prioritize the "Quick Stop" solution.

        3. STRUCTURE & TONE:
           - Start: "Dear Client,"
           - Confirmation: Confirm the time/date first.
           - The "Constraint": Explain WHY there is an issue (Rules/Safety).
           - The "Solution": Use Bullet Points to tell them how to handle it (e.g., "Be ready 5 mins early", "Active boarding only").
           - End: "Best regards, OsaBus Team"

        --- EXAMPLE TRAINING ---
        Input: "No parking at Riva. Only 1 minute stop or police fine. Other parking is 150eur extra."
        Output: "Regarding the location on the Riva: Local traffic regulations are very strict. Minibuses are permitted to stop for only one minute for active boarding. To ensure a smooth departure: 1. Please ensure the group is ready at the curb. 2. The driver will pull up exactly at the scheduled time."
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
    st.session_state["c_input"] = ""
    st.session_state["s_input"] = ""

# --- UI ---
st.title("↔️ OsaBus Comm Translator")

# TABS
tab1, tab2 = st.tabs(["Client ➡ Supplier", "Supplier ➡ Client"])

# --- TAB 1: CLIENT TO SUPPLIER ---
with tab1:
    st.markdown("Use this when the client asks for extra items/stops.")
    c_text = st.text_area("Client's Request:", height=150, key="c_input")
    
    if st.button("Draft Supplier Email", type="primary"):
        if not api_key: st.error("Add API Key in sidebar")
        elif not c_text: st.warning("Paste text first")
        else:
            with st.spinner("Drafting for Dispatch..."):
                status, res = generate_translation(api_key, c_text, "client_to_supplier")
                if status == "SUCCESS":
                    st.text_area("Copy for Supplier:", value=res, height=250)
                else: st.error(res)

# --- TAB 2: SUPPLIER TO CLIENT ---
with tab2:
    st.markdown("Use this when the supplier mentions **restrictions, fines, or timing issues**.")
    s_text = st.text_area("Supplier's Explanation:", height=150, key="s_input", 
                           placeholder="Example: 'No parking here. Police will fine me. Must be quick.'")
    
    if st.button("Draft Client Email", type="primary"):
        if not api_key: st.error("Add API Key in sidebar")
        elif not s_text: st.warning("Paste text first")
        else:
            with st.spinner("Formulating Logistics Solution..."):
                status, res = generate_translation(api_key, s_text, "supplier_to_client")
                if status == "SUCCESS":
                    st.text_area("Copy for Client:", value=res, height=250)
                else: st.error(res)
