"""Socket that handles ODIS commands"""
import socket


class SocketServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None

    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)  # Maximum number of queued connections

            print(f"Server listening on {self.host}:{self.port}")

            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"Accepted connection from {client_address}")

                # Handle the connection and receive messages
                self.handle_connection(client_socket)

        except socket.error as e:
            print(f"Server error: {e}")
        finally:
            self.server_socket.close()

    def handle_connection(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = data.decode()
                print(f"Received: {message}")
        except socket.error as e:
            print(f"Connection error: {e}")
        finally:
            client_socket.close()

# Example usage:
host = "localhost"  # Change this to the desired host
port = 12345  # Change this to the desired port

server = SocketServer(host, port)
server.start_server()
