import datetime
from typing import Tuple
from socket import socket, AF_INET, SOCK_DGRAM

from packet import packet

import constants


class Window(object):

    def __init__(self, size, filename: str,
                 timeout: datetime.timedelta = datetime.timedelta(
                     milliseconds=constants.TIMEOUT_VALUE)):
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

    def add_data(self, data: str, addr: Tuple[str, int]):
        """ Adds and sends data to the window in the next available slot.

        Args:
            data: The data to be added in the window slot, expected to be fixed-size
                bytes.
            addr: A hostname, port tuple to send data to.
        """
        if not len(self.window):
            self.timer = datetime.datetime.now()

        socket(AF_INET, SOCK_DGRAM).sendto(
            packet.create_packet(self.seq_number, data).get_udp_data(),
            addr)
        print(f"[SENDER] - Sent packet with no: {self.seq_number}")
        self.window.append((self.seq_number, data))
        self.seq_number += 1

    def has_timeout(self) -> True:
        """ Returns True if the current time is past the timer + timeout delta. False, Otherwise.
        """
        return datetime.datetime.now() > self.timer + self.d_timeout

    def reset_timer(self):
        """ Resets the timer for the window."""
        self.timer = datetime.datetime.now()

    def resend_all(self, addr: Tuple[str, int]):
        """ Resends all data in the window.

        Args:
            addr: A hostname, port tuple to send data to.
        """
        for w in self.window:
            num, data = w
            #socket(AF_INET, SOCK_DGRAM).sendto(
            #    packet.create_packet(num, data).get_udp_data(), addr)
            # print(f"[SENDER] - Sent packet with no: {num}")

    def update_base_number(self, next_seq_num):
        """ Updates the base number

        Args:
            acked_seq_num: The new sequence number for the window.
        :return:
        """
        self.base_number = next_seq_num
        for packet in self.window:
            num, data = packet
            if num < self.base_number:
                self.window.remove(packet)
