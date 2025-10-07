# client.py
import argparse
import json
from protocol import send_request

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, required=True)
    p.add_argument("action", help="create_account | list_accounts | balance | deposit | withdraw | inter_branch_transfer")
    p.add_argument("--account_no")
    p.add_argument("--name")
    p.add_argument("--amount", type=float)
    # for transfer:
    p.add_argument("--dest_host")
    p.add_argument("--dest_port", type=int)
    p.add_argument("--dest_account_no")
    p.add_argument("--src_account_no")
    args = p.parse_args()

    action = args.action

    params = {}
    if args.account_no:
        params["account_no"] = args.account_no
    if args.name:
        params["name"] = args.name
    if args.amount is not None:
        params["amount"] = args.amount

    if action == "inter_branch_transfer":
        params = {
            "src_account_no": args.src_account_no,
            "dest_host": args.dest_host,
            "dest_port": args.dest_port,
            "dest_account_no": args.dest_account_no,
            "amount": args.amount
        }

    resp = send_request(args.host, args.port, action, params)
    print(json.dumps(resp, indent=2))

if __name__ == "__main__":
    main()
