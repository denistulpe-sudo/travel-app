import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Client -> Supplier Translator", page_icon="🚌", layout="centered")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password")
    st.divider()
    st.info("This tool extracts requests from client emails and reformats them for bus suppliers.")

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

def generate_supplier_email(api_key, client_text):
    model_path, api_version = get_available_model(api_key)
    if not model_path: return "ERROR", "API Key invalid or API disabled."

    url = f"https://generativelanguage.googleapis.com/{api_version}/{model_path}:generateContent?key={api_key}"
    
    # --- PROMPT: CLIENT -> SUPPLIER TRANSLATION ---
    prompt = f"""
    You are a professional logistics dispatcher for OsaBus.
    
    Task: Convert the following CLIENT REQUEST into a professional SUPPLIER INQUIRY.
    
    --- RULES ---
    1. TONE: Direct, professional, and operational. Remove all client "fluff" (e.g., "We are so excited", "My grandmother walks slowly").
    2. GOAL: Ask the supplier if the request is possible and what the EXTRA COST is.
    3. FORMATTING:
       - Start with "Hello Team," or "Dear Partners,"
       - State the request clearly: "The client has requested [Item/Service] for this trip."
       - Ask specific questions: "Can you provide this? What is the total cost?"
    4. MISSING INFO:
       - If the client doesn't specify a number (e.g., "water for everyone"), use a placeholder like [Number of Pax].
       - If the client doesn't specify a time, use [Time].
    5. LANGUAGE: Write the email in English (standard business English).

    --- EXAMPLES ---
    Input: "Can we have some water on the bus?"
    Output: "The client has requested bottled water for the passengers. Could you please provide this? If so, what would be the total cost for [Number] bottles?"

    Input: "We need to stop for 2 hours in Brno on the way."
    Output: "The client requests an additional 2-hour stop in Brno during the transfer. Is this possible with the current driver's hours? Please confirm the additional cost for this stop."

    --- CLIENT EMAIL INPUT ---
    {client_text}
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
    st.session_state["client_input"] = ""

# --- UI ---
st.title("🚌 Client-to-Supplier Translator")
st.markdown("Paste a client's request (e.g., extra stops, water, child seats), and I will draft a professional email to the bus company.")

client_input = st.text_area("Paste Client Request Here:", height=200, key="client_input")

col1, col2 = st.columns([1, 4])
with col1:
    st.button("Clear", on_click=clear_input)
with col2:
    translate_btn = st.button("Draft Supplier Email", type="primary")

if translate_btn:
    if not api_key: st.error("Please enter your API Key!")
    elif not client_input: st.warning("Please paste text.")
    else:
        with st.spinner("Drafting operational message..."):
            status, result = generate_supplier_email(api_key, client_input)
            
            if status == "SUCCESS":
                st.subheader("✉️ Message to Supplier")
                st.code(result, language=None)
                st.success("You can copy this directly into your dispatch email.")
            else:
                st.error("Error generating email.")
                st.code(result)
