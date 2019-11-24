from argparse import ArgumentParser
from socket import gethostbyname, gethostname
import logging
import math
import os
import sys

from chunky import Chunky
import constants
from custom_exceptions import PortBindingException
import utils

_logger = logging.getLogger(f"Peer")


class Peer(object):

    def __init__(self, tracker_addr, tracker_port, minimum_alive_time):
        """Constructor.

        Args:
            tracker_addr: The Ip address of the tracker node.
            tracker_port: The port number of the tracker for initial connections.
            minimum_alive_time: The minimum time to stay alive after acquiring all
                files.
        """
        self.tracker_addr = tracker_addr
        self.main_tracker_port = tracker_port
        self.min_alive_time = minimum_alive_time
        self.addr = gethostbyname(gethostname())

    def get_tracker_port(self) -> int:
        """ Connects to the tracker via TCP and receive the port to reconnect to.

        Returns:
             A port number to connect to via.
        """
        try:
            socket, self_port = utils.bind_TCP_port("")
        except PortBindingException:
            return -1

        socket.connect((self.tracker_addr, self.main_tracker_port))
        msg = socket.recv(constants.MAX_BUFFER_SIZE).decode()
        try:
            port = int(msg)
        except ValueError:
            socket.close()
            return -1
        else:
            socket.close()
            return port

    def run(self) -> None:
        """ Runs the peer until it has acquired all files, is not exchanging chunks
            with any other peer and has waited an additional amount of time
            (min_alive_time).
        """
        ## Receive new port.
        ## TODO: do custom exceptions.
        tracker_port = self.get_tracker_port()
        if tracker_port < 0:
            return
        _logger.warning(f"Received new port from tracker: {tracker_port}.")

        ## Disconnect and create new TCP to tracker.
        try:
            socket, peer_port = utils.bind_TCP_port("")
        except PortBindingException:
            _logger.error(
                f"While attempting to connect to new Tracker connection, either could"
                f" not create or bind to port locally."
            )
            return
        socket.settimeout(constants.TCP_TIMEOUT_DURATION)
        socket.connect((self.tracker_addr, tracker_port))
        _logger.warning(f"Connected to individual connection of thread. ")

        # Get id of self from tracker
        self_ID = socket.recv(constants.MAX_BUFFER_SIZE).decode()
        try:
            self.id = int(self_ID)
        except ValueError:
            _logger.error(f"Invalid ID from tracker: {self_ID}. Exiting.")
            return

        ## Send addr & port for other peers to connect to you with
        msg = utils.create_new_peer_message(self.addr, peer_port)
        socket.send(msg)
        _logger.warning(f"Sent Tracker new peer message")

        ## Send filename and number of chunks
        files = os.listdir(constants.PEER_FILE_DIRECTORY)
        file_sizes = [os.path.getsize(f) for f in files]
        no_chunks = [math.ceil(size / constants.CHUNK_SIZE) for size in file_sizes]

        msg = utils.create_new_file_message(self.id, [(file, chunks) for file, chunks in
                                                      zip(files, no_chunks)])
        socket.send(msg)
        _logger.warning(f"Sent Tracker filename and chunk count.")

        ## Get all files, chunks from tracker
        msg = socket.recv(constants.MAX_BUFFER_SIZE)
        chunk_data = utils.parse_chunk_list_message(msg)
        self.chunky = Chunky.create_Chunky(chunk_data)
        _logger.warning(f"Received chunk data from tracker: {chunk_data}.")

        ## Get list of (addr, port) for other peers.
        msg = socket.recv(constants.MAX_BUFFER_SIZE)
        self.peer_info = utils.parse_peer_list_message(msg)
        _logger.warning(f"Received peer data from tracker: {self.peer_info}.")


def main():
    # Parse arguments
    parser = ArgumentParser(description='Peer')
    parser.add_argument("tracker_address", type=str,
                        help="The address of the tracker to connect to.")
    parser.add_argument("tracker_port", type=int,
                        help="The port of the tracker to connect to.")
    parser.add_argument("min_alive_time", type=int,
                        help="The minimum time to stay alive after acquiring all files.")
    args = parser.parse_args()

    # Configure Logging
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    _logger.addHandler(stdout_handler)

    # Run Client
    peer = Peer(args.tracker_address, args.tracker_port, args.min_alive_time)
    peer.run()


if __name__ == "__main__":
    main()
