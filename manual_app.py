import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="OsaBus SOP Assistant", page_icon="📘", layout="wide")

# --- FULL MANUAL TEXT ---
# I have prioritized the "Invoice" section text here to ensure the AI sees it first.
FULL_MANUAL_TEXT = """
CUSTOMER SERVICE MANUAL
Updated: 26/01/2026 

SECTION: Invoice (Client Accepted Proposal)
Once the client accepts the proposal, we receive a notification in our CRM. 
IMMEDIATE ACTION: We ask the client for details so we can prepare the invoice.
To prepare the invoice, please share the following details (Send this template to client):
- Method of payment: Credit Card checkout (+3% transaction fee) /or/ Bank Transfer
- Name / Company name:
- Legal address:
- Arrival details (Flight numbers, times):
- VAT number / Tax Number / Personal Code:
- Contact phone number with the country code in front:
- Contact person name:

Once the details are received:
1. Update the customer details in the CRM profile (Address, VAT, etc.).
2. Go to the proposal section -> Open accepted proposal -> Convert to Invoice.
3. Select payment option (Bank Transfer or Stripe).
4. Fill in Group details, Driver details, Flight details.
5. Save and Send the invoice link to the customer.

SECTION: Purchase requests
(Internal Step - Can happen in parallel or before confirming invoice, but Client Data is priority)
To make a purchase request:
1. Open Proposal -> Convert -> Purchase Request.
2. Select Vendors -> Save.
3. Copy Link -> Email Supplier (Subject: Proposal Number).
4. Once Supplier quotes -> Approve best quote.
5. Update Proposal price (Quote + 15% commission).

SECTION: Purchase Order (After Payment)
Once you receive payment (Full or Deposit):
1. Go to Purchase Request.
2. Make a PURCHASE ORDER to the supplier.
3. Send the Purchase Order Link to the supplier to confirm.

SECTION: Receiving payments
1. Payment recorded automatically (Status: Paid).
2. Send "Thank You" email:
   - Full Pay: "Thank you for choosing OsaBus! The payment has been received and the booking is confirmed."
   - Deposit: "Thank you, the deposit payment has been received... Rest due [Date]."

SECTION: Supplier invoice
We ask suppliers to make us an invoice once the service is confirmed and paid by our customer.
We make payments to suppliers approx 1 month before service.

SECTION: Commission Guidelines
- Regular: 20-25%
- Travel pros: 15%
- High risk: 25-35%
- Asia: 20-30%
"""

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Google API Key", type="password")
    
    st.divider()
    
    st.header("📘 Knowledge Base")
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
    
    # --- PROMPT WITH WORKFLOW CORRECTION ---
    prompt = f"""
    You are the OsaBus Process Assistant.
    
    --- MANUAL CONTENT ---
    {manual}
    --- END MANUAL ---

    --- USER QUESTION ---
    {question}

    --- CRITICAL INSTRUCTIONS ---
    1. Answer strictly based on the manual.
    2. CORRECT WORKFLOW for "Proposal Accepted":
       - Step 1: Request Invoice Details from Client. (DO NOT skip to Purchase Requests yet).
         - Provide the EXACT LIST of details to ask (Method of payment, VAT, etc.).
       - Step 2: Update Client Profile in CRM.
       - Step 3: Convert Proposal to Invoice.
       - Step 4: Send Invoice.
    
    3. FORMAT: Use bold headers and bullet points.

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
st.markdown("Ask about **Invoices, Payments, or Next Steps**.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! Ask me: 'Client accepted the proposal, what now?'"}]

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
            with st.spinner("Checking manual..."):
                status, response_text = ask_manual(api_key, manual_text, prompt)
                
                if status == "SUCCESS":
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    st.error("Error retrieving answer.")
                    st.code(response_text)
