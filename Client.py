"""
CLI controller using length-prefixed JSON over TCP.
"""
import json
import socket
import struct
from typing import Any, Dict

SERVER_PORT = 12345


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


def menu():
    print(
        """
1) List processes
2) Kill process
3) List apps
4) Start app
5) Stop app
x) Exit
"""
    )


def main():
    host = input("Server IP: ").strip()
    try:
        conn = socket.create_connection((host, SERVER_PORT), timeout=10)
    except (OSError, ConnectionError) as exc:
        print(f"Cannot connect: {exc}")
        return

    try:
        while True:
            menu()
            choice = input("Select: ").strip().lower()
            if choice == "x":
                break
            try:
                if choice == "1":
                    send_msg(conn, {"action": "list_processes"})
                elif choice == "2":
                    pid = int(input("PID to kill: "))
                    send_msg(conn, {"action": "kill_process", "pid": pid})
                elif choice == "3":
                    send_msg(conn, {"action": "list_apps"})
                elif choice == "4":
                    cmd = input("Command to run: ").strip()
                    send_msg(conn, {"action": "start_app", "command": cmd})
                elif choice == "5":
                    name = input("Process name to stop: ").strip()
                    send_msg(conn, {"action": "stop_app", "name": name})
                else:
                    print("Invalid choice")
                    continue

                resp = recv_msg(conn)
                status, data = resp.get("status"), resp.get("data")
                if status != "ok":
                    print(f"Error: {data}")
                else:
                    print(data)
            except (ValueError, OSError, ConnectionError, json.JSONDecodeError) as exc:
                print(f"Failure: {exc}")
                break
    finally:
        conn.close()


if __name__ == "__main__":
    main()
