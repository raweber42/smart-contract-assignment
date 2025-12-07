import streamlit as st
import requests
import time

# Configuration
API_URL = "http://127.0.0.1:5000/api"
MATIC_RATE = 1.5 # 1 USD = 1.5 MATIC (Mock)

st.set_page_config(page_title="Smart Contract Tutor", page_icon="👨🏼‍🏫", layout="wide")

# Custom CSS (Dark Lovable Theme)
st.markdown("""
<style>
    /* Global Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        color: #E2E8F0; /* Light Gray Text */
    }

    /* Main Background */
    .stApp {
        background-color: #1A1F2C; /* Dark Blue/Gray Background */
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #11141D; /* Darker Sidebar */
        border-right: 1px solid #2D3748;
    }
    
    /* Sidebar Text */
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] label {
        color: #A0AEC0;
    }

    /* Gradient Title */
    .gradient-text {
        background: linear-gradient(135deg, #9b87f5 0%, #D6BCFA 100%); /* Lighter Purple Gradient */
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3em;
        padding-bottom: 10px;
    }

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #9b87f5 0%, #7E69AB 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(155, 135, 245, 0.4);
        color: white;
        border: 1px solid #D6BCFA;
    }
    div.stButton > button:active {
        transform: translateY(0);
    }

    /* Metrics */
    div[data-testid="stMetricValue"] {
        color: #D6BCFA !important; /* Light Purple */
        font-weight: 700;
        font-size: 2.2rem !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8; /* Slate Gray */
        font-weight: 500;
    }
    
    /* Cards/Containers */
    .stInfo, .stSuccess, .stWarning, .stError {
        background-color: #2D3748; /* Dark Card Background */
        color: #E2E8F0;
        border-radius: 12px;
        border: 1px solid #4A5568;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #2D3748;
        border-radius: 8px;
        color: #E2E8F0;
    }
    div[data-testid="stExpander"] {
        background-color: #1A1F2C;
        border: 1px solid #4A5568;
        border-radius: 8px;
    }
    
    /* Code Blocks */
    code {
        color: #D6BCFA;
        background-color: #11141D;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def get_state():
    try:
        return requests.get(f"{API_URL}/state").json()
    except:
        return None

def format_currency(amount):
    matic_val = amount * MATIC_RATE
    return f"{amount:.2f} USD"

def format_matic(amount):
    matic_val = amount * MATIC_RATE
    return f"~{matic_val:.2f} MATIC"

# --- Sidebar ---
st.sidebar.title("Simulation Controls")

# Lesson Price Configuration
lesson_price = st.sidebar.number_input("Lesson Price (USD)", min_value=10, max_value=1000, value=30, step=5)

# Lesson Type Selection
lesson_type = st.sidebar.selectbox(
    "Select Lesson Type",
    ("English Lesson", "Coding", "Guitar")
)

st.sidebar.markdown("---")

# Add Funds
st.sidebar.subheader("Wallet Management")
if st.sidebar.button("Add 100 USD to Student"):
    requests.post(f"{API_URL}/topup", json={"amount": 100})
    st.toast("Added 100 USD", icon="💰")
    time.sleep(0.5)
    st.rerun()

st.sidebar.markdown("---")

scenario = st.sidebar.selectbox(
    "Select Scenario",
    ("Happy Path", "Student No-Show", "Teacher No-Show")
)

scenario_map = {
    "Happy Path": "happy_path",
    "Student No-Show": "student_no_show",
    "Teacher No-Show": "teacher_no_show"
}

# Removed manual "Apply Scenario" button to avoid confusion. 
# Scenario is now sent with the resolve request.

st.sidebar.markdown("---")
if st.sidebar.button("Reset System"):
    requests.post(f"{API_URL}/reset")
    st.rerun()

# --- Main UI ---

# Title
st.markdown('<h1 class="gradient-text">Smart Contract Tutor</h1>', unsafe_allow_html=True)

st.markdown("### Trustless Payments via Smart Contract & Oracle")

st.markdown(f"**Current Lesson:** {lesson_type}")
st.markdown("**Teacher:** Alice (Verified)")

# Fetch State
state = get_state()

if not state:
    st.error("Backend is not running. Please start the Flask server.")
    st.stop()

balances = state['balances']
status = state['status']
logs = state['logs']

# 1. Wallet Display
st.subheader("💰 Wallet Balances")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Student Wallet", value=format_currency(balances['student']), delta=format_matic(balances['student']), delta_color="off")
with col2:
    st.metric(label="Smart Contract (Escrow)", value=format_currency(balances['contract']), delta=format_matic(balances['contract']), delta_color="off")
with col3:
    st.metric(label="Teacher Wallet", value=format_currency(balances['teacher']), delta=format_matic(balances['teacher']), delta_color="off")
with col4:
    st.metric(label="Platform Wallet", value=format_currency(balances['platform']), delta=format_matic(balances['platform']), delta_color="off")

st.markdown("---")

# 2. Process Flow
st.subheader("📝 Lesson Workflow")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("#### 1. Agreement & Funding")
    
    # Prominent Booking Card
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(155, 135, 245, 0.1) 0%, rgba(126, 105, 171, 0.1) 100%);
        border: 1px solid #9b87f5;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    ">
        <div style="color: #D6BCFA; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Booking Details</div>
        <h3 style="color: #FFFFFF; margin: 0; font-size: 1.5em;">{lesson_type}</h3>
        <div style="font-size: 2.5em; font-weight: 800; color: #9b87f5; margin: 10px 0;">${lesson_price}</div>
        <div style="color: #A0AEC0; font-size: 0.9em;">60 Minutes • Live 1-on-1</div>
    </div>
    """, unsafe_allow_html=True)
    
    if status == "CREATED":
        if st.button(f"Fund Lesson ({lesson_price} USD)"):
            res = requests.post(f"{API_URL}/fund", json={"price": lesson_price, "lesson_title": lesson_type})
            if res.status_code == 200:
                st.toast("Funded Successfully!", icon="✅")
                time.sleep(1)
                st.rerun()
            else:
                st.error(res.json().get("message"))
    elif status == "FUNDED":
        st.success("✅ Lesson Funded")
    elif status in ["COMPLETED", "REFUNDED"]:
        # st.success("✅ Lesson Funded") # Removed as per request
        st.markdown("---")
        if st.button("Start New Lesson"):
            # Funding again will reset the state in the backend logic
            res = requests.post(f"{API_URL}/fund", json={"price": lesson_price, "lesson_title": lesson_type})
            if res.status_code == 200:
                st.toast("New Lesson Funded!", icon="✅")
                time.sleep(1)
                st.rerun()
            else:
                st.error(res.json().get("message"))

