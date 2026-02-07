import streamlit as st
import requests
import json

# --- PAGE SETUP ---
st.set_page_config(page_title="OsaBus Comm Translator", page_icon="↔️", layout="centered")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password")
    st.divider()
    st.info("↔️ **Two-Way Translator**\n\n**Tab 1:** Client -> Supplier (Direct).\n**Tab 2:** Supplier -> Client (Polite 'Planning Team').")

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
        # OPERATIONAL TONE (Direct)
        prompt = f"""
        You are a Logistics Dispatcher.
        Task: Convert this CLIENT REQUEST into a SUPPLIER INQUIRY.
        
        Input Text: "{input_text}"
        
        Rules:
        1. Tone: Direct, operational, concise.
        2. Goal: Ask if it's possible + Ask for cost.
        3. Structure:
           - Start: "Hello!"
           - Body: "The client has requested..."
           - Question: "Is this possible? What is the extra cost?"
           - End: "Looking forward to your response."
        """
        
    else: # supplier_to_client
        # POLITE "PLANNING TEAM" TONE (CONCISE)
        prompt = f"""
        You are a Customer Service Agent for OsaBus.
        Task: Convert this ROUGH UPDATE into a POLITE CLIENT EMAIL.
        
        Input Text: "{input_text}"
        
        Rules:
        1. IDENTITY PROTECTION (CRITICAL):
           - NEVER say "supplier", "driver", or "provider".
           - ALWAYS attribute decisions/info to "our planning team" ONLY.
           
        2. Tone: Polite, professional, but CONCISE. Do not write long paragraphs.
        
        3. Structure:
           - Start: "Dear Client,"
           - The Update: "Regarding your request... our planning team has informed us that..."
           - Next Step: "Please let us know if you would like to proceed."
           - End: "Best regards, OsaBus Team"
        """

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return "SUCCESS", result['candidates'][0]['content']['parts'][0]['text']
        else: return "ERROR", f"Google Error {response.status_code}"
    except Exception as e: return "ERROR", str(e)

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
    st.markdown("Use this when the supplier gives an answer (price, refusal, restrictions).")
    s_text = st.text_area("Supplier's Rough Reply:", height=150, key="s_input", 
                           placeholder="Example: 'No parking here. Police will fine me. Must be quick.'")
    
    if st.button("Draft Client Email", type="primary"):
        if not api_key: st.error("Add API Key in sidebar")
        elif not s_text: st.warning("Paste text first")
        else:
            with st.spinner("Drafting for Client (Using 'Planning Team' persona)..."):
                status, res = generate_translation(api_key, s_text, "supplier_to_client")
                if status == "SUCCESS":
                    st.text_area("Copy for Client:", value=res, height=250)
                else: st.error(res)
