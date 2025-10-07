# protocol.py
import json
import struct
import socket
from typing import Optional, Dict, Any

def send_msg(sock: socket.socket, msg: Dict[str, Any]) -> None:
    """Send a dict message as JSON with a 4-byte big-endian length prefix."""
    data = json.dumps(msg).encode("utf-8")
    sock.sendall(struct.pack("!I", len(data)) + data)

def recvall(sock: socket.socket, n: int) -> Optional[bytes]:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def recv_msg(sock: socket.socket, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Receive and parse one message. Returns dict or None on EOF/timeout."""
    sock.settimeout(timeout)
    raw_len = recvall(sock, 4)
    if not raw_len:
        return None
    msg_len = struct.unpack("!I", raw_len)[0]
    raw = recvall(sock, msg_len)
    if raw is None:
        return None
    return json.loads(raw.decode("utf-8"))

def send_request(host: str, port: int, action: str, params: Dict[str, Any], timeout: int = 5) -> Dict[str, Any]:
    """Connect, send one request, return response dict or {'status':'error', ...} on failure."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            send_msg(s, {"action": action, "params": params})
            resp = recv_msg(s, timeout=timeout)
            if resp is None:
                return {"status": "error", "error": "no response"}
            return resp
    except Exception as e:
        return {"status": "error", "error": str(e)}
