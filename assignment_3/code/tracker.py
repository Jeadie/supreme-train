import logging
from socket import socket, timeout, gethostbyname, gethostname
import threading

from chunky import Chunky
import constants
from custom_exceptions import PortBindingException
import utils

_logger = logging.getLogger(f"Tracker")


class Tracker(object):
    """Tracker service for the P2P network."""

    def __init__(self, addr):
        """ Constructor.

        Selects a port to bind to and saves the port number to file.
        """
        self.addr = addr

        # Initiate chunk data structure
        self.chunks = Chunky()

        # Choose and save port number to file.
        try:
            self.sock = utils.bind_TCP_port(self.addr)
        except PortBindingException as e:
            _logger.error(
                f"Could not connect to a port after "
                f"{constants.TRACKER_PORT_CONNECT_ATTEMPTS} attempts. Terminating."
            )
            return

    def handle_single_peer(self, socket: socket) -> None:
        """ Handles communication with a single socket.

        Args:
            socket: A configured TCP socket to the peer.
        """
        pass

        # Get Filename and sizefrom client

        # Update Chunky with new peer and new files.

        # Poll

    def run(self) -> None:
        """ Runs the tracker server indefinitely.
        """
        while constants.FOREVER:
            try:
                c, addr = self.sock.accept()
            except timeout:
                continue

            # Create new TCP connection, send port to peer node.
            socket, port = utils.bind_TCP_port(self.addr)
            c.send(port)
            c.close()

            # Start thread to communicate with single peer
            t = threading.Thread(target=self.handle_single_peer, args=(socket))
            t.start()



def main():
    addr = gethostbyname(gethostname())
    Tracker.run(addr)


if __name__ == "__main__":
    main()
