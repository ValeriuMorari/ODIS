"""Utilitary used for module development"""
import psutil
import socket

from func_timeout import func_timeout, FunctionTimedOut
from modules.logger import logger


def process_exists(process_name):
    """
    Checks is process process_name exists
    :param process_name:
    :return: True if process exists else False
    """
    for process in psutil.process_iter(attrs=['name']):
        if process.info['name'] == process_name:
            return True
    return False


def kill_process_by_name(process_name):
    """
    Iterated through processes find process by name and kill it
    :param process_name: process name aimed to be killed
    :return: True if process if found and killed else False
    """
    for process in psutil.process_iter(attrs=['pid', 'name']):
        if process.info['name'] == process_name:
            pid = process.info['pid']
            try:
                process = psutil.Process(pid)
                process.terminate()  # Terminate the process
                return True
            except psutil.NoSuchProcess:
                pass
    return False


def start_process(call: str, timeout: int = 0, **kwargs):
    """
    Function that starts process and waits till it is started
    If timeout is reached exception FunctionTimedOut (from func_timeout library) is raised
    :param call: call aimed to start process
    :param timeout: timeout time in seconds
    :param kwargs: other psutil kwargs
    :return: None, either exception from psutil or func-timeout libraries
    """
    def wait_for_process(pid):
        while not psutil.pid_exists(pid):
            pass

    # Start the process using psutil.Popen
    process = psutil.Popen(call, **kwargs)

    try:
        # Check if the process is running
        func_timeout(timeout, wait_for_process, args=(process.pid, ))
    except FunctionTimedOut:
        logger.exception(f"Process didn't opened within timeout time:{timeout}")
        raise


def is_port_open(port, host="127.0.0.1"):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)  # Set a timeout for the connection attempt
            s.connect((host, port))
        return True  # Port is occupied
    except (ConnectionRefusedError, socket.timeout):
        return False  # Port is not occupied
