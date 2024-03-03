import socket
import time

IP = 'localhost'
PORT = 12345
s = socket.socket()
s.connect((IP, PORT))

message_list = [
    "busy",
    "initialize(c:\\Program Files\\OE;c:\\ProgramData\\OE\\;8086)",
    "busy",
    "busy",
    "busy",
    "busy",
    "busy",
    "sleep",
    "busy",
    "busy",
    "busy",
    "busy",
    "busy",

    "get_result",
    "busy",
    "busy",
    # "open()",
    # "busy",
    # "get_result",
    # "busy",
    "stop_interface"
    # "set_vehicle_project(MQB_2023_Brake)",
    # "connect_to_ecu(3)",
    # "start_protocol()",
    # "send_raw_service(10 02)",
    # "stop_protocol()"
]
for item in message_list:
    if "sleep" in item:
        time.sleep(6)
        continue
    print(f"send: {item}")
    s.send(item.encode())
    print(f"received: {s.recv(1024)}")
