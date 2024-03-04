"""Socket that handles ODIS commands"""
import socket
from interfaces.detached_command_interface import CommandInterface
from odis.odis import Odis
from modules.logger import logger


class SocketServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.command_interface = CommandInterface(Odis)

    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()  # Maximum number of queued connections

            logger.info(f"Server listening on {self.host}:{self.port}")

            while True:
                client_socket, client_address = self.server_socket.accept()
                logger.info(f"Accepted connection from {client_address}")

                # Handle the connection and receive messages
                self.handle_connection(client_socket)
                self.command_interface.stop_interface()

        except socket.error as e:
            logger.info(f"Server error: {e}")
            self.command_interface.stop_interface()
        finally:
            self.server_socket.close()
            self.command_interface.stop_interface()

    def handle_connection(self, client_socket):
        first_call = True

        while True:
            data = client_socket.recv(1024)
            message = data.decode()
            logger.info(f"Received: {message}")

            if first_call:
                try:
                    self.command_interface.add_initialization_task(message)
                except Exception as error:
                    result = str(error)
                else:
                    result = "Task added"
                first_call = False
            elif message in self.command_interface.cmd_interface_commands:
                result = str(self.command_interface.__getattribute__(message)())
            else:
                try:
                    self.command_interface.add_command_execution_task(message)
                except Exception as error:
                    result = str(error)
                else:
                    result = "Task added"
            logger.info(f"SENT: {result}")
            client_socket.send(result.encode())


if __name__ == "__main__":
    # Example usage:
    host_ = "127.0.0.1"  # Change this to the desired host
    port_ = 12345  # Change this to the desired port

    server = SocketServer(host_, port_)
    server.start_server()
