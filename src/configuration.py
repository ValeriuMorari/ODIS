"""configuration class which encapsulates all necessary inputs for module usage"""
import os
from dataclasses import dataclass
from modules.trigger_setter_meta import TriggerSetterMeta


RESERVED_PORTS = {
    80: "HTTP",
    443: "HTTPS",
    25: "SMTP (Simple Mail Transfer Protocol)",
    22: "SSH (Secure Shell)",
    21: "FTP (File Transfer Protocol)",
    53: "DNS (Domain Name System)",
    23: "Telnet"
}


@dataclass()
class Configuration(metaclass=TriggerSetterMeta):
    """
    :param tool_path: Path to OffboardDiagLauncher.exe
    usually installed in: c:\\Program Files\\Offboard_Diagnostic_Information_System_Engineering
    :param configuration_path: Path to ODIS configuration
    usually installed in: c:\\ProgramData\\Offboard_Diagnostic_Information_System_Engineering
    :param tool_port: Port for connection to ODIS webservice
    Tool port is specified within webservice.ini configuration file
    which usually can be found within ODIS configuration path
    Example:
    c:\\ProgramData\\Offboard_Diagnostic_Information_System_Engineering\\configuration\\webservice.ini

    Corresponding configuration file shall contain following keys for automation usage of ODIS web service
    ----------------------------------------------------------------------------
    # Default if value is not set: FALSE
    de.volkswagen.odis.vaudas.vehiclefunction.automation.webservice.enabled=true

    # Port for publishing the web-service.
    # Default if value is not set: 8081
    de.volkswagen.odis.vaudas.vehiclefunction.automation.webservice.port=8086

    # End of file marker - must be here
    eof=eof
    ----------------------------------------------------------------------------
    """

    tool_path: str
    configuration_path: str
    tool_port: str

    def _tool_port_setter(self, tool_port):
        """
        Verifies that port type is valid and port is free
        :param tool_port: port for ODIS web service
        :return:
        """
        # accepted default value as attribute is optional
        if tool_port is None:
            return

        tool_port = int(tool_port)

        if 65535 < tool_port < 0:
            raise ValueError(f"Tool port: {tool_port} is out of range of "
                             f"16-bit unsigned integer, thus ranging from 0 to 65535")
        if 0 <= tool_port <= 1023:
            raise ValueError(f"Tool port: {tool_port} is reserved for "
                             f"{RESERVED_PORTS.get(tool_port, 'common and well-known services such as HTTP, SMTP ')} "
                             f"and cannot be used")
        self.tool_port = tool_port

    def _configuration_path_setter(self, configuration_path):
        """
        Checks whether configuration path exists and all needed sub folders like: configuration, logs exists
        :param configuration_path: configuration_path
        :return: ValueError exception if any of mandatory paths do not exists
        """
        if not os.path.exists(configuration_path):
            raise ValueError(f"Path: {configuration_path} do not exists")
        self.configuration_path = configuration_path

    def _tool_path_setter(self, tool_path):
        """
        Checks whether OffboardDiagLauncher.exe exists
        :param tool_path: tool_path
        :return: ValueError exception if path do not exist
        """
        if not os.path.isdir(tool_path):
            raise ValueError(f"Path: {tool_path} is not directory")
        _tool_path = os.path.join(tool_path, "OffboardDiagLauncher.exe")
        if not os.path.exists(_tool_path):
            raise ValueError(f"Path: {_tool_path} do not exists")
        self.tool_path = tool_path


if __name__ == "__main__":
    c = Configuration("D:\\Temp", "D:\\Temp", 8061)
