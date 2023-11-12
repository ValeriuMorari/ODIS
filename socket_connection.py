"""Socket that handles ODIS commands"""
import socket
from interfaces.command_interface import CommandInterface
from src.main import Odis
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

        except socket.error as e:
            logger.info(f"Server error: {e}")
        finally:
            self.server_socket.close()

    def handle_connection(self, client_socket):
        first_call = True

        while True:
            data = client_socket.recv(1024)
            message = data.decode()
            logger.info(f"Received: {message}")
            try:
                if first_call:
                    self.command_interface.initialize_object(message)
                    first_call = False
                    client_socket.send("initialized with success".encode())
                    continue
                response = self.command_interface.execute_command(message)
                logger.info(response)
            except Exception as error:
                logger.info("Sent: " + str(error))
                client_socket.send(str(error).encode())
            else:
                logger.info("Sent: " + str(response))
                client_socket.send(str(response).encode())


if __name__ == "__main__":
    # Example usage:
    host_ = "127.0.0.1"  # Change this to the desired host
    port_ = 12345  # Change this to the desired port

    server = SocketServer(host_, port_)
    server.start_server()
