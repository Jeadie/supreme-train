from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_DGRAM
import time

import constants
from packet import packet
import log

logger = log.configure_receiver_logger("receiver", info_stdout=constants.PRINT_INFO)


class Receiver(object):

    def __init__(self, hostname: str, ack_port: int, data_port: int, filename: str):
        """

        Args:
            hostname: The hostname of the network emulator to connect to.
            ack_port: The port to send ack messages to on the emulator.
            data_port: The port the emulator will send data packets to the receiver via.
            filename: The name of the file to save data into.
        """
        self.hostname = hostname
        self.ack_port = ack_port
        self.data_port = data_port
        self.filename = filename
        self.seq_num = 0

    def send_ack(self, seq_num: int):
        """ Sends an ACK packet for a sequence number.

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

    def handle_message(self, socket) -> packet:
        """ Handles the receiving of packets, sending acks and storing data locally.

        Args:
            socket: The socket to receive data from.

        Returns:
            The parsed packet object of the most recent message.
        """
        message, _ = socket.recvfrom(constants.PACKET_DATA_SIZE)
        try:
            p = packet.parse_udp_data(message)
        except Exception as e:
            logger.log(f"ERROR: {e}")
            return None
        logger.log(f"Received packet with no: {p.seq_num}."
                   f"Looking for {(self.seq_num + 1) % constants.MODULO_RANGE}")

        if p.type == constants.TYPE_EOT:
            logger.log("Received EOT.")
            return p

        elif p.type == constants.TYPE_ACK:
            # Should not happened
            logger.log("[ERROR] Received ACK.")
            return p

        # Else data message
        logger.arrival(p.seq_num)
        if p.seq_num == (self.seq_num + 1) % constants.MODULO_RANGE:
            # Expected, next packet
            with open(self.filename, "a") as f:
                f.write(p.data)
            self.send_ack(self.seq_num)
            logger.log(f"Sending ACK for good packet with no: {self.seq_num + 1}")
            self.seq_num = p.seq_num
        else:
            self.send_ack(self.seq_num)
            logger.log(f"Sending ACK for bad packet with no: {self.seq_num}")
        return p

    def run(self):
        """ Main thread for running a receiver.
        """
        self.seq_num = 0
        self.data = ""

        # Setup UDP port for receiving data
        data_socket = socket(AF_INET, SOCK_DGRAM)
        data_socket.bind((self.hostname, self.data_port))

        # do-while handling packets until it receives EOT
        packet = self.handle_message(data_socket)
        while packet.type != constants.TYPE_EOT:
            new_packet = self.handle_message(data_socket)
            if new_packet:
                packet = new_packet
            time.sleep(constants.PROCESS_WAIT)

        # Send EOT back
        self.send_EOT(packet.seq_num)


def main():
    # Parse arguments
    parser = ArgumentParser(description='Receiver')
    parser.add_argument("hostname", type=str,
                        help="The hostname of the network emulator to connect to.")
    parser.add_argument("ack_port", type=int,
                        help="The port to send ack messages to on the emulator.")
    parser.add_argument("data_port", type=int,
                        help="The port the emulator will send data packets to the receiver via.")
    parser.add_argument("filename", type=str,
                        help="The name of the file to save data into.")
    args = parser.parse_args()

    # Run Receiver
    receiver = Receiver(args.hostname, args.ack_port, args.data_port, args.filename)
    receiver.run()


if __name__ == "__main__":
    main()
