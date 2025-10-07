# web_gui.py
import tkinter as tk
from tkinter import ttk
import requests
import json

BASE_URL = "http://127.0.0.1:5000"
REQUEST_TIMEOUT = 5  # seconds

# ---------------- Helper functions ----------------
def insert_output(message, tag="info"):
    """Insert message into output box with tag and auto-scroll."""
    if isinstance(message, (dict, list)):
        text = json.dumps(message, indent=2)
    else:
        text = str(message)
    output.configure(state="normal")
    output.insert(tk.END, text + "\n")
    output.tag_add(tag, f"end-{len(text.splitlines())}l", "end")
    output.see(tk.END)
    output.configure(state="disabled")

def format_response(resp):
    """Return parsed JSON if possible, otherwise raw text."""
    try:
        return resp.json()
    except Exception:
        return resp.text

# ---------------- Account operations ----------------
def get_balance():
    host = host_entry.get().strip()
    port = port_entry.get().strip()
    account = account_entry.get().strip()
    if not (host and port and account):
        insert_output("[Balance Error] fill host, port and account", "error")
        return
    try:
        resp = requests.post(f"{BASE_URL}/balance",
                             data={"host": host, "port": port, "account": account},
                             timeout=REQUEST_TIMEOUT)
        payload = format_response(resp)
        insert_output(payload, "success" if resp.ok else "error")
    except Exception as e:
        insert_output(f"[Balance Error] {e}", "error")

def deposit():
    host = host_entry.get().strip()
    port = port_entry.get().strip()
    account = account_entry.get().strip()
    amount = amount_entry.get().strip()
    if not (host and port and account and amount):
        insert_output("[Deposit Error] fill all fields", "error")
        return
    try:
        float(amount)
    except ValueError:
        insert_output("[Deposit Error] amount must be a number", "error")
        return
    try:
        resp = requests.post(f"{BASE_URL}/deposit",
                             data={"host": host, "port": port, "account": account, "amount": amount},
                             timeout=REQUEST_TIMEOUT)
        payload = format_response(resp)
        insert_output(payload, "success" if resp.ok else "error")
    except Exception as e:
        insert_output(f"[Deposit Error] {e}", "error")

def withdraw():
    host = host_entry.get().strip()
    port = port_entry.get().strip()
    account = account_entry.get().strip()
    amount = amount_entry.get().strip()
    if not (host and port and account and amount):
        insert_output("[Withdraw Error] fill all fields", "error")
        return
    try:
        float(amount)
    except ValueError:
        insert_output("[Withdraw Error] amount must be a number", "error")
        return
    try:
        resp = requests.post(f"{BASE_URL}/withdraw",
                             data={"host": host, "port": port, "account": account, "amount": amount},
                             timeout=REQUEST_TIMEOUT)
        payload = format_response(resp)
        insert_output(payload, "success" if resp.ok else "error")
    except Exception as e:
        insert_output(f"[Withdraw Error] {e}", "error")

def list_accounts():
    host = host_entry.get().strip()
    port = port_entry.get().strip()
    if not (host and port):
        insert_output("[List Accounts Error] fill host and port", "error")
        return
    try:
        resp = requests.get(f"{BASE_URL}/list_accounts",
                            params={"host": host, "port": port},
                            timeout=REQUEST_TIMEOUT)
        payload = format_response(resp)
        insert_output(payload, "success" if resp.ok else "error")
    except Exception as e:
        insert_output(f"[List Accounts Error] {e}", "error")

# ---------------- Transfer operations ----------------
def transfer():
    src_host = src_host_entry.get().strip()
    src_port = src_port_entry.get().strip()
    src_acc = src_account_entry.get().strip()
    dest_host = dest_host_entry.get().strip()
    dest_port = dest_port_entry.get().strip()
    dest_acc = dest_account_entry.get().strip()
    amount = transfer_amount_entry.get().strip()

    if not (src_host and src_port and src_acc and dest_host and dest_port and dest_acc and amount):
        insert_output("[Transfer Error] fill all transfer fields", "error")
        return
    try:
        float(amount)
    except ValueError:
        insert_output("[Transfer Error] amount must be a number", "error")
        return

    try:
        resp = requests.post(f"{BASE_URL}/transfer",
                             data={
                                 "src_host": src_host, "src_port": src_port, "src_account": src_acc,
                                 "dest_host": dest_host, "dest_port": dest_port, "dest_account": dest_acc,
                                 "amount": amount
                             },
                             timeout=REQUEST_TIMEOUT)
        payload = format_response(resp)
        insert_output(payload, "success" if resp.ok else "error")
    except Exception as e:
        insert_output(f"[Transfer Error] {e}", "error")