with c2:
    st.markdown("#### 2. The Lesson")
    st.markdown(f"*Scenario Active: {scenario}*")
    st.markdown("Simulating Google Meet session...")
    
    if status == "FUNDED":
        st.markdown(f"[**Join Google Meet**](https://meet.google.com/abc-defg-hij)")
        st.info("Waiting for lesson completion...")
    elif status in ["COMPLETED", "REFUNDED"]:
        pass # Removed success message as per request

with c3:
    st.markdown("#### 3. Oracle Resolution")
    
    # Always show Oracle Data if available
    if state.get('last_oracle_data'):
        with st.expander("View Oracle API Response", expanded=True):
            st.json(state['last_oracle_data'])

    if status == "FUNDED":
        if st.button("Trigger Oracle Resolution"):
            with st.spinner("Oracle querying Google Meet API..."):
                time.sleep(1.5) # Fake delay for effect
                # Send the current scenario selection to ensure it's applied
                res = requests.post(f"{API_URL}/resolve", json={"scenario": scenario_map[scenario]}).json()
                
                # st.write(f"**Outcome:** {res['contract_outcome']}")
                # with st.expander("View Oracle API Response"):
                #     st.json(res['oracle_data'])
                
                time.sleep(1)
                st.rerun()
    elif status in ["COMPLETED", "REFUNDED"]:
        outcome = state.get('last_outcome', 'Unknown')
        
        if "Happy Path" in outcome:
            st.success(f"✅ Contract Settled: {outcome}")
        else:
            st.warning(f"⚠️ Contract Settled: {outcome}")
            st.info("Funds have been redistributed according to the No-Show policy.")

# 3. Logs
st.markdown("---")
st.subheader("📜 Smart Contract Logs")

for log in reversed(logs):
    # Handle both old string logs and new dict logs
    if isinstance(log, dict):
        msg = log['message']
        tx = log.get('tx_hash')
    else:
        msg = log
        tx = None
        
    st.text(f"> {msg}")
    if tx:
        st.markdown(f"[View Transaction on PolygonScan](https://amoy.polygonscan.com/tx/{tx})")
    st.markdown("---")
