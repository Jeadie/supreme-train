from argparse import ArgumentParser
import datetime
from socket import socket, AF_INET, SOCK_DGRAM
import time
from threading import Thread

from packet import packet

import constants
import log
from window import Window

logger = log.configure_sender_logger("sender", info_stdout=constants.PRINT_INFO)


class Sender(object):

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
        self.next_seq_num = 0
        self.eot = False

    def send_EOT(self, seq_num):
        """ Sends an EOT packet.
        """
        socket(AF_INET, SOCK_DGRAM).sendto(packet.create_eot(seq_num).get_udp_data(),
                                           (self.hostname, self.data_port))
        logger.log(f"Sent EOT with: {seq_num}.")

    def ack_recv_thread_func(self):
        """ Thread function for receiving client acks and updating window base
        accordingly.

        Also responsible for receiving EOT packets from client and changing state for
        main thread.
        """
        ack_socket = socket(AF_INET, SOCK_DGRAM)
        ack_socket.bind((self.hostname, self.ack_port))

        while not self.eot:
            try:
                # Parse Packet
                data, port = ack_socket.recvfrom(constants.ACK_BUFFER_SIZE)
                p = packet.parse_udp_data(data)

                # Packet is ACK
                if p.type == constants.TYPE_ACK:
                    logger.log(f"Received ack with seq: {p.seq_num}")
                    logger.ack(p.seq_num)
                    self.next_seq_num = p.seq_num
                    self.window.update_base_number(self.next_seq_num)

                # Packet is EOT
                if p.type == constants.TYPE_EOT:
                    self.eot = True
                    logger.log("Received EOT.")

            except TypeError as e:
                logger.log(
                    f"Received data that could not be processed: {e}.")

    def run(self):
        """ Main thread for running the sender.
        """
        # Start thread listening for ACKs.
        t = Thread(target=self.ack_recv_thread_func).start()

        # Create Window and start thread to send data.
        self.window = Window(constants.WINDOW_SIZE, logger)

        # Read a Packet of data and attempt to send
        with open(self.filename, "r") as f:
            start = datetime.datetime.now()
            data = f.read(constants.BUFFER_SIZE)
            while data:
                if not self.window.is_full():
                    self.window.add_data(data, (self.hostname, self.data_port))
                    data = f.read(constants.BUFFER_SIZE)
                elif self.window.has_timeout():
                    self.window.resend_all((self.hostname, self.data_port))
                else:
                    time.sleep(constants.PROCESS_WAIT)

        logger.log(f"Ending transmission. {self.window.window}")

        # Ensure all packets have been received by client
        while not self.window.finished(self.next_seq_num):
            if self.window.has_timeout():
                self.window.resend_all((self.hostname, self.data_port))
            time.sleep(constants.PROCESS_WAIT)

        logger.log(f"Finished sending remaining packets.")

        # Send and wait on EOT
        self.send_EOT(self.window.seq_number)
        while not self.eot:
            if self.window.has_timeout():
                self.send_EOT(self.window.seq_number)
                self.window.reset_timer()
            time.sleep(constants.PROCESS_WAIT)

        # Log Transmission Time
        transmission_time = 1000 * (datetime.datetime.now() - start).total_seconds()
        logger.time(str(transmission_time))
        logger.log("Done.")


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
