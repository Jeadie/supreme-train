import logging
import sys


def configure_sender_logger(name, sequence_log="seqnum.log", ack_log="ack.log",
                            time_log: str = "time.log​",
                            info_stdout: bool = False):
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
    class SenderLogger(object):

        def __init__(self):
            self._sequence = logging.getLogger(f"{name}-sequence")
            self._ack = logging.getLogger(f"{name}-ack")
            self._time = logging.getLogger(f"{name}-time")
            self._sequence.setLevel(logging.INFO)
            self._ack.setLevel(logging.INFO)
            self._time.setLevel(logging.INFO)

            # Add log file handlers
            seq_file = logging.FileHandler(sequence_log)
            seq_file.setLevel(logging.INFO)
            self._sequence.addHandler(seq_file)

            ack_file = logging.FileHandler(ack_log)
            ack_file.setLevel(logging.INFO)
            self._ack.addHandler(ack_file)

            time_file = logging.FileHandler(time_log)
            time_file.setLevel(logging.INFO)
            self._time.addHandler(time_file)

            if info_stdout:
                self._log = logging.Logger(f"{name}-log")
                stdout_handler = logging.StreamHandler(stream=sys.stdout)
                stdout_handler.setLevel(logging.INFO)
                self._log.addHandler(stdout_handler)

        def log(self, msg):
            self._log.info(f"[SENDER] - {msg}")

        def ack(self, msg):
            self._ack.info(msg)

        def sequence(self, msg):
            self._sequence.info(msg)

        def time(self, msg):
            self._time.info(msg)

    return SenderLogger()


def configure_receiver_logger(name: str, arrival_log: str="arrival.log",
                              info_stdout: bool = False):
    """ Configures the receiver's logger to send

    Args:
        name: Name of the logger
        arrival_log: Filename of the arrival log
        info_stdout: If True, will output INFO level to stdout.

    Returns:
        A Logger configured with separate sequence, ack and time logs.
    """

    class ReceiverLogger(object):

        def __init__(self):
            self._arrival = logging.Logger(f"{name}-arrival")
            arrival_file = logging.FileHandler(arrival_log)
            arrival_file.setLevel(logging.INFO)
            self._arrival.addHandler(arrival_file)

            if info_stdout:
                self._log = logging.Logger(f"{name}-log")
                stdout_handler = logging.StreamHandler(stream=sys.stdout)
                stdout_handler.setLevel(logging.INFO)
                self._log.addHandler(stdout_handler)

        def log(self, msg):
            self._log.info(f"[RECEIVER] - {msg}")

        def arrival(self, msg):
            self._arrival.info(msg)

    return ReceiverLogger()
