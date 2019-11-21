import random
from socket import socket, AF_INET, SOCK_STREAM
from typing import Tuple

import constants
from custom_exceptions import PortBindingException


def bind_TCP_port(addr: str) -> Tuple(socket, int):
    """ Attempts to bind to an arbitrary port on the given address.


    Args:
        addr: The IP address to bind with.

    Returns:
         A tuple consisting of:
            * A socket configured for TCP traffic to a random port number.
            * The port number the socket is connected to.

    Raises:
        PortBindingException: If a port could not be binded to after sufficient
            attempts.
    """
    s = socket(AF_INET, SOCK_STREAM)
    for i in range(constants.TRACKER_PORT_CONNECT_ATTEMPTS):
        try:
            port = random.randint(constants.MIN_PORT_NUMBER,
                                  constants.MAX_PORT_NUMBER)
            s.bind((addr, port))
            return (s, port)

            # TODO: fix this code smell (i.e. find actual exceptions)
        except Exception as e:
            continue

    raise PortBindingException()