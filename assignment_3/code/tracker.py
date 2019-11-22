import logging
import queue
from socket import socket, timeout, gethostbyname, gethostname
import threading
from typing import Queue

from chunky import Chunky
import constants
from custom_exceptions import PortBindingException
from queuey import Queuey
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
        self.chunky = Chunky()
        self.queuey = Queuey()
        # Choose and save port number to file.
        try:
            self.sock = utils.bind_TCP_port(self.addr)
        except PortBindingException as e:
            _logger.error(
                f"Could not connect to a port after "
                f"{constants.TRACKER_PORT_CONNECT_ATTEMPTS} attempts. Terminating."
            )
            return

    def handle_single_peer(self, socket: socket, peerId: int, queue: Queue) -> None:
        """ Handles communication with a single socket.

        Args:
            socket: A configured TCP socket to the peer.
        """

        # Wait for peer to reconnect (peer will drop connection, then connect to new
        # peer specific port)

        while constants.FOREVER:
            try:
                c, addr = self.sock.accept()
                break
            except timeout:
                # Repeat indefinitely.
                continue

        self.queuey.add_peer(peerId, addr)

        # Get Filename and sizefrom client
        filename, chunks = socket.recv().split(constants.MESSAGE_SEPARATOR, 1)
        try:
            chunks = int(chunks)
        except ValueError as e:
            socket.close()
            return

        # Update Chunky with new peer and new files.
        self.queuey.add_file(peerId, filename, chunks)

        # Poll (until disconnection breaks loop)
        while constants.FOREVER:
            try:
                message = socket.recv()
                isDone, chunks = utils.parse_peer_message(message)
                if isDone:
                    _logger.info(f"Peer {peerId} is disconnecting.")
                    self.queuey.disconnect(peerId)
                    socket.close()
                    break
                else:
                    for chunk in chunks:
                        filename, chunkId = chunk
                        self.queuey.peer_acquired_chunk(peerId, filename, chunkId)

            except timeout:
                # If messages to send to peer.
                if not queue.empty():
                    try:
                        message = queue.get_nowait()
                        socket.send(message)
                    except queue.Empty:
                        continue


    def run(self) -> None:
        """ Runs the tracker server indefinitely.
        """
        while constants.FOREVER:
            try:
                c, addr = self.sock.accept()

            except timeout:
                # Empty Queue
                self.queuey.process_tasks()

            # Create new TCP connection, send port to peer node.
            socket, port = utils.bind_TCP_port(self.addr)
            socket.settimeout(constants.TCP_TIMEOUT_DURATION)
            c.send(port)
            c.close()

            # Add queue
            id, message_queue = self.queuey.add_thread()

            # Start thread to communicate with single peer
            t = threading.Thread(target=self.handle_single_peer, args=(socket, id, message_queue))
            t.start()



def main():
    addr = gethostbyname(gethostname())
    Tracker.run(addr)


if __name__ == "__main__":
    main()
