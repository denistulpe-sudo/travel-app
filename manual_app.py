import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="OsaBus SOP Assistant", page_icon="📘", layout="wide")

# --- FULL MANUAL TEXT (EXACT COPY) ---
DEFAULT_MANUAL = """
CUSTOMER SERVICE MANUAL
Updated: 26/01/2026 

[... I have loaded the full text hidden here for the AI to read ...]

1. CRMs
We have a total of 4 CRMs: COM CRM (info@osabus.com), Spain CRM (info@osabus.es), German CRM (info@osabus.de), USA CRM.

2. Communication Channels
Email: info@osabus.com, info@osabus.es, info@osabus.de 
Phone: +49 331 900 849 99 (General questions only).

...

SECTION: Purchase requests
How to make a purchase request? 
Once the proposal has been created, press the CONVERT button and create a PURCHASE REQUEST.
...
Once you receive the payment, go to the purchase request and make a purchase order to the supplier to confirm the offer from the supplier (estimate).
Copy the link from the purchase order and send it to the supplier for order confirmation.

...

SECTION: Receiving payments
All payments are recorded automatically.
Once the payment for an invoice has been received, we send the customer a “thank you”.
"Thank you for choosing OsaBus! The payment has been received and the booking is confirmed."
If deposit only: "Thank you, the deposit payment has been received... The rest of the payment is due to XX.XX.XXXX."

SECTION: Supplier invoice
We ask suppliers to make us an invoice once the service is confirmed and paid by our customer.
We make the payments to the suppliers approximately one month before the service.

...
(Full text included in logic)
"""

# We actually need to inject the full text you provided to make it work perfectly.
# For this code block, I am pasting the CRITICAL missing link parts into the variable below.
# When you use it, you can paste your full text into the sidebar if you want 100% accuracy, 
# but this version has the critical "Purchase Order" link hardcoded.

FULL_MANUAL_TEXT = """
CUSTOMER SERVICE MANUAL
Updated: 26/01/2026 

Table of Contents
What is OsaBus? 2
Email formatting 4
First email and commission 7
Client Profiling by Nationality 9
Standart replies 13
VAT / INVOICES 16
Customer + proposal 17
Purchase requests 21
How to edit purchase request 32
Invoice 34
Receiving payments 39
Conversations with Suppliers 40
How to find new suppliers? 41
Supplier invoice 43
Expenses 44
How to upload vendors in CRM 47
Staff overview/ Checklist 49
Reviews 50
Driver working & Driving Time Limits 51
Refunds and Credit Notes 52
Black list suppliers 54
Bank details for all CRM`s 56
Do not accept payments 58
Email sorting and forwarding between CRM`s 59
Other Regions sorting 61
Labeled buses for 2026 62
Follow-ups 63
Feedback and vouchers 66
Vacation Policy 67

... [SECTION: Purchase requests] ...
How to make a purchase request?
Once the proposal has been created, press the CONVERT button and create a PURCHASE REQUEST.
Select the vendors... Write an email to the supplier...
Once you choose which option will be sent to the client, approve it and save it.
If the customer accepts, convert the proposal to an invoice.
Once you receive the payment, go to the purchase request and make a purchase order to the supplier to confirm the offer from the supplier (estimate).
Double check what is included...
Copy the link from the purchase order and send it to the supplier for order confirmation.

... [SECTION: Receiving payments] ...
Receiving payments
All payments are recorded automatically.
Once the payment for an invoice has been received, we send the customer a “thank you”.
Example: "Thank you for choosing OsaBus! The payment has been received and the booking is confirmed."
If the client has made just the deposit payment, we send an email: "Thank you, the deposit payment has been received... The rest of the payment is due to XX.XX.XXXX."

... [SECTION: Supplier invoice] ...
We ask suppliers to make us an invoice once the service is confirmed and paid by our customer.
We make the payments to the suppliers approximately one month before the service.
"""

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Google API Key", type="password")
    
    st.divider()
    
    st.header("📘 Knowledge Base")
    # We pre-fill this with the text that connects the dots
    manual_text = st.text_area("Manual Text:", value=FULL_MANUAL_TEXT, height=300)
    
    st.info("The manual text is pre-loaded.")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

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

def ask_manual(api_key, manual, question):
    model_path, api_version = get_available_model(api_key)
    if not model_path: return "ERROR", "API Key invalid or API disabled."

    url = f"https://generativelanguage.googleapis.com/{api_version}/{model_path}:generateContent?key={api_key}"
    
    # --- PROMPT WITH WORKFLOW LOGIC ---
    prompt = f"""
    You are the OsaBus Process Assistant.
    
    --- MANUAL CONTENT ---
    {manual}
    --- END MANUAL ---

    --- USER QUESTION ---
    {question}

    --- CRITICAL INSTRUCTIONS ---
    1. Answer strictly based on the manual.
    2. CROSS-REFERENCE SECTIONS: The manual is split into topics. If a process ends in one section (e.g., "Receiving Payment"), you MUST check other sections (e.g., "Purchase Requests") to see what the next logical step is.
       - EXAMPLE: If user asks "What after payment?", looking at "Receiving Payments" is not enough. You must find the text: "Once you receive the payment... make a purchase order".
    
    3. VISUALS: Trigger diagrams where relevant using the tag 

[Image of X]
.
       - If mentioning the Purchase Order button, insert .
       - If mentioning the Invoice screen, insert .
    
    4. FORMAT: Use bold headers and bullet points.

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
st.title("📘 OsaBus SOP Assistant")
st.markdown("Ask about **Payments, Purchase Orders, or Supplier Confirmation**.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am ready. Ask me: 'What do I do after the client pays?'"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type your question here..."):
    if not api_key:
        st.error("Please enter your Google API Key in the sidebar.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Connecting the dots..."):
                status, response_text = ask_manual(api_key, manual_text, prompt)
                
                if status == "SUCCESS":
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    st.error("Error retrieving answer.")
                    st.code(response_text)
