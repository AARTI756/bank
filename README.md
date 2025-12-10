# 🏦 Smart Distributed Banking System

A **distributed banking system** that demonstrates **real-world distributed computing principles** — including **replication**, **fault tolerance**, **atomic transactions**, and **the Two-Phase Commit (2PC) protocol**.  
Each branch runs as an **independent database node** with its own local state, coordinated through a **Flask REST bridge** and a **modern Streamlit dashboard**.

---

## ✨ Key Highlights

✅ **Multi-Branch Architecture** — Each branch is an independent database server  
✅ **Two-Phase Commit (2PC)** — Guarantees atomic cross-branch transfers  
✅ **Persistent Operation Logs** — All transactions stored and downloadable  
✅ **Modern Streamlit UI** — Interactive real-time interface  
✅ **Flask Bridge (REST API)** — Central controller for distributed coordination  
✅ **Fault-Tolerant Design** — Handles branch or connection failures gracefully  
✅ **Scalable** — Easily extend to more branches (nodes)  

---

## 🧠 Core Distributed Systems Concepts Demonstrated

| Concept | Explanation |
|----------|--------------|
| 🧩 **Decentralization** | Each branch maintains its own database (`Mumbai.db`, `Delhi.db`) instead of relying on a central server. |
| 🔁 **Replication** | Data updates can propagate to replicas (for high availability). |
| 🔄 **Two-Phase Commit (2PC)** | Ensures distributed atomicity — a transaction either commits everywhere or nowhere. |
| ⏱ **Concurrency Control** | Simultaneous requests are handled safely per branch using local database locks. |
| ⚖️ **Consistency** | Account balances remain consistent across branches even during failures. |
| 💥 **Fault Tolerance** | If one branch crashes mid-transfer, 2PC ensures system-wide rollback. |
| 📡 **Transparency** | The Flask bridge hides the complexity of distributed communication from the user. |

This project acts as a **miniature model of how distributed databases and banking systems (like HDFC or SBI)** maintain transactional safety across multiple branches.

---

## ⚙️ Requirements

* Python **3.8+** (tested on 3.10)
* Install dependencies:
```bash
pip install flask requests streamlit pandas
````

(`sqlite3` is built-in to Python.)

---

## 📂 Project Structure

```
bankmain/
│── branch_server.py       # TCP server for each bank branch
│── client.py              # CLI client for socket operations
│── ui_server.py           # Flask bridge exposing REST endpoints
│── web_gui_streamlit.py   # Streamlit web dashboard
│── operation_logs.csv     # Auto-generated persistent log file
│── README.md              # Project documentation
```

---

## 🚀 Running the Project

### 1️⃣ Start Branch Servers

Each branch runs independently with its own database:

```bash
# Mumbai branch
python branch_server.py --host 127.0.0.1 --port 9100 --name Mumbai --preload

# Delhi branch
python branch_server.py --host 127.0.0.1 --port 9101 --name Delhi --preload
```

> `--preload` creates default accounts (1001, 1002) if empty
> `--replicas` (optional) connects multiple branches for data synchronization

---

### 2️⃣ Start the Flask HTTP Bridge

```bash
python ui_server.py
```

Default: [http://127.0.0.1:5000](http://127.0.0.1:5000)

### 3️⃣ Start the Web Dashboard (Streamlit)

```bash
python -m streamlit run web_gui_streamlit.py
```

Open [http://localhost:8501](http://localhost:8501)

🎛 **Dashboard Features**

* 💰 Deposit & Withdraw
* 🔁 Inter-branch transfer (2PC-based)
* 🧾 Real-time operation logs
* 📥 Export logs per account or all accounts
* 🧹 Clear logs option
* 🌐 Multi-branch connectivity

---

## 🔄 How the 2PC Protocol Works

### 🧩 **Phase 1: Prepare**

1. Source branch locks funds and prepares withdrawal
2. Destination branch prepares deposit

### 🧩 **Phase 2: Commit / Abort**

* If both confirm readiness → Commit on both sides
* If one fails → Abort and rollback all changes

✅ Ensures **atomicity**, **consistency**, and **reliability** in distributed transactions.

---

Here’s a **shorter and cleaner** version of the **Multi-Device Setup (with IP example)** — compact but still clear 👇

---

## 🌍 Multi-Device Setup (Example)

Run different branches on separate machines connected via LAN or Wi-Fi.

| Device         | Branch | IP             | Port   |
| -------------- | ------ | -------------- | ------ |
| 💻 Laptop A    | Mumbai | `192.168.1.10` | `9100` |
| 🖥️ Laptop B   | Delhi  | `192.168.1.20` | `9101` |
| 🌐 Flask + GUI | Bridge | `192.168.1.10` | `5000` |

---

### 🏦 Start Branch Servers

**Mumbai (Laptop A):**

```bash
python branch_server.py --host 0.0.0.0 --port 9100 --name Mumbai --preload
```

**Delhi (Laptop B):**

```bash
python branch_server.py --host 0.0.0.0 --port 9101 --name Delhi --preload
```

---

### 🌉 Start Flask Bridge

Run on Laptop A:

```bash
python ui_server.py --host 0.0.0.0 --port 5000
```

Access at → `http://192.168.1.10:5000`

---

### 🖥️ Configure GUI (Streamlit)

In `web_gui_streamlit.py`:

```python
BASE_URL = "http://192.168.1.10:5000"
```

Then launch:

```bash
python -m streamlit run web_gui_streamlit.py
```

Open in browser → [http://192.168.1.10:8501](http://192.168.1.10:8501)

---

### 🔁 Example Transfer

Transfer ₹500 from **Mumbai (192.168.1.10:9100)** → **Delhi (192.168.1.20:9101)**
via Flask Bridge `192.168.1.10:5000` using **2PC protocol**.

## 📸 Application Screenshots

### 🏦 Dashboard View
![Dashboard UI](https://github.com/AARTI756/bank/blob/main/ss/dashboard.png)

### 📂 Account Operations
![Account UI](https://github.com/AARTI756/bank/blob/main/ss/account.png)

### 💸 Transfer Money
![Transfer UI](https://github.com/AARTI756/bank/blob/main/ss/transfer.png)


## 🎥 Demo Video

(https://github.com/AARTI756/bank/blob/main/bank.mp4)
