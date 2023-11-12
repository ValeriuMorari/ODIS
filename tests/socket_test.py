import socket


IP = 'localhost'
PORT = 12345
s = socket.socket()
s.connect((IP, PORT))

message_list = [
    "initialize(c:\\Program Files\\OE;c:\\ProgramData\\OE\\;8086)",
    "open()",
    "set_vehicle_project(MQB_2023_Brake)",
    "connect_to_ecu(3)",
    "start_protocol()",
    "send_raw_service(10 02)",
    "stop_protocol()"
]
for item in message_list:
    print(f"send: {item}")
    s.send(item.encode())
    print(f"received: {s.recv(1024)}")
