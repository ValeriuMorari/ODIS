from src.main import Odis

odis = Odis(tool_path="c:\\Program Files\\OE",
            configuration_path="c:\\ProgramData\\OE\\",
            tool_port=8086)
odis.open(force_kill=True)
odis.set_vehicle_project(project="EV_BrakeESCMQB37CLASS_VF8CG001679")
odis.connect_to_ecu(address=0x3)
asnwer = odis.send_raw_service("10 03")
print(asnwer)
