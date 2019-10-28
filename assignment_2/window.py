import datetime
from packet import packet
from socket import socket, AF_INET, SOCK_DGRAM


class Window(object):

    def __init__(self, size, filename: str, timeout: datetime.timedelta ):
        """

        Args:
            size: Window size to use in the window.
            filename: The name of the file to load.
            timeout: The timeout to use when resending packets.
        """
        self.size = size
        self.filename = filename
        self.d_timeout = timeout
        self.window = []
        self.seq_number = 0
        self.base_number = 0


    def is_full(self) -> bool:
        """ Returns True if the window is full and more data cannot be added,
            False otherwise.
        """
        return self.seq_number >= self.base_number + self.size

    def add_data(self, data: str):
        """ Adds and sends data to the window in the next available slot.

        Args:
            data: The data to be added in the window slot, expected to be fixed-size
                bytes.
        """
        if not len(self.window):
            self.timer = datetime.datetime.now()

        socket(AF_INET, SOCK_DGRAM).sendto(
            packet.create_packet(self.seq_number, data).get_udp_data(),
            (self.hostname, self.ack_port))
        self.window.append((self.seq_number, data))
        self.seq_number += 1

    def has_timeout(self)-> True:
        """ Returns True if the current time is past the timer + timeout delta. False, Otherwise.
        """
        return datetime.datetime.now() > self.timer + self.d_timeout

    def reset_timer(self):
        """ Resets the timer for the window."""
        self.timer = datetime.datetime.now()

    def resend_all(self):
        """ Resends all data in the window."""
        for w in self.window:
            num, data = w
            socket(AF_INET, SOCK_DGRAM).sendto(
                packet.create_packet(num, data).get_udp_data(),
                (self.hostname, self.ack_port))

    def update_base_number(self, seq_num):
        """

        Args:
            seq_num: The new sequence number for the window.
        :return:
        """
        self.base_number = seq_num + 1
        for packet in self.window:
            num, data = packet
            if num <= self.base_number:
                self.window.remove(packet)


