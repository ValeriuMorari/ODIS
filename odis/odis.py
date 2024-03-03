import os
import win32gui
import time
import func_timeout

try:
    from odis.configuration import Configuration
except ModuleNotFoundError:
    from configuration import Configuration
from modules.logger import logger
from modules.custom_exceptions import FlashingError
from modules.utils import process_exists, kill_process_by_name, start_process, is_port_open
from zeep import Client, Settings

STARTUP_TIMEOUT = 30

settings = Settings(strict=False, xml_huge_tree=True, xsd_ignore_sequence_order=True)


class Odis(Configuration):

    def __init__(self, *args, **kwargs):
        # Client interface for interacting with SOAP server
        self.service = None
        self.vehicle_project_set = False
        self.connection_handle = None
        self.ecu_connected = False
        super().__init__(*args, **kwargs)

    @classmethod
    def initialize(cls, tool_path, configuration_path, tool_port):
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

        return cls(tool_path=tool_path,  # "c:\\Program Files\\OE",
                   configuration_path=configuration_path,  # "c:\\ProgramData\\OE\\",
                   tool_port=tool_port)

    @staticmethod
    def _window_enumeration_callback(hwnd, top_windows):
        """
        Callback function enum_windows_callback that receives information about each top-level window
        :param hwnd:  window handle (HWND)
        :param top_windows: user defined arg, list of all top windows
        :return:
        """
        top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))

    def _wait_until_reading_finishes(self):
        """

        :return:
        """
        top_windows = []
        win32gui.EnumWindows(self._window_enumeration_callback, top_windows)

        @func_timeout.func_set_timeout(STARTUP_TIMEOUT)
        def wait_for_startup():
            """
            ODIS application startup takes several seconds where in all configuration and data are read,
            clean up is executed or latest close session is inspected
            Function inspects ODIS windows and waits till ODIS is fully started UP and can accept other commands
            :return: None or FunctionTimedOut exception from func-timeout library
            """
            for window in top_windows:
                if "OffboardDiagLauncher" in window[1]:
                    # logger.info(win32gui.GetWindowText(i[0]))
                    logger.info("Waiting...")
                    while win32gui.IsWindowVisible(window[0]):
                        logger.info("Waiting until {} is loading".format(win32gui.GetWindowText(window[0])))
                        # win32gui.ShowWindow(i[0], 5)
                        # win32gui.SetForegroundWindow(i[0])
                        time.sleep(1)
                    break
            while not is_port_open(self.tool_port):
                pass

            return True

        try:
            wait_for_startup()
        except func_timeout.exceptions.FunctionTimedOut:
            logger.error(f"ODIS did not opened within {STARTUP_TIMEOUT}s. Timeout reached")
            raise RuntimeError(f"ODIS did not opened within {STARTUP_TIMEOUT}s. Timeout reached")

    def open(self, force_kill=False) -> str:
        """
        Starts up ODIS, connects to ODIS service
        :param force_kill: if True, Kill ODIS before startup if existing
        :return: Client object is stored under `client` instance attribute; returned success string
        """
        force_kill = bool(force_kill)
        if process_exists("OffboardDiagLauncher.exe") and not force_kill:
            logger.error("OffboardDiagLauncher process is running. In case of force kill at method call "
                         "please specify argument force_kill=True")
        if force_kill:
            kill_process_by_name("OffboardDiagLauncher.exe")

        executable_path = os.path.join(self.tool_path, "OffboardDiagLauncher.exe")
        cmd_line_call = fr'{executable_path} -configuration configuration\webservice.ini'
        start_process(call=cmd_line_call, timeout=10)
        self._wait_until_reading_finishes()
        self.service = Client(f"http://localhost:{self.tool_port}/OdisAutomationService?wsdl",
                              settings=settings).service
        logger.info(f"Initialized: {self.service}: {self.service.getAutomationApiVersion()}")
        return "ODIS opened"

    def close(self):
        """
        Close ODIS
        Returns immediately and closes the application in a separate thread.
        This might take some seconds. So there is a period of time between the return of the exit method and the shutdown.
        """
        self.service.exit()
        time.sleep(3)
        return "Odis has been closed"

    def start_protocol(self):
        """
        Starts logging protocol
        Usually stored under [configuration path]\\DiagnosticProtocols
        Example: c:\\ProgramData\\Offboard_Diagnostic_Information_System_Engineering\\DiagnosticProtocols
        :return:
        """
        try:
            self.service.discardProtocol()
            self.service.initProtocol()
            self.service.startProtocol()
            logger.info("Protocol started")
            return "Protocol started"
        except Exception as error:
            logger.error(error)
            raise ValueError(f"Protocol not started due to error: {error}")

    def stop_protocol(self):
        """
        Stop logging protocol
        Usually stored under [configuration path]\\DiagnosticProtocols
        Example: c:\\ProgramData\\Offboard_Diagnostic_Information_System_Engineering\\DiagnosticProtocols
        :return:
        """
        try:
            self.service.stopProtocol()
            self.service.saveProtocol()
            return "Protocol stopped"
        except Exception as error:
            logger.error(error)
            raise ValueError(f"Protocol not stopped due to error: {error}")

    def set_vehicle_project(self, project):
        """
        Sets vehicle project (PDX) which usually is imported using PDXImporter
        :param project: PDX name
        :return:
        """
        project = str(project)
        self.service.setVehicleProject(project)
        self.vehicle_project_set = True
        return f"Vehicle project {project} was set"

    def set_doip_vehicle_project(self, project_name: str, ecu_ip_address: str) -> str:
        """
        Search DoIP VCI ,Set and load DOIP vehicle project
        :param ecu_ip_address:
        :param project_name: Name of valid project name present in ODIS
        :return:
        """
        if ecu_ip_address == '':
            ecu_ip_address = None
        ido_ipvci_list = self.service.searchDoIPVCIs(ecu_ip_address)
        if len(ido_ipvci_list) == 0:
            return "No DoIP ECUs found! Check adapter configuration."
        logger.info("Identified IPVCI:")
        logger.info(ido_ipvci_list)

        ido_ipvci = ido_ipvci_list[0]  # First node is selected - hardcoded
        # None element generates exception: Missing element name (setDoIPVehicleProject.identifier.name)
        ido_ipvci['name'] = ''
        self.service.setDoIPVehicleProject(ido_ipvci, project_name)
        return "DoIp set successfully"

    def close_connection_to_ecu(self, ecu_address: str) -> str:
        """
        Closes the connection to the current control unit and switches to CLOSE_CONNECTION_BEHAVIOUR.
        :param ecu_address: Communication ECU address
        :return:
        """
        ecu_handle = self.service.get_connection_handle(ecu_address)
        self.service.closeConnection(ecu_handle)
        return "Connection closed successfully."

    def check_flashing_preconditions(self):
        """
        Checks the flashing preconditions for the current control unit and delivers the list of unfulfilled conditions
        :return: The list of unfulfilled preconditions or an empty list if all conditions are fulfilled.
        """
        return str(self.service.checkFlashPreConditions(self.connection_handle))

    def flash_container_is_flashable(self, flash_container: str):
        """
        FROM odis DOCS:
        connectionHandle - Handle for control unit connection.
        containerFileName - Name of the container file with full path.
        sessionName - The session name to flash. A null value is allowed.

        Checks if the current control unit is flashable with the containerFileName
        if flash container is none than Checks if the current control unit is in principle flashable
        :param flash_container:  Name of the container file with full path.
        :return:
        """
        if not os.path.exists(flash_container):
            return "Flash container not found."
        if self.service.checkFlashProgrammingWithFlashContainer(self.connection_handle, flash_container, ""):
            return "Current control unit is flashable with the containerFileName content."
        else:
            return "Current control unit is NOT flashable with the containerFileName content."

    def is_flashable(self):
        """
        Checks if the current control unit is in principle flashable.
        If the information is not available the methods returns true.

        :return:
        """

        if self.service.checkFlashProgramming(self.connection_handle):
            return "Current control unit is flashable"
        else:
            return "Current control unit is NOT flashable"

    def identify_ecu(self):
        """
        Reads all identification data from the currently selected control unit including
        extended information and slave control units.
        :return:
        """

        result_identification = self.service.readIdentification(self.connection_handle)
        if len(result_identification) == 0:
            return "No ECU data identified"
        else:
            return f"Identified ECU: {result_identification[0].ecuAddress}"

    def connect_to_ecu(self, address: int = 33114):
        """
        Initialize connection to ECU
        :return:
        """
        address = int(address)
        logger.info("Connect to ECU")
        self.connection_handle = self.service.connectToEcu(address).connectionHandle
        logger.info("Open connection")
        self.service.openConnection(self.connection_handle)
        self.ecu_connected = True
        return f"Connected to ECU: {address}"

    @property
    def operable(self):
        """
        Checks if PDX is imported and ecu is connected
        This represents mandatory prerequisite for sending raw dia request and flashing
        """
        if self.ecu_connected and self.vehicle_project_set:
            return True
        else:
            raise ConnectionError("Diagnostic connection not initialized either vehicle project is not set")

    @staticmethod
    def __to_hex(val, nbits):
        return hex((val + (1 << nbits)) % (1 << nbits))

    def __format_response(self, response):
        response_formatted = ""
        for item in response:
            response_formatted = response_formatted + str(self.__to_hex(item, 8)) + " "
        return response_formatted

    @staticmethod
    def __m_zero(string):
        resp = ""
        string_splitted = string.split(" ")

        for element in string_splitted:
            if len(element) == 3:
                element = element.replace("x", "x0")
            resp = resp + element + " "
        return resp

    def send_raw_service(self, hex_command):
        """
        Sends raw diagnostic service, example: Extended diagnostic session: '10 03'
        :param hex_command: Command in hex
        :return:
        """
        hex_command = str(hex_command)
        if not self.operable:
            raise ConnectionError("Diagnostic connection not initialized either vehicle project is not set")

        hex_command = hex_command.strip().replace(" ", "")
        hex_list = [hex_command[index: index + 2] for index in range(0, len(hex_command), 2)]
        hex_list = ["0x" + item for item in hex_list if "0x" not in item]
        hex_data = [(int(item, 0)) for item in hex_list]
        hex_data = bytes(hex_data)

        answer = self.service.sendRawService(self.connection_handle, hex_data)

        answer = self.__format_response(answer)
        answer = self.__m_zero(answer)
        answer = answer.upper()
        answer = answer.strip().replace(" ", "").replace("0x", "")
        answer = ' '.join(answer[i:i + 4] for i in range(0, len(answer), 4))

        return answer

    def set_communication_trace(self, trace_state: str):
        """
        Starts or stops the tracing of BUS, DoIP or JOB traces. Which traces are affected is configured within
        configureSetting.
        Usually stored under [configuration path]\\trace_logs
        Parameters:
        traceState - The state for tracing.

        """
        if trace_state not in ["ON", "OFF"]:
            return "Invalid traceState: Possible values:[ON][OFF]"

        self.service.setCommunicationTrace("ON")
        return f"Trace state set to: {trace_state}"

    def flash(self, odx_container):
        """
        Precondition: clear DTC should be performed as precondition
        :param odx_container: path to ODX container
        :return:
        """
        odx_container = str(odx_container)
        if not os.path.exists(odx_container):
            logger.info("ODX container: {} do not exists".format(odx_container))
            raise ValueError("ODX_CONTAINER_DO_NOT_EXISTS")

        # self.service.resetAllOBDFaultMemories()
        logger.info(f"Initiate flash session; ODX: {odx_container}")
        preconditions = self.service.checkFlashPreConditions(self.connection_handle)
        if not preconditions:
            logger.info("Preconditions for flashing are fulfilled")
        else:
            logger.error("Preconditions for flashing are not fulfilled")
            raise ConnectionError("FLASH_PRECONDITIONS_NOT_FULFILLED")

        self.start_protocol()
        logger.info("Flashing started. It will take several minutes...")
        try:
            flash_session = self.service.flashProgramming(self.connection_handle, odx_container,
                                                          checkSessionWithEcu=False)
        except Exception as error:
            self.stop_protocol()
            return str(error)

        self.stop_protocol()

        if flash_session.errorOccurred is not False:
            logger.error("Error occurred during flashing.")
            logger.error("Error message: {}".format(flash_session.errorMessage))
            logger.error(flash_session.negativeResponse)
            logger.error("ECU ID: {}".format(flash_session.ecuId))
            logger.error("Session name: {}".format(flash_session.sessionName))
            logger.error("Duration path: {}s".format(flash_session.duration))
            logger.error("Container size: {}".format(flash_session.containerSize))
            raise FlashingError
        else:
            logger.info("Flashing process ends with success")
            logger.info("ECU ID: {}".format(flash_session.ecuId))
            logger.info("Session name: {}".format(flash_session.sessionName))
            logger.info("Duration path: {}s".format(flash_session.duration))
            logger.info("Container size: {}".format(flash_session.containerSize))

        return "ECU flashed successfully"


if __name__ == "__main__":
    obj = Odis(tool_path="c:\\Program Files\\OE",
               configuration_path="c:\\ProgramData\\OE\\",
               tool_port=8081)
    obj.open(force_kill=True)
    print("ODIS opened ---")
    # obj.set_vehicle_project("VW38XPA");
    print(obj.set_doip_vehicle_project("VW", "fd53:8cb8:323:1::33"))
    print(obj.connect_to_ecu())
    print(obj.identify_ecu())
    print(obj.set_communication_trace("ON"))
    print(obj.flash(odx_container=r"C:\sw\temp.pdx"))
    print(obj.set_communication_trace("OFF"))
    print(obj.close())
    print("ODIS closed ---")
    print('TERMINATED')
    # obj.set_vehicle_project(project="")
    # obj.connect_to_ecu(address=0x10)
    # obj.start_protocol()

    # answers = []
    # # answers.append(obj.send_raw_service("10 02"))
    # # answers.append(obj.send_raw_service("10 03"))
    # answers.append(obj.send_raw_service("10 01"))
    # for item in answers:
    #     print(item)
    # obj.stop_protocol()

    # print(obj.service.getAutomationApiVersion())
