from argparse import ArgumentParser
import random
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
import threading

import constants

class Server(object):

    def __init__(self, req_code):
        """ Constructor.

        Args:
            req_code: The request code to use.
        """
        self.req_code = req_code

    def udp_server(self, tcp_conn, udp_port):


        # Connect to UDP port
        udp_s = socket(AF_INET, SOCK_DGRAM)
        udp_s.bind(('', udp_port))

        # Send UDP port name to client over initial TCP connection
        tcp_conn.send(udp_port)

        # Close TCP connection
        tcp_conn.close()

        message, _ = udp_s.recvfrom(constants.BUFFER_SIZE)
        message = message.decode()






        # Remove udp_port from list.
        self.udp_ports.remove(udp_port)

    def print_port(self, port):
        print("SERVER_PORT=" + str(port))

    def run(self):
        """

        Returns:
            True if the server ran successfully, False otherwise.
        """

        # Clear Message Queue
        self.message_queue = [constants.INITIAL_SERVER_MESSAGE]
        self.udp_ports = []

        # Create TCP Connection
        tcp_socket = socket(AF_INET, SOCK_STREAM)
        port = random.randint(1025, 65534)
        tcp_socket.bind(("", port))
        self.print_port(port)
        tcp_socket.listen(constants.MAX_QUEUED_CONNECTIONS)

        while constants.SERVER_END_MESSAGE not in self.message_queue:
            c, addr = tcp_socket.accept()

            # Get and validate request code
            req_code = c.recv(constants.BUFFER_SIZE).decode()

            # Throw error
            if req_code != self.req_code:
                c.send(constants.INVALID_REQUEST_CODE)
                c.close()

            # make new UDP thread
            else:
                udp_port = max(self.udp_ports + [port]) + 1
                self.udp_ports.append(udp_port)

                threading.Thread(target = self.udp_server, args=(c, udp_port))
                threading.start()


        # Close main TCP server.
        tcp_socket.close()

def main():
    parser = ArgumentParser(description='Server')
    parser.add_argument("req_code", type=str, help="The request code to use.")
    args = parser.parse_args()

    server = Server(args.req_code)
    server.run()

if __name__ == "__main__":
    main()