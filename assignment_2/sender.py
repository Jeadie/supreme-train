from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_DGRAM

import constants
import time
from packet import packet

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

    def send_data(self, seq_num: int):
        """ Sends a data packet based on the sequence number.

        Args:
            seq_num: Sequence number of the packet to mention in the ACK.
        """
        socket(AF_INET, SOCK_DGRAM).sendto(packet.create_ack(seq_num).get_udp_data(),
                                           (self.hostname, self.ack_port))

    def send_EOT(self, seq_num):
        """ Sends an EOT packet.
        """
        socket(AF_INET, SOCK_DGRAM).sendto(packet.create_eot(seq_num).get_udp_data(),
                                           (self.hostname, self.ack_port))

    def run(self):
        """ Main thread for running the sender.
        """
        # Start thread listening for ACKS.


        # Create Window and start thread to send data.
        window = Window(constants.WINDOW_SIZE, self.filename, constants.TIMEOUT_VALUE)
        with open(self.filename, "r") as f:
            data  = f.read(constants.BUFFER_SIZE)
            while data:
                if not window.is_full():
                    window.add_data(data)
                elif window.has_timeout():
                    window.resend_all()
                else:
                    window.update_sequence_number(self.seq_num)
                    time.sleep(constants.SENDER_SLEEP) # update the window based on ACK thread.


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
