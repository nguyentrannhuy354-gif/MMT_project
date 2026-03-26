"""
Modular remote control server using length-prefixed JSON.
"""
import json
import socket
import struct
import threading
from typing import Any, Dict

from features.process_manager import handle_process
from features.app_manager import handle_app

HOST = "0.0.0.0"
PORT = 12345
RECV_TIMEOUT = 10


def send_msg(conn: socket.socket, payload: Dict[str, Any]) -> None:
    data = json.dumps(payload).encode("utf-8")
    conn.sendall(struct.pack(">I", len(data)) + data)


def recv_exact(conn: socket.socket, size: int) -> bytes:
    buf = b""
    while len(buf) < size:
        chunk = conn.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("connection closed")
        buf += chunk
    return buf


def recv_msg(conn: socket.socket) -> Dict[str, Any]:
    header = recv_exact(conn, 4)
    (length,) = struct.unpack(">I", header)
    body = recv_exact(conn, length)
    return json.loads(body.decode("utf-8"))


def dispatch(cmd: Dict[str, Any]) -> Dict[str, Any]:
    action = cmd.get("action")
    if action == "ping":
        return {"status": "ok", "data": "pong"}
    if action in {"list_processes", "kill_process"}:
        return handle_process(action, cmd)
    if action in {"list_apps", "start_app", "stop_app"}:
        return handle_app(action, cmd)
    return {"status": "error", "data": f"unknown action {action}"}


def handle_client(conn: socket.socket, addr):
    conn.settimeout(RECV_TIMEOUT)
    print(f"Client connected: {addr}")
    try:
        while True:
            try:
                cmd = recv_msg(conn)
            except (ConnectionError, json.JSONDecodeError) as exc:
                print(f"{addr} disconnect/error: {exc}")
                break
            resp = dispatch(cmd)
            send_msg(conn, resp)
    finally:
        conn.close()
        print(f"Client {addr} closed")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Shutting down server")
    finally:
        server.close()


if __name__ == "__main__":
    main()
