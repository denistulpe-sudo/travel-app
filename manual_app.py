import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="OsaBus Process Assistant", page_icon="📘", layout="wide")

# --- INTERNAL MANUAL (PRE-LOADED) ---
# This is the text you provided. You can update it here in the code if policies change.
DEFAULT_MANUAL = """
CUSTOMER SERVICE MANUAL
Updated: 26/01/2026 

1. CRMs
We have a total of 4 CRMs:
COM CRM: info@osabus.com (Latvia, Netherlands, General)
Spain CRM: info@osabus.es (Spain)
German CRM: info@osabus.de (Germany)
USA CRM: Used for proposals and invoices in USD (USA, Asia, LatAm)

2. Communication Channels
Email: info@osabus.com, info@osabus.es, info@osabus.de 
Phone: +49 331 900 849 99 (General questions only. No consultations/changes via phone).

3. Email Formatting
- Use standard fonts. No emojis.
- Subject line, Greeting, Body, Sign-off.
- Use "Reply All" if client CC'd others. 
- Do NOT "Reply All" if other bus companies are CC'd.
- No ALL CAPS.

4. Commission Guidelines
- Regular: 20–25%
- Travel professionals: 15%
- High risk (Weddings/Stag): 25–35%
- Long tours (5+ days): 10%
- Last-minute: 20–50%
- USA/Canada: 10–20%
- Minimum profit: €50

5. VAT / INVOICES RULES
- General Rule: All proposals start with 0% VAT in COM CRM.
- Latvia Service (COM CRM): 21% VAT.
- Spain Service (SPAIN CRM): Spanish VAT.
- Germany Service (DE CRM): 19% VAT.
- Netherlands Service (COM CRM): 9% VAT.
- Private Individual (EU Registered): Apply VAT of service country.
- Company (EU Registered): 0% VAT (Reverse Charge).
- Non-EU Client: 0% VAT.

6. Creating a Proposal (CRM Steps)
1. Check if customer exists. If new (WordPress email), create new customer.
2. Go to Proposals -> New Proposal.
3. Add item details (dates, pax, luggage, start location).
4. Subject: Start day + City.
5. Save. Proposal stays in DRAFT until supplier quote is received.

7. Purchase Requests (Sourcing Suppliers)
1. Inside Proposal, click CONVERT -> PURCHASE REQUEST.
2. Select Vendors based on city/pax.
3. Save (Do not "Save and Send" yet).
4. Copy the "Vendor Link".
5. Email supplier from operations1@osagroup.ltd with the link.
6. When supplier quotes, approve the best quote in the system.
7. Update proposal price based on approved quote + 15% margin.

8. Invoicing
1. Update Customer Details (VAT, Address, Group type).
2. Convert Proposal -> Invoice.
3. Select Payment: Stripe (+3% fee) or Bank Transfer.
4. Fill in: Dispo number, Driver details, Flight info.
5. Save and Send to customer.
6. Payment terms: 30% deposit, balance 48 days prior.

9. Supplier Invoices & Expenses
1. Open the Client Invoice.
2. Click MORE -> ADD EXPENSE.
3. Select Vendor.
4. Enter Amount and Upload Supplier Invoice.
5. Status: Ready for Payment.
6. Email zane.cunska@connect2trip.com with the expense link.

10. Refund Policy
- Requires Credit Note.
- Refund fee for credit cards: €35 (covered by client).
- Send details (IBAN, SWIFT) to Zane.

11. Blacklisted Suppliers
(Do not use: Vienna Connection Cab, Global bus rental, Eg Reisen, Zonetransfers, etc - refer to full list in manual).

12. Email Sorting
- Germany internal -> DE CRM.
- Spain internal -> SPAIN CRM.
- Everything else -> COM CRM.
- USA CRM handles: USA, Asia, Latin America, Middle East.

13. Reviews
- Minimum 2 reviews/month per agent.
- Bonus: €10 per extra review.

14. Driver Hours
- Max drive/day: 9h (ext to 10h twice/week).
- Max work/day: 12h (ext to 15h).
- Break: 45min after 4.5h driving.

15. Vacation Policy
- Min 2 weeks/year (1 week summer, 1 week winter).
- Restricted: April, May, June, September.
"""

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Google API Key", type="password")
    
    st.divider()
    
    st.header("📘 Knowledge Base")
    with st.expander("View/Edit Manual Text"):
        manual_text = st.text_area("Current Manual:", value=DEFAULT_MANUAL, height=300)
    
    st.info("The app is pre-loaded with the OsaBus Customer Service Manual (Updated 26/01/2026).")
    
    if st.button("Clear Chat History"):
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
    
    # --- PROMPT ---
    prompt = f"""
    You are the OsaBus Process Assistant. You have access to the official 'CUSTOMER SERVICE MANUAL'.
    
    --- USER MANUAL CONTENT ---
    {manual}
    --- END MANUAL ---

    --- USER QUESTION ---
    {question}

    --- INSTRUCTIONS ---
    1. Answer strictly based on the manual.
    2. Provide STEP-BY-STEP instructions.
    3. VISUALS: If the step involves using the CRM, specific forms, or looking at a specific document, INSERT A VISUAL TAG like  or  at the relevant step.
    4. REFERENCE: Mention the Section Name (e.g., "See Section 'VAT / INVOICES'").
    5. If the answer is not in the manual, say "I cannot find this in the OsaBus manual."

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
st.markdown("Ask questions about **Invoices, VAT, CRM Steps, or Supplier Policies**.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I have the OsaBus manual memorized. How can I help you today? (e.g., 'How do I add an expense?' or 'What is the VAT for a trip in Germany?')"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Type your question here..."):
    if not api_key:
        st.error("Please enter your Google API Key in the sidebar.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Checking the manual..."):
                status, response_text = ask_manual(api_key, manual_text, prompt)
                
                if status == "SUCCESS":
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    st.error("Error retrieving answer.")
                    st.code(response_text)
