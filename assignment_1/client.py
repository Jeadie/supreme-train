from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
import sys

import constants

class Client(object):

    def __init__(self, address, port, req_code, message):
        """ Constructor

        Args:
            address:  The address of the server to connect to.
            port: The port of the server to connect to.
            req_code: The request code to use.
            message: The message to send to the server.
        """
        self.addr = address
        self.port = port
        self.req_code = req_code
        self.msg = message

    def run(self):
        """ Connects to the server via TCP to establish a port to send a UDP message
            on and recieve a list of messages to print.

        Returns:
            True if the communication was succesful, False otherwise.
        """
        # The client creates a TCP socket and connects to the server.
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((self.addr, self.port))

        # The client sends a message to the server containing a numerical code
        # (req_code).
        s.send(self.req_code)

        # if the req_code is invalid, the server should reply to the client "0", and the
        # client should terminate with an error "Invalid req_code."
        req_code_response = s.recv(constants.BUFFER_SIZE)
        s.close()

        if req_code_response == constants.INVALID_REQUEST_CODE:
            print(constants.INVALID_REQUEST_ERROR)
            return False
        else:
            udp_port = int(req_code_response)

        # The client sends a message "GET", over UDP, to the server
        s = socket(AF_INET, SOCK_DGRAM)
        s.sendto(constants.GET_MESSAGE.encode(), (self.addr, udp_port))

        # The server should then send all stored messages over UDP to the client.
        serverAddress = ("", "")
        while serverAddress[0] != self.addr:
            messages, serverAddress = s.recvfrom(constants.BUFFER_SIZE)

        messages = messages.decode()

        # The client will display each message on its own line.
        for message in messages.split(constants.MESSAGE_DELIMETER):
            print(message)

        # The client sends its text message, over UDP, to the Server
        s.sendto(self.msg.encode(), (self.addr, udp_port))
        s.close()

        # The client waits for keyboard input before exiting.        #
        raw_input(constants.KEYBOARD_MESSAGE_EXIT)
        return True

def main():
    parser = ArgumentParser(description='Client')
    parser.add_argument("address", type=str, help="The address of the server to connect to.")
    parser.add_argument("port", type=int, help="The port of the server to connect to.")
    parser.add_argument("req_code", type=str, help="The request code to use.")
    parser.add_argument("message", type=str,help="The message to send to the server.")
    args = parser.parse_args()
    client = Client(args.address, args.port, args.req_code, args.message)
    client.run()

if __name__ == "__main__":
    main()