import os
import win32gui
import time
import func_timeout

from odis.configuration import Configuration
from modules.logger import logger
from modules.custom_exceptions import FlashingError
from modules.utils import process_exists, kill_process_by_name, start_process, is_port_open
from zeep import Client

STARTUP_TIMEOUT = 30


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
            raise

    def open(self, force_kill=False) -> str:
        """
        Starts up ODIS, connects to ODIS service
        :param force_kill:
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
        self.service = Client(f"http://localhost:{self.tool_port}/OdisAutomationService?wsdl").service
        logger.info(f"Initialized: {self.service}: {self.service.getAutomationApiVersion()}")
        return "ODIS opened"

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
        Sets vehicle project (PDX) which usually is imported using PDXImported
        :param project: PDX name
        :return:
        """
        project = str(project)
        self.service.setVehicleProject(project)
        self.vehicle_project_set = True
        return f"Vehicle project {project} was set"

    def connect_to_ecu(self, address: int = 3):
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

    def flash(self, odx_container):
        """
        Precondition: clear DTC and OBD_Driving_cycle = 0 should be performed as precondition
        :param odx_container: path to ODX container
        :return:
        """
        odx_container = str(odx_container)
        if not os.path.exists(odx_container):
            logger.info("ODX container: {} do not exists".format(odx_container))
            raise ValueError("ODX_CONTAINER_DO_NOT_EXISTS")

        self.service.resetAllOBDFaultMemories()
        logger.info(f"Initiate flash session; ODX: {odx_container}")
        preconditions = self.service.checkFlashPreConditions(self.connection_handle)
        if not preconditions:
            logger.info("Preconditions for flashing are fulfilled")
        else:
            logger.error("Preconditions for flashing are not fulfilled")
            raise ConnectionError("FLASH_PRECONDITIONS_NOT_FULFILLED")

        self.start_protocol()
        logger.info("Flashing started. It will take several minutes...")
        flash_session = self.service.flashProgramming(self.connection_handle, odx_container,
                                                      checkSessionWithEcu=False)

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
               tool_port=8086)
    obj.open(force_kill=True)
    obj.set_vehicle_project(project="EV_BrakeESCMQB37CLASS_VF8CG001679")
    obj.connect_to_ecu(address=0x3)
    obj.start_protocol()
    answers = []
    # answers.append(obj.send_raw_service("10 02"))
    # answers.append(obj.send_raw_service("10 03"))
    answers.append(obj.send_raw_service("10 01"))
    for item in answers:
        print(item)
    obj.stop_protocol()

    # print(obj.service.getAutomationApiVersion())
