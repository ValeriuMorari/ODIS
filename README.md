# ODIS

### Description:
By calling create_exe.bat you can create executable which opens socket.

Executable release is attached as asset: socket_connection.exe to release: https://github.com/ValeriuMorari/ODIS/releases/tag/1.0.0

Corresponding .exe opens socket at port 12345 and interprets commands specified below. 


### Encapsulated methods:
```
    "initialize(c:\\Program Files\\OE;c:\\ProgramData\\OE\\;8086)",
    "open()",
    "set_vehicle_project(MQB_2023_Brake)",
    "connect_to_ecu(3)",
    "start_protocol()",
    "send_raw_service(10 02)",
    "stop_protocol()",
     "flash(D:\\odx.container)"
```

It works in tandem with CAPL DLL from release: https://github.com/ValeriuMorari/CAPL_DLL_socket/releases/tag/3.0
Which means first executable have to be started then from CAPL ODIS can be started and methods like: flash or send_raw_service can be used diretcyl from CAPL (Canoe/Canape/Canalyzer).

### Python usage example: 
```c
from odis.odis import Odis

odis = Odis(tool_path="c:\\Program Files\\OE",
            configuration_path="c:\\ProgramData\\OE\\",
            tool_port=8086)
odis.open(force_kill=True)
odis.set_vehicle_project(project="BRAKE2023")
odis.connect_to_ecu(address=0x3)
answer = odis.send_raw_service("10 03")
print(answer)

```

### CAPL Example:
```CAPL
/*@!Encoding:1252*/
includes
{
#if X64
  #pragma library("..\Exec64\capldll.dll")
#else
  #pragma library("..\Exec32\capldll.dll")
#endif
}

variables 
{
  int socketResult = 0;
  int numberOfBytesReceived = 0;
  int i = 0;
  char receivedMessage[512];
}


on start 
{
  write("CAPL DLL VERSION: %d", caplGetDLLVersion());
  socketResult = caplSocketConnect(12345);
  write("SOCKET CONNECT: %d", socketResult);
}

on key '1' {
  /*
   "initialize(c:\\Program Files\\OE;c:\\ProgramData\\OE\\;8086)",
    "open()",
    "set_vehicle_project(MQB_2023_Brake)",
    "connect_to_ecu(3)",
    "start_protocol()",
    "send_raw_service(10 02)"
  */
  write("Send message: 'initialize(c:\\Program Files\\OE;c:\\ProgramData\\OE\\;8086)'");
  socketResult = caplSocketSend("initialize(c:\\Program Files\\OE;c:\\ProgramData\\OE\\;8086)");
  write("Bytes send: %d", socketResult);
  numberOfBytesReceived = caplSocketReceive(receivedMessage);
  write("Received response with length: %d", numberOfBytesReceived); 
  write("Received message: %s", receivedMessage);
  
  write("Send message: 'open()'");
  socketResult = caplSocketSend("open()");
  write("Bytes send: %d", socketResult);
  numberOfBytesReceived = caplSocketReceive(receivedMessage);
  write("Received response with length: %d", numberOfBytesReceived); 
  write("Received message: %s", receivedMessage);
  
  write("Send message: 'set_vehicle_project(MQB_2023_Brake)'");
  socketResult = caplSocketSend("set_vehicle_project(MQB_2023_Brake)");
  write("Bytes send: %d", socketResult);
  numberOfBytesReceived = caplSocketReceive(receivedMessage);
  write("Received response with length: %d", numberOfBytesReceived); 
  write("Received message: %s", receivedMessage);
  
  write("Send message: 'connect_to_ecu(3)'");
  socketResult = caplSocketSend("connect_to_ecu(3)");
  write("Bytes send: %d", socketResult);
  numberOfBytesReceived = caplSocketReceive(receivedMessage);
  write("Received response with length: %d", numberOfBytesReceived); 
  write("Received message: %s", receivedMessage);
  
  write("Send message: 'start_protocol()'");
  socketResult = caplSocketSend("start_protocol()");
  write("Bytes send: %d", socketResult);
  numberOfBytesReceived = caplSocketReceive(receivedMessage);
  write("Received response with length: %d", numberOfBytesReceived); 
  write("Received message: %s", receivedMessage);
  
  write("Send message: 'send_raw_service(10 02)'");
  socketResult = caplSocketSend("send_raw_service(10 02)");
  write("Bytes send: %d", socketResult);
  numberOfBytesReceived = caplSocketReceive(receivedMessage);
  write("Received response with length: %d", numberOfBytesReceived); 
  write("Received message: %s", receivedMessage);
  
  write("Send message: 'stop_protocol()'");
  socketResult = caplSocketSend("stop_protocol()");
  write("Bytes send: %d", socketResult);
  numberOfBytesReceived = caplSocketReceive(receivedMessage);
  write("Received response with length: %d", numberOfBytesReceived); 
  write("Received message: %s", receivedMessage);
}


on preStop 
{
  socketResult = caplSocketShutdown();
  write("SOCKET SHUTDOWN: %d", socketResult);
  socketResult = caplSocketClose();
  write("SOCKET CLOSE: %d", socketResult);
} 
```
