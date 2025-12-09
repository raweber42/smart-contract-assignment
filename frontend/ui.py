import streamlit as st
import time
import random

# Configuration
MATIC_RATE = 8.09 # 1 USD = 8.09 MATIC (State of 12/09/2025: https://de.tradingview.com/symbols/MATICUSD/)

st.set_page_config(page_title="Smart Contract Tutor", page_icon="👨🏼‍🏫", layout="wide")

# ============================================
# Smart Contract Logic (embedded)
# ============================================
class SmartContract:
    def __init__(self):
        self.reset()

    def reset(self):
        # Initial Balances (Mock USD)
        self.balances = {
            "student": 100,
            "teacher": 0,
            "contract": 0,
            "platform": 0
        }
        self.status = "CREATED" # CREATED, FUNDED, COMPLETED, REFUNDED
        self.lesson_price = 30
        self.platform_fee_percent = 0.02
        self.tx_fee_percent = 0.001 
        self.logs = []
        self.last_oracle_data = None
        self.last_outcome = None
        self.transactions = []

    def log(self, message, tx_hash=None):
        self.logs.append({"message": message, "tx_hash": tx_hash})

    def topup_student(self, amount):
        self.balances["student"] += amount
        self.log(f"Student wallet topped up by ${amount:.2f}.")
        return True, "Top-up successful."

    def fund_lesson(self, price=30, lesson_title="Lesson"):
        if self.status not in ["CREATED", "COMPLETED", "REFUNDED"]:
            return False, "Contract already funded."
        
        # Reset state for new lesson if previous was completed
        if self.status in ["COMPLETED", "REFUNDED"]:
            self.status = "CREATED"
            self.last_oracle_data = None
            self.last_outcome = None
        
        self.lesson_price = price
        tx_fee = price * self.tx_fee_percent
        total_deduction = price + tx_fee

        if self.balances["student"] < total_deduction:
            return False, f"Insufficient funds. Need ${total_deduction:.2f}."

        self.balances["student"] -= total_deduction
        self.balances["contract"] += price
        self.status = "FUNDED"
        
        tx_hash = f"0x{abs(hash(str(time.time()) + 'fund'))}"
        self.log(f"Student funded '{lesson_title}' (${price:.2f} - ${tx_fee:.2f} fee). Funds locked in Escrow.", tx_hash)
        return True, "Lesson funded successfully."

    def resolve_lesson(self, teacher_duration, student_duration, oracle_data=None, required_duration=60):
        if self.status != "FUNDED":
            return False, "Contract not in funded state."

        self.last_oracle_data = oracle_data

        min_threshold = required_duration * 0.95
        student_override = oracle_data.get("student_override", False) if oracle_data else False

        payout_teacher = False
        refund_student = False
        
        outcome = "Unknown"
        
        teacher_pct = (teacher_duration / required_duration) * 100
        student_pct = (student_duration / required_duration) * 100

        # Check for student override first - student agrees to release payment regardless of attendance
        if student_override:
            outcome = f"Student Override: Student approved payment release. (Teacher: {teacher_pct:.0f}%, Student: {student_pct:.0f}%)"
            payout_teacher = True
        elif teacher_duration >= min_threshold and student_duration >= min_threshold:
            outcome = "Happy Path: Lesson Completed Successfully."
            payout_teacher = True
        elif teacher_duration < min_threshold:
            outcome = f"Teacher No-Show: Student refunded. (Teacher attended {teacher_pct:.0f}%, which is less than the required minimum of 95%)"
            refund_student = True
        else:
            outcome = f"Student No-Show: Teacher compensated. (Teacher was present {teacher_pct:.0f}% of the time, Student only attended {student_pct:.0f}%)"
            payout_teacher = True
        
        self.last_outcome = outcome
        tx_hash = f"0x{abs(hash(str(time.time()) + 'resolve'))}"

        if payout_teacher:
            contract_balance = self.balances["contract"]
            
            platform_fee = contract_balance * self.platform_fee_percent
            gross_payout = contract_balance - platform_fee
            
            tx_fee = gross_payout * self.tx_fee_percent
            net_payout = gross_payout - tx_fee
            
            self.balances["contract"] = 0
            self.balances["teacher"] += net_payout
            self.balances["platform"] += platform_fee
            
            self.status = "COMPLETED"
            self.log(f"Oracle Resolution: {outcome} -> Payout ${net_payout:.2f} to Teacher (Fees: ${platform_fee:.2f} Platform, ${tx_fee:.2f} Tx).", tx_hash)
        
        elif refund_student:
            gross_refund = self.balances["contract"]
            tx_fee = gross_refund * self.tx_fee_percent
            net_refund = gross_refund - tx_fee
            
            self.balances["contract"] = 0
            self.balances["student"] += net_refund
            
            self.status = "REFUNDED"
            self.log(f"Oracle Resolution: {outcome} -> Refund ${net_refund:.2f} to Student (Tx Fee: ${tx_fee:.2f}).", tx_hash)

        return True, outcome

    def get_state(self):
        return {
            "balances": self.balances,
            "status": self.status,
            "logs": self.logs,
            "lesson_price": self.lesson_price,
            "last_oracle_data": self.last_oracle_data,
            "last_outcome": self.last_outcome
        }


