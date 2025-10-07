# ui_server.py
from flask import Flask, request, jsonify
from protocol import send_request
import requests

app = Flask(__name__)

@app.route("/balance", methods=["POST"])
def balance():
    host = request.form["host"]
    port = int(request.form["port"])
    account = request.form["account"]
    resp = send_request(host, port, "balance", {"account_no": account})
    return jsonify(resp)

@app.route("/deposit", methods=["POST"])
def deposit():
    host = request.form["host"]
    port = int(request.form["port"])
    account = request.form["account"]
    amount = float(request.form["amount"])
    resp = send_request(host, port, "deposit", {"account_no": account, "amount": amount})
    return jsonify(resp)

@app.route("/withdraw", methods=["POST"])
def withdraw():
    host = request.form["host"]
    port = int(request.form["port"])
    account = request.form["account"]
    amount = float(request.form["amount"])
    resp = send_request(host, port, "withdraw", {"account_no": account, "amount": amount})
    return jsonify(resp)

@app.route("/list_accounts", methods=["GET"])
def list_accounts():
    host = request.args.get("host", "127.0.0.1")
    port = int(request.args.get("port"))
    try:
        resp = send_request(host, port, "list_accounts", {})
        return jsonify(resp)
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route("/transfer", methods=["POST"])
def transfer():
    src_host = request.form["src_host"]
    src_port = int(request.form["src_port"])
    src_account = request.form["src_account"]
    dest_host = request.form["dest_host"]
    dest_port = int(request.form["dest_port"])
    dest_account = request.form["dest_account"]
    amount = float(request.form["amount"])

    if src_host == dest_host and src_port == dest_port:
        # Local transfer
        params = {
            "src_account_no": src_account,
            "dest_account_no": dest_account,
            "amount": amount,
        }
        resp = send_request(src_host, src_port, "local_transfer", params)
    else:
        # Inter-branch transfer
        params = {
            "src_account_no": src_account,
            "dest_host": dest_host,
            "dest_port": dest_port,
            "dest_account_no": dest_account,
            "amount": amount,
        }
        resp = send_request(src_host, src_port, "inter_branch_transfer", params)

    return jsonify(resp)

# ----- new endpoint to fetch logs for an account -----
@app.route("/get_logs", methods=["POST"])
def get_logs():
    host = request.form["host"]
    port = int(request.form["port"])
    account = request.form["account"]
    resp = send_request(host, port, "get_logs", {"account_no": account})
    return jsonify(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
