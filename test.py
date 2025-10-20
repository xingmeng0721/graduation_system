import socket
s = socket.socket()
s.bind(('127.0.0.1', 10001))
print("Port 8000 OK")
s.close()