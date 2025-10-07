import streamlit as st
import requests
import pandas as pd
import random
import os
from datetime import datetime

# Map replica IPs/ports to branch names
replica_branch_names = {
    "127.0.0.1:9101": "Delhi Branch",
    "127.0.0.1:9100": "Mumbai Branch",
    # add more if you have more replicas
}

LOG_FILE = "operation_logs.csv"

if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=["Time", "Branch", "Account", "Action", "Result"]).to_csv(LOG_FILE, index=False)

logs_df = pd.read_csv(LOG_FILE)
for col in ["Time", "Account", "Action", "Result"]:
    if col not in logs_df.columns:
        logs_df[col] = None


# ---------------- CONFIG ----------------
BASE_URL = "http://127.0.0.1:5000"
REQUEST_TIMEOUT = 5

st.set_page_config(
    page_title="🏦 Smart Distributed Bank",
    layout="wide",
    page_icon="💎"
)

# ---------------- STYLES ----------------
st.markdown("""
<style>
body {
  background: linear-gradient(135deg, #141e30, #243b55);
  color: #f8f9fa;
}
.block-container {
  padding-top: 1rem;
}
.glass {
  background: rgba(255,255,255,0.08);
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 8px 32px 0 rgba(31,38,135,0.37);
  backdrop-filter: blur(6.5px);
  -webkit-backdrop-filter: blur(6.5px);
  border: 1px solid rgba(255,255,255,0.18);
}
.stButton > button {
  border-radius: 10px;
  background-color: #00C9A7 !important;
  color: white !important;
  font-weight: bold;
  border: none;
  transition: 0.3s ease;
}
.stButton > button:hover {
  transform: scale(1.05);
  background-color: #00E1C4 !important;
}
.metric-box {
  text-align: center;
  padding: 10px;
  background: rgba(255,255,255,0.1);
  border-radius: 15px;
  margin: 10px;
}
hr {
  border: none;
  border-top: 1px solid rgba(255,255,255,0.1);
  margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
LOG_FILE = "operation_logs.csv"

# Load existing logs if available
if os.path.exists(LOG_FILE):
    st.session_state.logs = pd.read_csv(LOG_FILE).to_dict("records")
else:
    st.session_state.logs = []

def save_logs():
    """Save logs to CSV for persistence"""
    if st.session_state.logs:
        pd.DataFrame(st.session_state.logs).to_csv(LOG_FILE, index=False)

# ---------------- API Helper ----------------
def call_api(endpoint, method="post", data=None, params=None):
    try:
        if method == "post":
            resp = requests.post(f"{BASE_URL}/{endpoint}", data=data, timeout=REQUEST_TIMEOUT)
        else:
            resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=REQUEST_TIMEOUT)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_branch_name(host, port):
    """Return readable branch name from host-port combo."""
    key = f"{host}:{port}"
    if key in replica_branch_names:
        return replica_branch_names[key]
    return f"Custom ({host}:{port})"


def log_action(action, result, account=None, host=None, port=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    branch = get_branch_name(host, port)
    entry = {
        "Time": timestamp,
        "Branch": branch,
        "Account": account if account else "N/A",
        "Action": action,
        "Result": str(result)
    }
    st.session_state.logs.append(entry)
    save_logs()



def display_logs(selected_account=None):
    st.markdown("### 🧾 Operation Logs")
    logs_df = pd.DataFrame(st.session_state.logs)

    if len(logs_df) > 0:
        if selected_account:
            logs_df = logs_df[logs_df["Account"] == selected_account]

        if logs_df.empty:
            st.caption("No logs found for this account.")
            return

        latest_logs = logs_df.tail(10)
        st.dataframe(latest_logs, use_container_width=True)

        csv_data = logs_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Logs for This Account",
            data=csv_data,
            file_name=f"logs_{selected_account or 'all'}.csv",
            mime="text/csv"
        )
    else:
        st.caption("No operations performed yet.")

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center; color:#00E1C4;'>🏦 Smart Distributed Banking System</h1>", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.header("📋 Navigation")
page = st.sidebar.radio("Choose section", ["Dashboard", "Account Operations", "Transfer Money"])

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.markdown("### 🧾 Operation Logs")
    st.markdown("<hr>", unsafe_allow_html=True)

    # ✅ Collect unique accounts from logs
    logs_df = pd.DataFrame(st.session_state.logs)
    account_list = sorted(logs_df["Account"].dropna().unique().tolist()) if not logs_df.empty else []
    selected_account = None

    # ✅ Account filter dropdown
    if account_list:
        selected_account = st.selectbox(
            "Select Account to View Logs",
            options=["All Accounts"] + account_list,
            index=0
        )

    # ✅ Display filtered logs
    if selected_account == "All Accounts" or not selected_account:
        display_logs()
    else:
        display_logs(selected_account)

    # --- Clear Logs Button ---
    if st.button("🗑️ Clear Logs"):
        st.session_state.logs = []
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        st.success("Logs cleared successfully!")

    st.markdown("<hr>", unsafe_allow_html=True)

    # --- Feature Overview Section ---
    st.markdown("### 💡 Features Implemented")
    features = [
        "💸 Real-time Deposit and Withdrawal System",
        "🔁 Inter-branch Money Transfer",
        "📊 Distributed Architecture using Replica Servers",
        "🧾 Transaction Logging and Transparency",
        "🔐 Fault-Tolerant Communication Between Nodes"
    ]
    cols = st.columns(2)
    for i, feat in enumerate(features):
        with cols[i % 2]:
            st.markdown(f"<div class='glass metric-box'>{feat}</div>", unsafe_allow_html=True)

# ---------------- ACCOUNT OPS ----------------
elif page == "Account Operations":
    st.subheader("💰 Account Operations")

    host = st.text_input("Branch Host", "127.0.0.1")
    port = st.text_input("Port", "9100")
    account = st.text_input("Account No", "1001")
    amount = st.text_input("Amount")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📊 Get Balance"):
            res = call_api("balance", data={"host": host, "port": port, "account": account})
            log_action("Get Balance", res, account, host, port)

    with col2:
        if st.button("💸 Deposit"):
            res = call_api("deposit", data={"host": host, "port": port, "account": account, "amount": amount})
            log_action("Deposit", res, account, host, port)

    with col3:
        if st.button("🏧 Withdraw"):
            res = call_api("withdraw", data={"host": host, "port": port, "account": account, "amount": amount})
            log_action("Withdraw", res, account, host, port)

    with col4:
        if st.button("📋 List Accounts"):
            res = call_api("list_accounts", method="get", params={"host": host, "port": port})
            log_action("List Accounts", res, account, host, port)

    st.markdown("<hr>", unsafe_allow_html=True)
    display_logs()  # ✅ show all logs
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------- TRANSFER ----------------
elif page == "Transfer Money":
    st.subheader("🔁 Transfer Money")

    col1, col2 = st.columns(2)
    with col1:
        src_host = st.text_input("From Host", "127.0.0.1")
        src_port = st.text_input("From Port", "9100")
        src_account = st.text_input("From Account", "1001")

    with col2:
        dest_host = st.text_input("To Host", "127.0.0.1")
        dest_port = st.text_input("To Port", "9200")
        dest_account = st.text_input("To Account", "2001")

    transfer_amount = st.text_input("💵 Transfer Amount")

    if st.button("🚀 Initiate Transfer"):
        res = call_api("transfer", data={
            "src_host": src_host, "src_port": src_port, "src_account": src_account,
            "dest_host": dest_host, "dest_port": dest_port, "dest_account": dest_account,
            "amount": transfer_amount
        })
        log_action("Transfer", res, src_account, src_host, src_port)
        st.success("✅ Transfer completed successfully!")

    st.markdown("<hr>", unsafe_allow_html=True)
    display_logs()  # ✅ show all logs
    st.markdown("</div>", unsafe_allow_html=True)
