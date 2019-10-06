from argparse import ArgumentParser
import random
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, timeout, gethostbyname, gethostname
import threading

import constants

class Server(object):

    def __init__(self, addr, req_code):
        """ Constructor.

        Args:
            req_code: The request code to use.
            addr: The IP address to run the server sockets on. 
        """
        self.addr = addr
        self.req_code = req_code

    def udp_server(self, tcp_conn, udp_port):
        """ A single UDP socket thread for a communication between server and client
            via UDP.

        Args:
            tcp_conn: A TCP connection opened by the main process.
            udp_port: The port for the client to send/recv wuth the server on, via UDP.
        """

        # Connect to UDP port
        udp_s = socket(AF_INET, SOCK_DGRAM)
        udp_s.bind((self.addr, udp_port))

        # Send UDP port name to client over initial TCP connection
        tcp_conn.send(str(udp_port))

        recv_count = 0

        # To messages will be sent by client, a GET and a message
        while recv_count < 2:
            # Receive message
            message, addr = udp_s.recvfrom(constants.BUFFER_SIZE)
            message = message.decode()

            # if GET message, send list of messages.
            if message == constants.GET_MESSAGE:
                for m in self.message_queue:
                    udp_s.sendto(m.encode(), addr)
                udp_s.sendto(constants.SERVER_DONE_MESSAGES.encode(), addr)

            # Add onto message queue.
            else:
                if message == constants.SERVER_END_MESSAGE:
                    self.close_server = True
                self.message_queue.append("[{0}]: {1}".format(addr[-1], message))
            recv_count += 1

        # Remove udp_port from list.
        self.udp_ports.remove(udp_port)

    def print_port(self, port):
        print("SERVER_PORT=" + str(port))

    def run(self):
        """ Main server thread to run the TCP socket and create subsequent UDP threads.

        Returns:
            True if the server ran successfully, False otherwise.
        """

        # Clear Message Queue
        self.message_queue = []
        self.udp_ports = []
        self.close_server = False

        # Create TCP Connection on random port above 1024
        tcp_socket = socket(AF_INET, SOCK_STREAM)
        port = random.randint(1025, 65534)
        tcp_socket.bind((self.addr, port))
        self.print_port(port)
        tcp_socket.listen(constants.MAX_QUEUED_CONNECTIONS)
        tcp_socket.settimeout(constants.SERVER_LOOP_TIMEOUT)

        while not self.close_server:
            try:
                c, addr = tcp_socket.accept()
            except timeout:
                continue
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

                t = threading.Thread(target = self.udp_server, args=(c, udp_port))
                t.start()


        # Close main TCP server.
        tcp_socket.close()

def main():
    # Parse arguments
    parser = ArgumentParser(description='Server')
    parser.add_argument("req_code", type=str, help="The request code to use.")
    args = parser.parse_args()

    # Get IP address
    addr = gethostbyname(gethostname())

    # Run Server
    server = Server(addr, args.req_code)
    server.run()

if __name__ == "__main__":
    main()
