import argparse
import socket
import threading
import sqlite3
import time
import random
import json
import sys
from typing import Dict, Any, List, Tuple, Optional

from protocol import send_msg, recv_msg, send_request

REPL_RETRY = 2     # number of replication retries
REPL_TIMEOUT = 2   # seconds per replication attempt

class BranchServer:
    def __init__(self, host: str, port: int, name: str, preload: bool = False, replicas: List[Tuple[str,int]] = None):
        self.host = host
        self.port = port
        self.name = name
        self.replicas = replicas or []   # list of (host,port) tuples
        self.lock = threading.Lock()

        # sqlite DB per branch
        self.db_file = f"{name}.db"
        # use check_same_thread False for multi-threaded access; commit explicitly
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False, isolation_level=None)
        self.cur = self.conn.cursor()
        self._init_db()

        if preload:
            self._preload_accounts()

        # recover any pending transactions
        self.recover_pending()

        # action -> handler
        self.handlers = {
            # basic
            "create_account": self.handle_create_account,
            "list_accounts": self.handle_list_accounts,
            "balance": self.handle_balance,
            "deposit": self.handle_deposit,         # immediate deposit (non-2PC)
            "withdraw": self.handle_withdraw,       # immediate withdraw (non-2PC)
            # 2PC endpoints used during inter-branch transfer
            "prepare_withdraw": self.handle_prepare_withdraw,
            "commit_withdraw": self.handle_commit_withdraw,
            "abort_withdraw": self.handle_abort_withdraw,
            "prepare_deposit": self.handle_prepare_deposit,
            "commit_deposit": self.handle_commit_deposit,
            "abort_deposit": self.handle_abort_deposit,
            # transfer coordinator (start transfer from this branch)
            "inter_branch_transfer": self.handle_inter_branch_transfer,
            "local_transfer": self.handle_local_transfer,

            # replication handler (applies a replicated update)
            "replicate": self.handle_replicate,
        }

    # ---------- DB ----------
    def _init_db(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS accounts (
                            account_no TEXT PRIMARY KEY,
                            name TEXT,
                            balance REAL
                            )""")
        # pending 2PC records: txid, account_no, amount, type ('withdraw'|'deposit')
        self.cur.execute("""CREATE TABLE IF NOT EXISTS pending_tx (
                            txid TEXT PRIMARY KEY,
                            account_no TEXT,
                            amount REAL,
                            type TEXT
                            )""")
        self.conn.commit()

    def _preload_accounts(self):
        # add two sample accounts if none exist
        self.cur.execute("SELECT COUNT(*) FROM accounts")
        if self.cur.fetchone()[0] == 0:
            for i in range(1, 3):
                acc = str(1000 + i)
                self.cur.execute("INSERT OR IGNORE INTO accounts (account_no, name, balance) VALUES (?, ?, ?)",
                                 (acc, f"User_{self.name}_{i}", 1000.0))
            self.conn.commit()

    def recover_pending(self):
        self.cur.execute("SELECT txid, account_no, amount, type FROM pending_tx")
        rows = self.cur.fetchall()
        if not rows:
            return
        print(f"[{self.name}] Recovering {len(rows)} pending transactions (aborting them).")
        for txid, acc, amt, typ in rows:
            print(f"[{self.name}] Aborting leftover tx {txid} type={typ} acc={acc}")
            self.cur.execute("DELETE FROM pending_tx WHERE txid=?", (txid,))
        self.conn.commit()

    # ---------- Helpers ----------
    def get_account(self, account_no: str) -> Optional[Dict[str,Any]]:
        self.cur.execute("SELECT account_no, name, balance FROM accounts WHERE account_no=?", (account_no,))
        r = self.cur.fetchone()
        if not r:
            return None
        return {"account_no": r[0], "name": r[1], "balance": float(r[2])}

    def update_balance(self, account_no: str, new_bal: float) -> None:
        self.cur.execute("UPDATE accounts SET balance=? WHERE account_no=?", (new_bal, account_no))
        self.conn.commit()

    def list_accounts(self) -> List[Dict[str,Any]]:
        self.cur.execute("SELECT account_no, name, balance FROM accounts")
        return [{"account_no": a, "name": n, "balance": float(b)} for (a,n,b) in self.cur.fetchall()]

    # Replication: best-effort apply to replicas
    def replicate_to_replicas(self, action: str, params: Dict[str,Any]) -> List[Dict[str,Any]]:
        results = []
        for (h,p) in self.replicas:
            last_err = None
            for attempt in range(REPL_RETRY):
                resp = send_request(h, p, "replicate", {"action": action, "params": params}, timeout=REPL_TIMEOUT)
                if resp.get("status") == "ok":
                    results.append({"replica": f"{h}:{p}", "ok": True})
                    break
                else:
                    last_err = resp.get("error")
                    time.sleep(0.1)
            else:
                results.append({"replica": f"{h}:{p}", "ok": False, "error": last_err})
        return results

    # ---------- Handlers: basic operations ----------
    def handle_create_account(self, params: Dict[str,Any]) -> Dict[str,Any]:
        acc = params.get("account_no")
        name = params.get("name", "")
        bal = float(params.get("balance", 0.0))
        if not acc:
            return {"status":"error", "error": "missing account_no"}
        with threading.Lock():
            if self.get_account(acc):
                return {"status":"error", "error":"account exists"}
            self.cur.execute("INSERT INTO accounts (account_no, name, balance) VALUES (?, ?, ?)",
                             (acc, name, bal))
            self.conn.commit()
        # replicate create to replicas (best effort)
        self.replicate_to_replicas("create_account", {"account_no": acc, "name": name, "balance": bal})
        return {"status":"ok", "result": "account created"}

    def handle_list_accounts(self, params: Dict[str,Any]) -> Dict[str,Any]:
        return {"status":"ok", "result": self.list_accounts()}

    def handle_balance(self, params: Dict[str,Any]) -> Dict[str,Any]:
        acc = params.get("account_no")
        if not acc:
            return {"status":"error","error":"missing account_no"}
        acct = self.get_account(acc)
        if not acct:
            return {"status":"error","error":"account not found"}
        return {"status":"ok", "result": {"balance": acct["balance"], "name": acct["name"]}}

    # Immediate deposit/withdraw used by UI (non 2PC)
    def handle_deposit(self, params: Dict[str,Any]) -> Dict[str,Any]:
        acc = params.get("account_no")
        try:
            amt = float(params.get("amount", 0.0))
        except Exception:
            return {"status":"error","error":"invalid amount"}
        if not acc:
            return {"status":"error","error":"missing account_no"}
        with self.lock:
            acct = self.get_account(acc)
            if not acct:
                return {"status":"error","error":"account not found"}
            new_bal = acct["balance"] + amt
            self.update_balance(acc, new_bal)
        # replicate deposit (best effort)
        self.replicate_to_replicas("deposit", {"account_no": acc, "amount": amt})
        return {"status":"ok", "result": {"balance": new_bal}}

    def handle_withdraw(self, params: Dict[str,Any]) -> Dict[str,Any]:
        acc = params.get("account_no")
        try:
            amt = float(params.get("amount", 0.0))
        except Exception:
            return {"status":"error","error":"invalid amount"}
        if not acc:
            return {"status":"error","error":"missing account_no"}
        with self.lock:
            acct = self.get_account(acc)
            if not acct:
                return {"status":"error","error":"account not found"}
            if acct["balance"] < amt:
                return {"status":"error","error":"insufficient funds"}
            new_bal = acct["balance"] - amt
            self.update_balance(acc, new_bal)
        # replicate withdraw (best effort)
        self.replicate_to_replicas("withdraw", {"account_no": acc, "amount": amt})
        return {"status":"ok", "result": {"balance": new_bal}}

    # ---------- 2PC handlers for withdraw (source) ----------
    def handle_prepare_withdraw(self, params: Dict[str,Any]) -> Dict[str,Any]:
        txid = params.get("txid")
        acc = params.get("account_no")
        try:
            amt = float(params.get("amount", 0.0))
        except Exception:
            return {"status":"error","error":"invalid amount"}
        if not txid or not acc:
            return {"status":"error","error":"missing txid/account_no"}
        with self.lock:
            acct = self.get_account(acc)
            if not acct or acct["balance"] < amt:
                return {"status":"error","error":"insufficient funds or account not found"}
            # store pending withdraw (no balance change)
            self.cur.execute("INSERT OR REPLACE INTO pending_tx (txid, account_no, amount, type) VALUES (?, ?, ?, ?)",
                             (txid, acc, amt, "withdraw"))
            self.conn.commit()
        return {"status":"ok"}

    def handle_commit_withdraw(self, params: Dict[str,Any]) -> Dict[str,Any]:
        txid = params.get("txid")
        if not txid:
            return {"status":"error","error":"missing txid"}
        with self.lock:
            self.cur.execute("SELECT account_no, amount FROM pending_tx WHERE txid=? AND type='withdraw'", (txid,))
            row = self.cur.fetchone()
            if not row:
                return {"status":"error","error":"no such tx"}
            acc, amt = row
            acct = self.get_account(acc)
            if not acct:
                # cleanup
                self.cur.execute("DELETE FROM pending_tx WHERE txid=?", (txid,))
                self.conn.commit()
                return {"status":"error","error":"account not found"}
            if acct["balance"] < amt:
                # cannot commit
                self.cur.execute("DELETE FROM pending_tx WHERE txid=?", (txid,))
                self.conn.commit()
                return {"status":"error","error":"insufficient funds at commit"}
            new_bal = acct["balance"] - amt
            self.update_balance(acc, new_bal)
            self.cur.execute("DELETE FROM pending_tx WHERE txid=?", (txid,))
            self.conn.commit()
        # replicate final withdraw (best effort)
        self.replicate_to_replicas("withdraw", {"account_no": acc, "amount": amt})
        return {"status":"ok"}

    def handle_abort_withdraw(self, params: Dict[str,Any]) -> Dict[str,Any]:
        txid = params.get("txid")
        if not txid:
            return {"status":"error","error":"missing txid"}
        with self.lock:
            self.cur.execute("DELETE FROM pending_tx WHERE txid=? AND type='withdraw'", (txid,))
            self.conn.commit()
        return {"status":"ok"}

    # ---------- 2PC handlers for deposit (destination) ----------
    def handle_prepare_deposit(self, params: Dict[str,Any]) -> Dict[str,Any]:
        txid = params.get("txid")
        acc = params.get("account_no")
        try:
            amt = float(params.get("amount", 0.0))
        except Exception:
            return {"status":"error","error":"invalid amount"}
        if not txid or not acc:
            return {"status":"error","error":"missing txid/account_no"}
        with self.lock:
            acct = self.get_account(acc)
            if not acct:
                return {"status":"error","error":"destination account not found"}
            # record pending deposit
            self.cur.execute("INSERT OR REPLACE INTO pending_tx (txid, account_no, amount, type) VALUES (?, ?, ?, ?)",
                             (txid, acc, amt, "deposit"))
            self.conn.commit()
        return {"status":"ok"}

    def handle_commit_deposit(self, params: Dict[str,Any]) -> Dict[str,Any]:
        txid = params.get("txid")
        if not txid:
            return {"status":"error","error":"missing txid"}
        with self.lock:
            self.cur.execute("SELECT account_no, amount FROM pending_tx WHERE txid=? AND type='deposit'", (txid,))
            row = self.cur.fetchone()
            if not row:
                return {"status":"error","error":"no such tx"}
            acc, amt = row
            acct = self.get_account(acc)
            if not acct:
                self.cur.execute("DELETE FROM pending_tx WHERE txid=?", (txid,))
                self.conn.commit()
                return {"status":"error","error":"account not found"}
            new_bal = acct["balance"] + amt
            self.update_balance(acc, new_bal)
            self.cur.execute("DELETE FROM pending_tx WHERE txid=?", (txid,))
            self.conn.commit()
        # replicate deposit (best effort)
        self.replicate_to_replicas("deposit", {"account_no": acc, "amount": amt})
        return {"status":"ok"}

    def handle_abort_deposit(self, params: Dict[str,Any]) -> Dict[str,Any]:
        txid = params.get("txid")
        if not txid:
            return {"status":"error","error":"missing txid"}
        with self.lock:
            self.cur.execute("DELETE FROM pending_tx WHERE txid=? AND type='deposit'", (txid,))
            self.conn.commit()
        return {"status":"ok"}

    # ---------- Inter-branch transfer coordinator (2PC) ----------
    def handle_inter_branch_transfer(self, params: Dict[str,Any]) -> Dict[str,Any]:
        """
        params expected:
            src_account_no, dest_host, dest_port, dest_account_no, amount
        This branch is coordinator (source branch).
        Steps:
            1) local prepare_withdraw(txid)
            2) remote prepare_deposit(txid) on dest_host:dest_port
            3) commit local withdraw
            4) commit remote deposit
        This ordering minimizes lost money if remote commit fails (we commit local first then remote).
        """
        src_acc = params.get("src_account_no")
        dest_host = params.get("dest_host")
        dest_port = int(params.get("dest_port"))
        dest_acc = params.get("dest_account_no")
        try:
            amount = float(params.get("amount"))
        except Exception:
            return {"status":"error","error":"invalid amount"}
        if not (src_acc and dest_host and dest_port and dest_acc):
            return {"status":"error","error":"missing parameters"}

        txid = f"{self.name}-{int(time.time()*1000)}-{random.randint(1000,9999)}"
        # 1) prepare local withdraw
        prep_local = self.handle_prepare_withdraw({"txid": txid, "account_no": src_acc, "amount": amount})
        if prep_local.get("status") != "ok":
            return {"status":"error","error":"local prepare failed: " + str(prep_local)}

        # 2) ask dest to prepare deposit
        resp = send_request(dest_host, dest_port, "prepare_deposit",
                            {"txid": txid, "account_no": dest_acc, "amount": amount})
        if resp.get("status") != "ok":
            # abort local
            self.handle_abort_withdraw({"txid": txid})
            return {"status":"error","error":"destination prepare failed: " + str(resp)}

        # 3) commit local withdraw
        commit_local = self.handle_commit_withdraw({"txid": txid})
        if commit_local.get("status") != "ok":
            # best-effort abort remote
            send_request(dest_host, dest_port, "abort_deposit", {"txid": txid})
            return {"status":"error","error":"local commit failed: " + str(commit_local)}

        # 4) commit remote deposit
        commit_remote = send_request(dest_host, dest_port, "commit_deposit", {"txid": txid})
        if commit_remote.get("status") != "ok":
            # at this point local already committed -> inconsistent unless we do compensation
            # Attempt best-effort: notify remote abort (already tried) and return error
            return {"status":"error","error":"remote commit failed: " + str(commit_remote)}

        return {"status":"ok", "result": {"status":"transfer_complete", "txid": txid, "amount": amount,
                                         "from": f"{self.name}:{src_acc}", "to": f"{dest_host}:{dest_acc}"}}



    def handle_local_transfer(self, params: Dict[str, Any]) -> Dict[str, Any]:
            src_acc = params.get("src_account_no")
            dest_acc = params.get("dest_account_no")
            try:
                amount = float(params.get("amount", 0.0))
            except Exception:
                return {"status": "error", "error": "invalid amount"}
            if not (src_acc and dest_acc):
                return {"status": "error", "error": "missing account numbers"}
            return self.local_transfer(src_acc, dest_acc, amount)


        # ---------- Local transfer (within same branch) ----------
    def local_transfer(self, src_account: str, dest_account: str, amount: float) -> Dict[str, Any]:
        """Simple atomic transfer within this branch."""
        with self.lock:
            src = self.get_account(src_account)
            dest = self.get_account(dest_account)
            if not src:
                return {"status": "error", "error": "source account not found"}
            if not dest:
                return {"status": "error", "error": "destination account not found"}
            if src["balance"] < amount:
                return {"status": "error", "error": "insufficient funds"}

            # update balances atomically
            new_src_bal = src["balance"] - amount
            new_dest_bal = dest["balance"] + amount
            self.update_balance(src_account, new_src_bal)
            self.update_balance(dest_account, new_dest_bal)

        # replicate both updates (best effort)
        self.replicate_to_replicas("withdraw", {"account_no": src_account, "amount": amount})
        self.replicate_to_replicas("deposit", {"account_no": dest_account, "amount": amount})

        return {"status": "ok", "result": {
            "from": {"account": src_account, "balance": new_src_bal},
            "to": {"account": dest_account, "balance": new_dest_bal},
            "amount": amount
        }}

    # ---------- Replicate handler (called by primary to replicas) ----------
    def handle_replicate(self, params: Dict[str,Any]) -> Dict[str,Any]:
        """
        receive replicate messages:
          params: {"action": "<action>", "params": {...}}
        We apply a subset of actions locally (create_account / deposit / withdraw).
        This is simple best-effort replication apply on replica servers.
        """
        data = params.get("data") or params  # support either form
        action = data.get("action")
        p = data.get("params", {})
        # Only accept certain write ops on replica: create_account, deposit, withdraw
        if action == "create_account":
            acc = p.get("account_no"); name = p.get("name"); bal = float(p.get("balance",0.0))
            with self.lock:
                if not self.get_account(acc):
                    self.cur.execute("INSERT OR IGNORE INTO accounts (account_no, name, balance) VALUES (?, ?, ?)",
                                     (acc, name, bal))
                    self.conn.commit()
            return {"status":"ok"}
        if action == "deposit":
            acc = p.get("account_no"); amt = float(p.get("amount",0.0))
            with self.lock:
                acct = self.get_account(acc)
                if acct:
                    new_bal = acct["balance"] + amt
                    self.update_balance(acc, new_bal)
            return {"status":"ok"}
        if action == "withdraw":
            acc = p.get("account_no"); amt = float(p.get("amount",0.0))
            with self.lock:
                acct = self.get_account(acc)
                if acct:
                    new_bal = acct["balance"] - amt
                    self.update_balance(acc, new_bal)
            return {"status":"ok"}
        # other replicate actions are no-op on replica
        return {"status":"ok"}

    # ---------- Network server ----------
    def start(self):
        print(f"[{self.name}] Server listening on {self.host}:{self.port} (replicas={self.replicas})")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(50)
        try:
            while True:
                conn, _ = sock.accept()
                threading.Thread(target=self._client_thread, args=(conn,), daemon=True).start()
        finally:
            sock.close()

    def _client_thread(self, conn: socket.socket):
        try:
            req = recv_msg(conn)
            if not req:
                conn.close(); return
            action = req.get("action")
            params = req.get("params", {}) or {}
            handler = self.handlers.get(action)
            if not handler:
                send_msg(conn, {"status":"error","error":f"unknown action {action}"})
            else:
                try:
                    res = handler(params)
                    send_msg(conn, res if isinstance(res, dict) else {"status":"ok", "result": res})
                except Exception as e:
                    send_msg(conn, {"status":"error","error":str(e)})
        except Exception as e:
            try:
                send_msg(conn, {"status":"error","error":str(e)})
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass


# CLI runner
def parse_replicas(rep_arg: str) -> List[Tuple[str,int]]:
    try:
        lst = json.loads(rep_arg)
        out = []
        for item in lst:
            if isinstance(item, (list,tuple)) and len(item) >= 2:
                out.append((item[0], int(item[1])))
            elif isinstance(item, str) and ":" in item:
                h,p = item.split(":"); out.append((h,int(p)))
        return out
    except Exception:
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--preload", action="store_true")
    parser.add_argument("--replicas", type=str, default="[]",
                        help='JSON list of replicas, e.g. \'[["127.0.0.1",9001],["127.0.0.1",9002]]\'')
    args = parser.parse_args()

    replicas = parse_replicas(args.replicas)
    server = BranchServer(args.host, args.port, args.name, preload=args.preload, replicas=replicas)
    try:
        server.start()
    except KeyboardInterrupt:
        print("shutting down")
        try:
            server.conn.close()
        except Exception:
            pass
        sys.exit(0)
