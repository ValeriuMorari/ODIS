"""Socket command"""
import re
import queue
import threading
import time

from queue import Empty
from interfaces.custom_exceptions import CommandTemplateError, InvalidInitialization, InvalidCommand
from modules.logger import logger
from modules.custom_exceptions import *

METHOD_PATTERN = r'^.*(?=\()'
ARGS_PATTERN = r'(?<=\().*(?=\))'


class CommandInterface:
    """
    Command Generic class
    """

    def __init__(self, component_class) -> None:
        self._tasks = queue.Queue(maxsize=1)
        self._results = queue.Queue(maxsize=1)
        self._execute = threading.Event()
        self._obj = None
        self._component_class = component_class
        self._force_stop = False
        self._thread = threading.Thread(target=self._main_thread).start()
        self.cmd_interface_commands = ["busy",
                                       "get_result",
                                       "stop_interface"]

    def _main_thread(self):
        """
        Method aim to run in thread
        Checks tasks queue
        Once _run events is set get task from queue and executes it
        Task result is pushed to _results queue
        :return:
        """
        while not self._force_stop:
            if self._execute.is_set():
                logger.info("Running task from queue...")
                continue
            try:
                operation = self._tasks.get(timeout=1)
            except Empty:
                logger.info("Queue is empty...")
                continue
            if not operation:
                logger.info("Queue is empty or get timeout reached...")
                continue

            logger.info(f"Set _execute flag with operation {operation}")
            self._execute.set()
            operation()
            logger.info("Clear _execute flag")
            self._execute.clear()

    def busy(self):
        """
        Checks whether interface is running any task
        :return: True is interface is busy with task run, False otherwise
        """
        return self._execute.is_set()

    def get_result(self):
        if self._results.qsize():
            return self._results.get()
        else:
            return "Results queue is empty"

    def stop_interface(self):
        """
        Stops thread execution
        :return:
        """
        self._force_stop = True

    def add_initialization_task(self, message):
        if self._results.qsize():
            raise LastResultNotRead
        if self._tasks.qsize():
            raise Busy

        self._tasks.put(lambda: self._initialize_object(message))

    def add_command_execution_task(self, message):
        if self._tasks.qsize():
            raise Busy
        if self._results.qsize():
            raise LastResultNotRead

        self._tasks.put(lambda: self._execute_command(message))

    def _initialize_object(self, message):
        """
        method responsible to register automated tool object
        :param message: Raw socket message
        :return: None
        """
        time.sleep(3)
        self._results.put("executed initialize with success")
        return
        logger.info(f"RUN _initialize_object: {message}")
        command = Command(message)
        method, args = command.dispatch()
        if "initialize" not in method:
            raise InvalidInitialization
        self._obj = self._component_class.initialize(*args)
        self._results.put("initialized")

    def _execute_command(self, message: str):
        """

        :param message:
        :return:
        """
        time.sleep(3)
        self._results.put("executed CMD with success")
        return
        logger.info(f"RUN _execute_command: {message}")
        try:
            command = Command(message)
            result_ = command.execute(self._obj)
        except Exception as error_:
            result_ = error_

        self._results.put(result_)


class Command:

    def __init__(self, command: str):
        """
        :param command: string command according to template:
        command(arg1; arg2; ...; argN)
        """
        self.command = command

    def dispatch(self) -> (str, tuple):
        """
        Dispatch command to method string and tuple of arguments
        :return: method string, tuple of arguments
        """
        args = re.search(ARGS_PATTERN, self.command)
        method = re.search(METHOD_PATTERN, self.command)
        if method is None:
            raise CommandTemplateError
        if args and args.group():
            args = args.group().split(";")
        else:
            args = []
        method = method.group()
        return method, args

    def execute(self, component: object):
        """
        Executes command in accordance to mentioned message & automation component
        :param component: automation component object
        :return: result in string format
        """
        method, args = self.dispatch()
        if not hasattr(component, method):
            raise InvalidCommand
        call = component.__getattribute__(method)
        response = call(*args)
        return str(response)


if __name__ == "__main__":
    obj = CommandInterface("temp")
    logger.info(f"busy: {obj.busy()}")
    logger.info(f"busy: {obj.get_result()}")
    logger.info("Add task  1...")
    obj.add_command_execution_task('set_vehicle_project(MQB_2023_Brake)')
    # logger.info(f"Result  1: {obj.get_result()}")
    logger.info("Add task  2...")
    try:
        obj.add_command_execution_task('set_vehicle_project(MQB_2023_Brake)')
    except Exception as error:
        logger.info(error)
    import time

    time.sleep(3)
    logger.info(f"Result: {obj.get_result()}")
    logger.info("Add task  2.1 ...")
    try:
        obj.add_command_execution_task('set_vehicle_project(MQB_2023_Brake)')
    except Exception as error:
        logger.info(error)
    logger.info(f"Result: {obj.get_result()}")
    logger.info(f"busy: {obj.busy()}")

    obj.stop_interface()