# ---------------- Build GUI ----------------
root = tk.Tk()
root.title("🏦 Distributed Bank Client")
root.geometry("900x700")

style = ttk.Style()
# Optional: set theme if available
try:
    style.theme_use("clam")
except Exception:
    pass
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
style.configure("TEntry", padding=4)

# --- Account frame ---
frame_acc = ttk.LabelFrame(root, text="Account Operations", padding=(12, 10))
frame_acc.pack(fill="x", padx=12, pady=(12, 6))

ttk.Label(frame_acc, text="Branch Host").grid(row=0, column=0, sticky="w", padx=4, pady=4)
host_entry = ttk.Entry(frame_acc, width=28); host_entry.grid(row=0, column=1, pady=4, padx=4)
host_entry.insert(0, "127.0.0.1")

ttk.Label(frame_acc, text="Port").grid(row=1, column=0, sticky="w", padx=4, pady=4)
port_entry = ttk.Entry(frame_acc, width=28); port_entry.grid(row=1, column=1, pady=4, padx=4)
port_entry.insert(0, "9100")

ttk.Label(frame_acc, text="Account No").grid(row=2, column=0, sticky="w", padx=4, pady=4)
account_entry = ttk.Entry(frame_acc, width=28); account_entry.grid(row=2, column=1, pady=4, padx=4)
account_entry.insert(0, "1001")

ttk.Label(frame_acc, text="Amount").grid(row=3, column=0, sticky="w", padx=4, pady=4)
amount_entry = ttk.Entry(frame_acc, width=28); amount_entry.grid(row=3, column=1, pady=4, padx=4)

# Buttons for account ops
btn_frame = ttk.Frame(frame_acc)
btn_frame.grid(row=0, column=2, rowspan=4, padx=12, sticky="ns")
ttk.Button(btn_frame, text="Balance", command=get_balance).pack(fill="x", pady=4)
ttk.Button(btn_frame, text="Deposit", command=deposit).pack(fill="x", pady=4)
ttk.Button(btn_frame, text="Withdraw", command=withdraw).pack(fill="x", pady=4)
ttk.Button(btn_frame, text="List Accounts", command=list_accounts).pack(fill="x", pady=4)

# --- Transfer frame ---
frame_trans = ttk.LabelFrame(root, text="Transfer Operations", padding=(12, 10))
frame_trans.pack(fill="x", padx=12, pady=(6, 6))

labels_trans = ["From Host", "From Port", "From Account",
                "To Host", "To Port", "To Account", "Transfer Amount"]

entries_trans = {}
for i, lbl in enumerate(labels_trans):
    ttk.Label(frame_trans, text=lbl).grid(row=i, column=0, sticky="w", padx=4, pady=4)
    entry = ttk.Entry(frame_trans, width=28)
    entry.grid(row=i, column=1, pady=4, padx=4)
    entries_trans[lbl] = entry

# Assign references for code
src_host_entry = entries_trans["From Host"]
src_port_entry = entries_trans["From Port"]
src_account_entry = entries_trans["From Account"]
dest_host_entry = entries_trans["To Host"]
dest_port_entry = entries_trans["To Port"]
dest_account_entry = entries_trans["To Account"]
transfer_amount_entry = entries_trans["Transfer Amount"]

# Small Transfer button (no rowspan, no stretching)
ttk.Button(frame_trans, text="Transfer", command=transfer).grid(row=len(labels_trans), column=0, columnspan=2, pady=8)

# --- Output frame ---
frame_out = ttk.LabelFrame(root, text="Output", padding=(8, 8))
frame_out.pack(fill="both", expand=True, padx=12, pady=(6, 12))

output = tk.Text(frame_out, height=14, wrap="none", font=("Consolas", 10))
output.pack(fill="both", expand=True)
output.configure(state="disabled")
# color tags
output.tag_config("success", foreground="green")
output.tag_config("error", foreground="red")
output.tag_config("info", foreground="blue")

# start the GUI
root.mainloop()
