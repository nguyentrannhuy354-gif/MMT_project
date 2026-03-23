# server/server.py

import socket
import threading

HOST = '0.0.0.0'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((HOST, PORT))
server.listen()

print("Server đang chờ kết nối...")


def handle_client(conn, addr):
    print("Client kết nối từ:", addr)

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break

            cmd = data.decode()
            print(f"[{addr}] gửi:", cmd)

            if cmd == "ping":
                conn.send("pong".encode())
            elif cmd == "hello":
                conn.send("hi client".encode())
            else:
                conn.send("unknown command".encode())

        except:
            break

    conn.close()
    print(f"Client {addr} đã ngắt kết nối")


# loop chính: nhận nhiều client
while True:
    conn, addr = server.accept()

    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()