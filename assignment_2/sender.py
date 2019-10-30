from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_DGRAM
import time
from threading import Thread

from packet import packet

import constants
from window import Window


class Sender(object):
    # TODO: Need to implement modulo sequence numbers

    def __init__(self, hostname: str, ack_port: int, data_port: int, filename: str):
        """ Constructor.

        Args:
            hostname: The hostname of the network emulator to connect to.
            data_port: The port to send the emulator data.
            ack_port: The port to receive ack messages from the sender (via emulator).
            filename: The name of the file to transmit.
        """
        self.hostname = hostname
        self.ack_port = ack_port
        self.data_port = data_port
        self.filename = filename
        self.seq_num = 0
        self.eot = False

    def send_EOT(self, seq_num):
        """ Sends an EOT packet.
        """
        socket(AF_INET, SOCK_DGRAM).sendto(packet.create_eot(seq_num).get_udp_data(),
                                           (self.hostname, self.ack_port))

    def ack_recv_thread_func(self):
        ack_socket = socket(AF_INET, SOCK_DGRAM)

        while not self.eot:
            data = ack_socket.recvfrom(constants.ACK_BUFFER_SIZE)
            p = packet.parse_udp_data(data)

            if p.type == constants.TYPE_ACK:
                print(f"[RECEIVER] - Received ack with seq: {p.seq_num}")
                self.seq_num = p.seq_num + 1

            if p.type == constants.TYPE_EOT:
                self.send_EOT(self.seq_num)
                self.eot = True

    def run(self):
        """ Main thread for running the sender.
        """
        # Start thread listening for ACKS.
        t = Thread(target=self.ack_recv_thread_func).start()

        # Create Window and start thread to send data.
        window = Window(constants.WINDOW_SIZE, self.filename)
        with open(self.filename, "r") as f:
            data  = f.read(constants.BUFFER_SIZE)
            while data:
                if not window.is_full():
                    window.add_data(data, (self.hostname, self.data_port))
                elif window.has_timeout():
                    window.resend_all((self.hostname, self.data_port))
                else:
                    window.update_base_number(self.seq_num)
                    time.sleep(constants.SENDER_SLEEP) # update the window based on ACK thread.

        while not self.eot:
            time.sleep(constants.SENDER_SLEEP)


def main():
    # Parse arguments
    parser = ArgumentParser(description='Sender')
    parser.add_argument("hostname", type=str,
                        help="The hostname of the network emulator to connect to.")
    parser.add_argument("data_port", type=int,
                        help="The port to send the emulator data.")
    parser.add_argument("ack_port", type=int,
                        help="The port to receive ack messages from the sender (via emulator).")
    parser.add_argument("filename", type=str,
                        help="The name of the file to transmit.")
    args = parser.parse_args()

    # Run Sender
    sender = Sender(args.hostname, args.ack_port, args.data_port, args.filename)
    sender.run()


if __name__ == "__main__":
    main()
