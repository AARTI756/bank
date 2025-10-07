# 🏦 Distributed Banking System

A distributed banking demo where multiple **branch servers** run independently with their own SQLite databases.
A **Flask bridge** exposes REST APIs, and a **Streamlit dashboard** provides a modern web interface for operations like deposits, withdrawals, and inter-branch transfers using a **Two-Phase Commit (2PC)** protocol.

## ✨ Features

* 🏦 **Multi-branch architecture** — each branch = independent server + database
* 🔗 **Two-phase commit (2PC)** for **inter-branch transfers**
* 💰 Local atomic transactions (deposit, withdraw, balance check)
* 🌍 **Multi-device support** (branches on different machines)
* 🌐 REST API bridge (`ui_server.py`) with Flask
* 📊 Modern **web dashboard** with Streamlit
* 🖥️ CLI client (`client.py`) for direct socket operations
* 🔄 Replication support (optional, best effort)


## ⚙️ Requirements

* Python **3.8+** (tested on 3.10)
* Install dependencies:

```bash
pip install requests Flask streamlit
```

(`sqlite3` is built into Python, no need to install separately.)

## 🗂 Project Structure

```
banking-system/
│── branch_server.py      # TCP server for branch operations
│── client.py             # CLI client for testing branches directly
│── ui_server.py          # Flask HTTP bridge → REST endpoints
│── web_gui_streamlit.py  # Modern web dashboard (Streamlit)
│── README.md             # Documentation
```

## 🚀 Running the Project
### 1️⃣ Start Branch Servers
Each branch runs in its own terminal:

```bash
# Mumbai branch
python branch_server.py --host 127.0.0.1 --port 9100 --name Mumbai --preload

# Delhi branch
python branch_server.py --host 127.0.0.1 --port 9101 --name Delhi --preload
```

* `--preload` = creates sample accounts (`1001`, `1002`) if empty
* `--replicas` = optional replication peers

### 2️⃣ Start the Flask HTTP Bridge

```bash
python ui_server.py
```

Default: runs at [http://127.0.0.1:5000](http://127.0.0.1:5000)

Exposes endpoints:

* `POST /balance`
* `POST /deposit`
* `POST /withdraw`
* `GET /list_accounts`
* `POST /transfer`

### 3️⃣ Start the Web Dashboard (Streamlit)

```bash
python -m streamlit run web_gui_streamlit.py
```

Opens at → [http://localhost:8501](http://localhost:8501)

Dashboard allows:

* 📋 List accounts
* 💵 Deposit / Withdraw
* 🔄 Local transfers
* 🌍 Inter-branch transfers via 2PC

### 4️⃣ CLI Client (Direct TCP Calls)

```bash
# Balance
python client.py --host 127.0.0.1 --port 9100 balance --account_no 1001

# Deposit
python client.py --host 127.0.0.1 --port 9100 deposit --account_no 1001 --amount 100

# Inter-branch transfer
python client.py --host 127.0.0.1 --port 9100 inter_branch_transfer \
  --src_account_no 1001 --dest_host 127.0.0.1 --dest_port 9101 \
  --dest_account_no 1002 --amount 50
```


## 🔄 How Transfers Work

* **Local transfer** (same branch) → one DB transaction
* **Inter-branch transfer** → 2PC protocol:

1. **Prepare withdraw** on source branch
2. **Prepare deposit** on destination branch
3. If both succeed → **commit both**
4. If one fails → **abort all**





## 🌍 Multi-Device Setup

You can run different branches on **different machines** (e.g., Mumbai on Laptop A, Delhi on Laptop B).

### Steps:

#### 1. Start Branch Servers with LAN Access

On **Device A** (Mumbai, IP: `192.168.1.50`):

```bash
python branch_server.py --host 0.0.0.0 --port 9100 --name Mumbai --preload
```

On **Device B** (Delhi, IP: `192.168.1.51`):

```bash
python branch_server.py --host 0.0.0.0 --port 9101 --name Delhi --preload
```

> Use `--host 0.0.0.0` to allow LAN connections.

---

#### 2. Start Flask Bridge on One Device

On Device A:

```bash
python ui_server.py --host 0.0.0.0 --port 5000
```

Now available at:
👉 `http://192.168.1.50:5000`

---

#### 3. Update GUI Config

In `web_gui_streamlit.py`, set:

```python
BASE_URL = "http://192.168.1.50:5000"
```

Run GUI from **any device**:

```bash
python -m streamlit run web_gui_streamlit.py
```

#### 4. Example Transfer Across Devices

* Source: Mumbai (`192.168.1.50:9100`)
* Destination: Delhi (`192.168.1.51:9101`)
* Flask bridge coordinates 2PC.

## 🛠 Troubleshooting

* **Connection refused** → server not running or wrong IP/port
* **Firewall blocked** → allow ports `9100`, `9101`, `5000`
* **GUI not updating** → check `BASE_URL` in `web_gui_streamlit.py`
* **Different networks** → use VPN (e.g., Tailscale, ZeroTier)

## 🌟 Future Enhancements

* 🔍 Auto-discovery of branches
* 🔑 Authentication & security
* 🗄 Persistent transaction logs (WAL)
* 🐳 Dockerized deployment
