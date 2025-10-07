import streamlit as st
import requests
import json

# -------------------- CONFIG --------------------
BASE_URL = "http://127.0.0.1:5000"
REQUEST_TIMEOUT = 5

st.set_page_config(
    page_title="🏦 Distributed Banking Client",
    layout="wide",
    page_icon="🏦"
)

# -------------------- API Helper --------------------
def call_api(endpoint, method="post", data=None, params=None):
    try:
        if method == "post":
            resp = requests.post(f"{BASE_URL}/{endpoint}", data=data, timeout=REQUEST_TIMEOUT)
        else:
            resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=REQUEST_TIMEOUT)
        try:
            return resp.json()
        except:
            return {"error": resp.text}
    except Exception as e:
        return {"error": str(e)}

# -------------------- HEADER --------------------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1F4172;
        margin-bottom: 10px;
    }
    .section-title {
        font-size: 1.3rem;
        color: #25476A;
        border-left: 4px solid #5DADE2;
        padding-left: 10px;
        margin-top: 25px;
    }
    .stButton button {
        border-radius: 10px;
        background-color: #1F4172 !important;
        color: white !important;
        border: none;
        padding: 0.5em 1em;
    }
    .stButton button:hover {
        background-color: #2E86C1 !important;
        color: white !important;
        transform: scale(1.03);
        transition: 0.2s;
    }
    .result-box {
        background-color: #F8F9F9;
        padding: 10px 15px;
        border-radius: 10px;
        border: 1px solid #E5E8E8;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<p class="main-title">🏦 Distributed Banking Client</p>', unsafe_allow_html=True)
st.caption("Manage accounts, deposits, withdrawals, and transfers across distributed bank branches.")

# -------------------- SIDEBAR --------------------
st.sidebar.header("📋 Navigation")
page = st.sidebar.radio("Go to", ["🏠 Dashboard", "💰 Account Operations", "🔁 Transfer Money"])

# -------------------- ACCOUNT OPERATIONS --------------------
if page == "💰 Account Operations":
    st.markdown('<p class="section-title">💳 Account Operations</p>', unsafe_allow_html=True)
    col1, col2 = st.columns([1.3, 1])

    with col1:
        host = st.text_input("Branch Host", "127.0.0.1")
        port = st.text_input("Port", "9100")
        account = st.text_input("Account No", "1001")
        amount = st.text_input("Amount")

    with col2:
        st.write("### 🔧 Actions")
        if st.button("📊 Get Balance"):
            res = call_api("balance", data={"host": host, "port": port, "account": account})
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.json(res)
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("💸 Deposit"):
            res = call_api("deposit", data={"host": host, "port": port, "account": account, "amount": amount})
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.json(res)
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🏧 Withdraw"):
            res = call_api("withdraw", data={"host": host, "port": port, "account": account, "amount": amount})
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.json(res)
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("📋 List Accounts"):
            res = call_api("list_accounts", method="get", params={"host": host, "port": port})
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.json(res)
            st.markdown('</div>', unsafe_allow_html=True)

# -------------------- TRANSFER MONEY --------------------
elif page == "🔁 Transfer Money":
    st.markdown('<p class="section-title">🔄 Transfer Money Between Accounts</p>', unsafe_allow_html=True)
    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🏦 Source Account")
            src_host = st.text_input("From Host", "127.0.0.1")
            src_port = st.text_input("From Port", "9100")
            src_account = st.text_input("From Account", "1001")

        with col2:
            st.markdown("#### 🏧 Destination Account")
            dest_host = st.text_input("To Host", "127.0.0.1")
            dest_port = st.text_input("To Port", "9200")
            dest_account = st.text_input("To Account", "2001")

        transfer_amount = st.text_input("💰 Transfer Amount")

        if st.button("🚀 Transfer Now"):
            res = call_api("transfer", data={
                "src_host": src_host, "src_port": src_port, "src_account": src_account,
                "dest_host": dest_host, "dest_port": dest_port, "dest_account": dest_account,
                "amount": transfer_amount
            })
            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.json(res)
            st.markdown('</div>', unsafe_allow_html=True)

# -------------------- DASHBOARD --------------------
else:
    st.markdown('<p class="section-title">📊 Overview Dashboard</p>', unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/2920/2920244.png", width=300)
    st.markdown(
        """
        Welcome to the **Distributed Banking Dashboard** 🏦  
        Here you can:
        - Deposit, withdraw, and check balances across branches  
        - Perform **inter-branch money transfers**  
        - Get account lists and monitor distributed transactions  
        """)
    st.success("✅ Connected to backend API at " + BASE_URL)
