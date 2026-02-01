import streamlit as st
import requests
import json

# --- PAGE SETUP ---
st.set_page_config(page_title="OsaBus SOP Assistant", page_icon="📘", layout="wide")

# --- FULL MANUAL TEXT ---
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

RECEIVING PAYMENTS workflow:
1. Payments are recorded automatically (Status changes to "Paid").
2. Send "Thank You" email to client:
   - Full Pay: "Thank you for choosing OsaBus! The payment has been received and the booking is confirmed. The driver's details will be provided the evening before the trip."
   - Deposit: "Thank you, the deposit payment has been received... Rest due [Date]."
3. (Immediate Next Step) Go to Purchase Request -> Create Purchase Order -> Send Link to Supplier to confirm.

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
    manual_text = st.text_area("Manual Text:", value=FULL_MANUAL_TEXT, height=300)
    
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

def ask_manual(api_key, manual, chat_history, question):
    model_path, api_version = get_available_model(api_key)
    if not model_path: return "ERROR", "API Key invalid or API disabled."

    url = f"https://generativelanguage.googleapis.com/{api_version}/{model_path}:generateContent?key={api_key}"
    
    # Constructing context from history (Last 3 exchanges to keep memory fresh)
    history_text = ""
    for msg in chat_history[-6:]: 
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"

    # --- STRICT INSTRUCTION PROMPT ---
    prompt = f"""
    You are an assistant whose ONLY knowledge source is the provided manual.
    
    --- MANUAL CONTENT ---
    {manual}
    --- END MANUAL ---

    --- CONVERSATION HISTORY (Context) ---
    {history_text}
    --- END HISTORY ---

    --- USER QUESTION ---
    {question}

    --- INSTRUCTIONS ---
    Your main goal is to guide the user step-by-step through all processes in the manual without skipping any steps or important details.
    
    Rules you must follow:
    1. Always base your answers strictly on the manual content. Do NOT invent steps or information.
    2. When the user asks vague or short questions such as “what’s next?”, “continue”, “next step”, or “go on”, you must automatically continue with the next logical step from the current process based on the CONVERSATION HISTORY.
    3. Track the current progress in the procedure and remember which step the user is on.
    4. Never skip steps, warnings, notes, prerequisites, or confirmations mentioned in the manual.
    5. If a step requires user confirmation or action, clearly tell the user what to do and wait for confirmation before proceeding.
    6. If multiple procedures exist, ask the user which task they want to perform before starting.
    7. Use clear, simple instructions and number the steps when guiding the user.
    8. If the user asks a question outside the manual’s scope, respond with: "This information is not available in the manual."
    9. If a step depends on previous conditions, verify them before continuing.
    10. Always prioritize accuracy and completeness over speed or brevity.
    11. VISUALS: If a step involves a specific button or screen, insert a tag like .

    Behavior style:
    - Be concise but precise
    - Be structured
    - Be instructional
    - Be patient and supportive
    
    Your purpose is to function as an interactive manual assistant that ensures the user completes tasks correctly and in the proper order.
    Maintain an internal state of the current task and step number. Resume automatically when the user says “next”, “continue”, “done”, or “finished”.
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
st.markdown("Ask about workflows. Say **'Next'** to move to the next step.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello. I am your strict SOP assistant. What task would you like to start? (e.g., 'Proposal Accepted', 'Receiving Payment')."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type your question here..."):
    if not api_key:
        st.error("Please enter your Google API Key in the sidebar.")
    else:
        # 1. Append User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Generate Response (Passing History!)
        with st.chat_message("assistant"):
            with st.spinner("Processing step..."):
                # We pass the full session state messages to the function now
                status, response_text = ask_manual(api_key, manual_text, st.session_state.messages, prompt)
                
                if status == "SUCCESS":
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    st.error("Error retrieving answer.")
                    st.code(response_text)
