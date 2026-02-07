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
    1. TONE: Direct, professional, and operational. Remove all client "fluff".
    2. GOAL: Ask the supplier if the request is possible and what the EXTRA COST is.
    3. STRUCTURE:
       - Start with: "Hello!" or "Hello Team,"
       - Body: State the request clearly (e.g., "The client has requested...").
       - Question: "Is this possible? What is the total extra cost?"
       - End with: "Looking forward to your response." followed by "Best regards,"
    4. UNKNOWNS:
       - If numbers/times are missing, use placeholders like [Number] or [Time].
    5. FORMAT: Use standard paragraphs (no code blocks).

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
st.markdown("Paste the client's request below. I will rewrite it for the bus company.")

client_input = st.text_area("Paste Client Request Here:", height=150, key="client_input")

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
                # Using text_area instead of code block ensures text wraps and doesn't scroll sideways
                st.text_area("Copy this text:", value=result, height=250)
                st.success("Draft ready! You can edit the text above before copying.")
            else:
                st.error("Error generating email.")
                st.write(result)
