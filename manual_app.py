import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="OsaBus SOP Assistant", page_icon="📘", layout="wide")

# --- FULL INTERNAL MANUAL ---
# This contains the EXACT text you provided.
DEFAULT_MANUAL = """
CUSTOMER SERVICE MANUAL
Updated: 26/01/2026 

1. CRMs
We have a total of 4 CRMs:
COM CRM: info@osabus.com (General)
Spain CRM: info@osabus.es
German CRM: info@osabus.de
USA CRM: Used for proposals and invoices in USD

2. Communication Channels
Email: info@osabus.com, info@osabus.es, info@osabus.de 
Phone: +49 331 900 849 99 (General questions only. No consultations/changes via phone).

3. Email Formatting
- Use standard fonts. No emojis.
- Subject line, Greeting, Body, Sign-off.
- Use "Reply All" if client CC'd others (except other bus companies).
- No ALL CAPS.

4. Commission Guidelines
- Regular: 20–25%
- Travel professionals: 15%
- Weddings / Sports teams / Bachelor parties / High-risk bookings: 25–35%
- Long tours (5+ days): 10%
- Last-minute requests: 20–50% (consult manager)
- Asia: 20–30% + inform clients of currency exchange differences
- USA/Canada: 10–20% due to high rates
- Minimum profit: €50 for small deals (applies to all countries)

5. VAT / INVOICES
General Rule (Always Start Here)
- All proposals are initially created with 0% VAT in COM CRM.
- VAT is reviewed and applied only at the invoicing stage.
- Proposals/invoices in SPAIN CRM and DE CRM are always issued with VAT according to local rules.

Where the Service Takes Place (CRM & VAT):
- Latvia → Use COM CRM → 21% VAT
- Spain → Use SPAIN CRM → Apply Spanish VAT
- Germany → Use DE CRM → 19% VAT
- Netherlands → COM CRM → 9% VAT
- COM CRM Rules:
  - Legal entity (company) → 0% VAT
  - Private individual, EU registered → Apply VAT of the service country
  - Private individual, NOT EU registered → 0% VAT

6. Purchase Requests (Sourcing)
- Once proposal created -> Press CONVERT -> PURCHASE REQUEST.
- Select vendors based on city/pax.
- Save (Do not "Save and Send").
- Copy the link.
- Email supplier from operations1@osagroup.ltd with the link.
- Subject: Proposal number + Subject.
- Once supplier quotes, approve the best quote in system.
- Update proposal price (Quote + 15% commission usually).

7. Purchase Order (CONFIRMING SUPPLIER)
- Once you receive payment from client, go to the Purchase Request.
- Make a PURCHASE ORDER to the supplier to confirm the offer.
- Check details (flight number, etc).
- Copy the Purchase Order link and email it to the supplier for confirmation.

8. Invoicing & Receiving Payments
- Convert Proposal to Invoice.
- Payment Options: Bank Transfer (Preferred) or Credit Card (+3% fee).
- Fill in Group details, Driver details, Flight details.
- Terms: Full payment required. 30% deposit to secure, balance 48 days prior.

RECEIVING PAYMENTS (What to do next):
- Payments are recorded automatically (Status changes to "Paid").
- Send "Thank You" email to client:
  "Thank you for choosing OsaBus! The payment has been received and the booking is confirmed. The driver's details will be provided the evening before the trip."
- If only Deposit paid:
  "Thank you, the deposit payment has been received, and the booking is confirmed. The rest of the payment is due to XX.XX.XXXX." (Update invoice due date).

9. Supplier Invoices & Expenses
- We pay suppliers approx 1 month before service (or 20-30% deposit if requested).
- Open Client Invoice -> More -> Add Expense.
- Select Vendor.
- Enter Amount & Upload Supplier Invoice.
- Status: Ready for Payment.
- Email zane.cunska@connect2trip.com with the expense link.

10. Refund Policy
- Requires Credit Note.
- Create Credit Note in system.
- Send details (IBAN, SWIFT) to Zane.
- Credit Card refund fee: €35 (covered by client).

11. Blacklisted Suppliers
(Do not use: Vienna Connection Cab, Global bus rental, Eg Reisen, Zonetransfers, etc).

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
- Rest: 11h between shifts.

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
    
    st.info("The app is pre-loaded with the OsaBus Customer Service Manual.")
    
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
    3. VISUALS: If the step involves using the CRM, specific forms, or looking at a specific document, INSERT A VISUAL TAG like  at the relevant step.
    4. REFERENCE: Mention the Section Name (e.g., "See Section 'Receiving payments'").
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
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I have the OsaBus manual memorized. How can I help you today? (e.g., 'Client paid, what next?' or 'How do I create a Purchase Order?') "}]

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
