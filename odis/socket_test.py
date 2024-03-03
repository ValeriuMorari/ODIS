import socket


IP = '127.0.0.1'
PORT = 12345
s = socket.socket()
s.connect((IP, PORT))

message_list = [
    "initialize(c:\\Program Files\\OE;c:\\ProgramData\\OE\\;8081)",
    "open()",
    "set_doip_vehicle_project(VW;fd23:74b8:363:2::39)",
    "connect_to_ecu()",
    "identify_ecu()",
    "set_communication_trace(ON)",
    "set_communication_trace(OFF)",
    "flash(C:\\sw\\path\\PDX\\pdx_file.pdx)",
    "close()"
    # "close_connection_to_ecu(33114)",
    # "check_flashing_preconditions()",
    # "is_flashable()",
    # "identify_ecu()",
    #"set_vehicle_project(VW4500)",

   # "connect_to_ecu(33114)",
   # "start_protocol()",
   # "send_raw_service(10 02)"
]
# s.send("set_doip_vehicle_project(VW38XPA;fd53:7cb8:383:2::39)".encode())
# print(f"received: {s.recv(1024)}")
# s.send(check_flashing_preconditions()".encode())
# print(f"received: {s.recv(1024)}")

for item in message_list:
    print(f"send: {item}")
    s.send(item.encode())
    print(f"received: {s.recv(1024)}")