# ============================================
# Oracle Logic (embedded)
# ============================================
class Oracle:
    def __init__(self):
        self.scenario = "happy_path" # Default

    def set_scenario(self, scenario_key):
        self.scenario = scenario_key

    def get_meeting_data(self):
        # Simulating Google Meet API response
        # Returns duration in minutes
        
        if self.scenario == "happy_path":
            return {
                "teacher_duration": 60,
                "student_duration": 60,
                "raw_json": {
                    "meetingCode": "abc-defg-hij",
                    "participants": [
                        {"email": "teacher@uni.com", "durationSeconds": 3600},
                        {"email": "student@uni.com", "durationSeconds": 3600}
                    ]
                }
            }
        elif self.scenario == "student_no_show":
            return {
                "teacher_duration": 60,
                "student_duration": 0,
                "raw_json": {
                    "meetingCode": "abc-defg-hij",
                    "participants": [
                        {"email": "teacher@uni.com", "durationSeconds": 3600}
                    ]
                }
            }
        elif self.scenario == "teacher_no_show":
            return {
                "teacher_duration": 0,
                "student_duration": 60,
                "raw_json": {
                    "meetingCode": "abc-defg-hij",
                    "participants": [
                        {"email": "student@uni.com", "durationSeconds": 3600}
                    ]
                }
            }
        elif self.scenario == "student_override":
            # Both attend only 50%, but student agrees to release payment
            return {
                "teacher_duration": 30,
                "student_duration": 30,
                "student_override": True,
                "raw_json": {
                    "meetingCode": "abc-defg-hij",
                    "participants": [
                        {"email": "teacher@uni.com", "durationSeconds": 1800},
                        {"email": "student@uni.com", "durationSeconds": 1800}
                    ],
                    "student_override": True,
                    "override_reason": "Student agreed to release funds to teacher"
                }
            }
        elif self.scenario == "random":
            t_dur = random.randint(0, 60)
            s_dur = random.randint(0, 60)
            return {
                "teacher_duration": t_dur,
                "student_duration": s_dur,
                "raw_json": {
                    "meetingCode": "abc-defg-hij",
                    "participants": [
                        {"email": "teacher@uni.com", "durationSeconds": t_dur * 60},
                        {"email": "student@uni.com", "durationSeconds": s_dur * 60}
                    ]
                }
            }
        else:
            # Default fallback
            return {
                "teacher_duration": 0,
                "student_duration": 0,
                "raw_json": {}
            }


# ============================================
# Initialize Session State
# ============================================
if "contract" not in st.session_state:
    st.session_state.contract = SmartContract()
if "oracle" not in st.session_state:
    st.session_state.oracle = Oracle()

contract = st.session_state.contract
oracle = st.session_state.oracle

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
    return contract.get_state()

def format_currency(amount):
    matic_val = amount * MATIC_RATE
    return f"{amount:.2f} USD"

def format_matic(amount):
    matic_val = amount * MATIC_RATE
    return f"~{matic_val:.2f} MATIC"

# --- Sidebar ---
st.sidebar.title("Settings")

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

