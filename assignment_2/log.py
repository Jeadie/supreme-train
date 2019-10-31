import logging
import sys
from typing import Callable

import constants


def construct_log_level_func(self, log_number) -> Callable:
    """ Constructs a log function for a single log level.

    Args:
        log_number: The log number

    Returns:
        A logging function for a given log number.
    """

    def log_func(message, *args, **kws):
        if self.isEnabledFor(log_number):
            self._log(log_number, message, args, **kws)

    return log_func


def configure_sender_logger(name, sequence_log="seqnum.log", ack_log="ack.log",
                            time_log: str = "time.log​",
                            info_stdout: bool = False) -> logging.Logger:
    """ Configures

    Args:
        name: Name of the logger
        ack_log: Filename of the ack log.
        sequence_log: Filename of the sequence log
        time_log: Filename of the time log.
        info_stdout: If True, will output INFO level to stdout.

    Returns:
        A Logger configured with separate sequence, ack and time logs.
    """
    _logger = logging.getLogger(name)

    if info_stdout:
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        _logger.addHandler(stdout_handler)

    logging.addLevelName(constants.SEQUENCE_LOG_NUM, "SEQUENCE")
    logging.addLevelName(constants.ACK_LOG_NUM, "ACK")
    logging.addLevelName(constants.TIME_LOG_NUM, "TIME")

    # Add specific logger functions to logger
    _logger.sequence = construct_log_level_func(_logger, constants.SEQUENCE_LOG_NUM)
    _logger.ack = construct_log_level_func(_logger, constants.ACK_LOG_NUM)
    _logger.time = construct_log_level_func(_logger, constants.TIME_LOG_NUM)

    # Add file handlers for sequence, ack & time
    seq_file = logging.FileHandler(sequence_log)
    seq_file.setLevel(constants.SEQUENCE_LOG_NUM)
    _logger.addHandler(seq_file)

    ack_file = logging.FileHandler(ack_log)
    ack_file.setLevel(constants.ACK_LOG_NUM)
    _logger.addHandler(ack_file)

    time_file = logging.FileHandler(time_log)
    time_file.setLevel(constants.TIME_LOG_NUM)
    _logger.addHandler(time_file)

    return _logger


def configure_receiver_logger(name: str, arrival_log: str="arrival.log",
                              info_stdout: bool = False) -> logging.Logger:
    """ Configures the receiver's logger to send

    Args:
        name: Name of the logger
        arrival_log: Filename of the arrival log
        info_stdout: If True, will output INFO level to stdout.

    Returns:
        A Logger configured with separate sequence, ack and time logs.
    """
    _logger = logging.getLogger(name)

    # info -> stdout
    if info_stdout:
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        _logger.addHandler(stdout_handler)

    logging.addLevelName(constants.ARRIVAL_LOG_NUM, "ARRIVAL")

    # Add handler for arrival log
    _logger.arrival = construct_log_level_func(_logger, constants.ARRIVAL_LOG_NUM)
    arrival_file = logging.FileHandler(arrival_log)
    arrival_file.setLevel(constants.ARRIVAL_LOG_NUM)
    _logger.addHandler(arrival_file)
    return _logger
