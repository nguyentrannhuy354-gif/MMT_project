import socket

HOST = '0.0.0.0'
PORT = 5001

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)

    print("Waiting for client...")
    conn, addr = server.accept()
    print(f"Connected to {addr}")

    while True:
        command = input("Enter command: ")

        if command == "screenshot":
            conn.send(command.encode())

            with open("received_screenshot.png", "wb") as f:
                data = conn.recv(10000000)
                f.write(data)
            print("Screenshot saved!")

        elif command.startswith("copy"):
            # format: copy|source|destination
            conn.send(command.encode())
            print(conn.recv(1024).decode())

        elif command in ["shutdown", "restart"]:
            conn.send(command.encode())

        elif command == "exit":
            conn.send(command.encode())
            break
        else:
            print("⚠️ Unknown command")

    conn.close()
    print("sever closed.")

start_server()