st.sidebar.markdown(
    """
    <div style="text-align: center; margin-bottom: 15px;">
        <a href="https://amoy.polygonscan.com/address/0x1397ec5db7a62a90c10b3ac949c225fdf057773f" target="_blank">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=https://amoy.polygonscan.com/address/0x1397ec5db7a62a90c10b3ac949c225fdf057773f" style="border-radius: 10px; border: 2px solid #333;">
        </a>
        <div style="font-size: 0.8em; color: #A0AEC0; margin-top: 5px;">
            Scan to fund Student Wallet
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

if st.sidebar.button("Add 100 USD to Student"):
    contract.topup_student(100)
    st.toast("Added 100 USD", icon="💰")
    time.sleep(0.5)
    st.rerun()

st.sidebar.markdown("---")

scenario = st.sidebar.selectbox(
    "Select Scenario",
    ("Happy Path", "Student No-Show", "Teacher No-Show", "Student Override", "Random")
)

scenario_map = {
    "Happy Path": "happy_path",
    "Student No-Show": "student_no_show",
    "Teacher No-Show": "teacher_no_show",
    "Student Override": "student_override",
    "Random": "random"
}

# Removed manual "Apply Scenario" button to avoid confusion. 
# Scenario is now sent with the resolve request.

st.sidebar.markdown("---")
if st.sidebar.button("Reset System"):
    contract.reset()
    st.rerun()

# --- Main UI ---

# Title
st.markdown('<h1 class="gradient-text">Smart Contract Tutor</h1>', unsafe_allow_html=True)

st.markdown("### Trustless Payments via Smart Contract & Oracle")

st.markdown(f"**Current Lesson:** {lesson_type}")
st.markdown("**Teacher:** Alice (Verified)")

# Fetch State
state = get_state()

balances = state['balances']
status = state['status']
logs = state['logs']

# 1. Wallet Display
st.subheader("💰 Wallet Balances")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Student Wallet", value=format_currency(balances['student']), delta=format_matic(balances['student']), delta_color="off")
    st.markdown("[View on Explorer ↗](https://amoy.polygonscan.com/address/0x1397ec5db7a62a90c10b3ac949c225fdf057773f)", unsafe_allow_html=True)
with col2:
    st.metric(label="Smart Contract (Escrow)", value=format_currency(balances['contract']), delta=format_matic(balances['contract']), delta_color="off")
    st.markdown("[View on Explorer ↗](https://amoy.polygonscan.com/address/0x432c90E7808B6fB474F7886e691Af3664c9C5b28#code)", unsafe_allow_html=True)
with col3:
    st.metric(label="Teacher Wallet", value=format_currency(balances['teacher']), delta=format_matic(balances['teacher']), delta_color="off")
    st.markdown("[View on Explorer ↗](https://amoy.polygonscan.com/address/0xcffdbf68a5f49b72efd81bc39911ec94a51cecda)", unsafe_allow_html=True)
with col4:
    st.metric(label="Platform Wallet", value=format_currency(balances['platform']), delta=format_matic(balances['platform']), delta_color="off")
    st.markdown("[View on Explorer ↗](https://amoy.polygonscan.com/address/0xcffdbf68a5f49b72efd81bc39911ec94a51cecda)", unsafe_allow_html=True)

st.markdown("---")

# 2. Process Flow
st.subheader("📝 Lesson Workflow")

c1, c2, c3 = st.columns(3)

with c1:
    with st.container(border=True):
        st.markdown("#### 1. Agreement & Funding")
        
        # Prominent Booking Card
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(155, 135, 245, 0.1) 0%, rgba(126, 105, 171, 0.1) 100%);
            border: 1px solid #9b87f5;
            border-radius: 10px;
            padding: 8px;
            text-align: center;
            margin-bottom: 10px;
        ">
            <div style="color: #D6BCFA; font-size: 0.7em; text-transform: uppercase; letter-spacing: 1px;">Booking Details</div>
            <h3 style="color: #FFFFFF; margin: 2px 0; font-size: 1.1em;">{lesson_type}</h3>
            <div style="font-size: 1.8em; font-weight: 800; color: #9b87f5; line-height: 1.1;">${lesson_price}</div>
            <div style="color: #A0AEC0; font-size: 0.75em;">60 Minutes • Live 1-on-1</div>
        </div>
        """, unsafe_allow_html=True)
        
        if status == "CREATED":
            if st.button(f"Fund Lesson ({lesson_price} USD)"):
                success, message = contract.fund_lesson(lesson_price, lesson_type)
                if success:
                    st.toast("Funded Successfully!", icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
        elif status == "FUNDED":
            st.success("✅ Lesson Funded")
        elif status in ["COMPLETED", "REFUNDED"]:
            st.markdown("---")
            if st.button("Start New Lesson"):
                success, message = contract.fund_lesson(lesson_price, lesson_type)
                if success:
                    st.toast("New Lesson Funded!", icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)

with c2:
    with st.container(border=True):
        st.markdown("#### 2. The Lesson")
        st.markdown("Simulating Google Meet session...")
        
        if status == "FUNDED":
            st.markdown(f"[**Join Google Meet**](https://meet.google.com/fac-hbvx-pjz)")
            st.info("Waiting for lesson completion...")
        elif status in ["COMPLETED", "REFUNDED"]:
            st.markdown("✅ Lesson completed")

with c3:
    with st.container(border=True):
        st.markdown("#### 3. Oracle Resolution")
        
        # Always show Oracle Data if available
        if state.get('last_oracle_data'):
            with st.expander("View Oracle API Response", expanded=True):
                st.json(state['last_oracle_data'])

        if status == "FUNDED":
            if st.button("Trigger Oracle Resolution"):
                with st.spinner("Oracle querying Google Meet API..."):
                    time.sleep(1.5) # Fake delay for effect
                    # Set the scenario and get meeting data
                    oracle.set_scenario(scenario_map[scenario])
                    data = oracle.get_meeting_data()
                    # Resolve the lesson via smart contract
                    contract.resolve_lesson(
                        teacher_duration=data['teacher_duration'],
                        student_duration=data['student_duration'],
                        oracle_data=data
                    )
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
        
    st.code(f"> {msg}", language="text")
    if tx:
        st.markdown(f"[View Transaction on PolygonScan](https://amoy.polygonscan.com/tx/0xe695d8b80f4d094672af19477bbc9ec536dff2bdf0b90df7c78c920c07c8d579)")
    st.markdown("---")
