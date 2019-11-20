import datetime
from typing import Tuple
from socket import socket, AF_INET, SOCK_DGRAM

from packet import packet

import constants


class Window(object):

    def __init__(self, size, logger,
                 timeout: datetime.timedelta = datetime.timedelta(
                     milliseconds=constants.TIMEOUT_VALUE)):
        """
        Args:
            size: Window size to use in the window.
            logger: Logger with following methods: log, sequence:= Callable(str)->None
            timeout: The timeout to use when resending packets.
        """
        self.size = size
        self.d_timeout = timeout
        self._logger = logger
        self.window = [None for i in range(constants.MODULO_RANGE)]
        self.seq_number = 0
        self.base_number = 0
        self.timer = datetime.datetime.now()

    def get_size(self) -> int:
        """ Returns the number of packets in the window.
        """
        return len([i for i in self.window if i is not None])

    def is_full(self) -> bool:
        """ Returns True if the window is full and more data cannot be added,
            False otherwise.
        """
        return self.get_size() >= self.size

    def add_data(self, data: str, addr: Tuple[str, int]):
        """ Adds and sends data to the window in the next available slot.

        Args:
            data: The data to be added in the window slot, expected to be fixed-size
                bytes.
            addr: A hostname, port tuple to send data to.
        """

        socket(AF_INET, SOCK_DGRAM).sendto(
            packet.create_packet(self.seq_number, data).get_udp_data(),
            addr)
        self._logger.sequence(self.seq_number)
        self._logger.log(f"Sent packet with no: {self.seq_number}")
        self.window[self.seq_number] = data

        self.seq_number = (self.seq_number + 1) % constants.MODULO_RANGE

    def has_timeout(self) -> bool:
        """ Returns True if the current time is past the timer + timeout delta. False,
        otherwise.

        Does not change timer state.
        """
        return datetime.datetime.now() > self.timer + self.d_timeout

    def finished(self, receive_num) -> bool:
        """ Returns True if the window has sent all data. False, otherwise.

        Args:
            receive_num: The packet number the receiver is expecting.
        """
        return (self.seq_number - 1) % constants.MODULO_RANGE == receive_num

    def reset_timer(self):
        """ Resets the timer for the window."""
        self.timer = datetime.datetime.now()

    def resend_all(self, addr: Tuple[str, int]):
        """ Resends all data in the window.

        Args:
            addr: A hostname, port tuple to send data to.
        """
        for num, data in zip(range(constants.MODULO_RANGE), self.window):
            if data:
                self._logger.sequence(num)
                socket(AF_INET, SOCK_DGRAM).sendto(
                    packet.create_packet(num, data).get_udp_data(), addr)
                self._logger.log(f"Resent packet with no: {num}")
        self.reset_timer()

    def update_base_number(self, next_seq_num):
        """ Updates the base number

        Args:
            acked_seq_num: The new sequence number for the window.
        :return:
        """
        if next_seq_num == self.base_number:
            return

        if self.base_number > next_seq_num:
            for i in range(self.base_number, constants.MODULO_RANGE):
                self.window[i] = None

            for i in range(0, next_seq_num):
                self.window[i] = None

        else:
            for i in range(self.base_number, next_seq_num):
                self.window[i] = None
        self.base_number = next_seq_num
