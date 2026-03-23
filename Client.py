# client/client.py

import socket

ip = input("Nhập IP server: ")
port = 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((ip, port))
    print("Kết nối thành công!")
except:
    print("Không kết nối được")
    exit()

try:
    while True:
        cmd = input("Nhập lệnh: ")

        if cmd == "exit":
            break

        client.send(cmd.encode())

        response = client.recv(1024)
        print("Server:", response.decode())

except KeyboardInterrupt:
    print("\nThoát client")

client.close()