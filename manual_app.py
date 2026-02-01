import streamlit as st
import requests
import json
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="OsaBus SOP Assistant", page_icon="📘", layout="wide")

# --- FULL MANUAL TEXT (FROM PDF) ---
# This contains the EXACT text from your PDF upload.
FULL_MANUAL_TEXT = """
CUSTOMER SERVICE MANUAL
Updated: 26/01/2026 

1. CRMs
We have a total of 4 CRMs:
- COM CRM: info@osabus.com (Latvia, Netherlands, General)
- Spain CRM: info@osabus.es
- German CRM: info@osabus.de
- USA CRM: Used for proposals and invoices in USD (USA, Asia, LatAm, Middle East)

2. Communication Channels
Email: info@osabus.com, info@osabus.es, info@osabus.de 
Phone: +49 331 900 849 99 (General questions only. No consultations/changes via phone).
Staff Guidelines: "We do not provide consultations over the phone... please write an email."

3. Email Formatting
- Use standard fonts. No emojis.
- Subject line, Greeting, Body, Sign-off.
- "Reply All" if client CC'd others (except other bus companies).
- No ALL CAPS.
- Use sentence case.

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
General Rule:
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
- Save (Do not "Save and Send" yet).
- Copy the "Vendor Link".
- Email supplier from operations1@osagroup.ltd with the link.
- Subject: Proposal number + Subject.
- Once supplier quotes, approve the best quote in system.
- Update proposal price (Quote + 15% commission usually).

7. Purchase Order (Confirming Supplier)
- Once you receive payment from client, go to the Purchase Request.
- Make a PURCHASE ORDER to the supplier to confirm the offer.
- Check details (flight number, etc).
- Copy the Purchase Order link.
- Send this link to the supplier to officially confirm the order.

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
- Refund fee for credit cards: €35 (covered by client).
- Send details (IBAN, SWIFT) to Zane.

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
    # Pre-load the manual text
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
    
    # --- PROMPT WITH STRICT LOGIC ---
    prompt = f"""
    You are the OsaBus Process Assistant.
    
    --- MANUAL CONTENT ---
    {manual}
    --- END MANUAL ---

    --- USER QUESTION ---
    {question}

    --- INSTRUCTIONS ---
    1. Answer strictly based on the provided manual text.
    2. STEP-BY-STEP: Provide a clear, numbered list of actions.
    3. NO IMAGES: Do not use  tags. Use text descriptions only.
    4. LOGICAL ASSUMPTIONS:
       - If a step is missing in one section but logically implied by another (e.g., "Ask supplier for invoice" implies sending an email), you may state it.
       - MARK ASSUMPTIONS: If you make a logical deduction, prefix it with "(Logical Assumption):".
       - Example: "3. (Logical Assumption): Since the manual says to 'revert back for invoice', you should do this in the same email as the confirmation."
    5. UNKNOWN INFO: If the manual has absolutely no information on a topic, state: "I cannot find this specific information in the OsaBus manual."
    6. FORMAT: Use bold headers and bullet points.

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
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am ready. Ask me anything about the SOPs."}]

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
            with st.spinner("Consulting manual..."):
                status, response_text = ask_manual(api_key, manual_text, prompt)
                
                if status == "SUCCESS":
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    st.error("Error retrieving answer.")
                    st.code(response_text)
