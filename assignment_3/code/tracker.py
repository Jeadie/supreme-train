import logging
import queue
from socket import socket, timeout, gethostbyname, gethostname
import sys
import threading

from chunky import Chunky
import constants
from custom_exceptions import PortBindingException, UnexpectedMessageReceivedException
from queuey import Queuey
import utils

logging.addLevelName(constants.TRACKER_OUTPUT_LOGGING_LEVEL, "OUTPUT")
logging.basicConfig(format='[TRACKER] - %(message)s')
_logger = logging.getLogger(f"Tracker")

def output(self, message, *args, **kws):
    if self.isEnabledFor(constants.TRACKER_OUTPUT_LOGGING_LEVEL):
        self._log(constants.TRACKER_OUTPUT_LOGGING_LEVEL, message, args, **kws)
_logger.output = output


# TODO: ADD required outputs
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
            self.sock, self.port = utils.bind_TCP_port(self.addr)

            with open(constants.TRACKER_PORT_FILENAME, "w") as f:
                f.write(str(self.port))

            _logger.warning(f"Created main tracker socket at port: {self.port}.")
            self.sock.settimeout(1)
            self.sock.listen(constants.MAX_QUEUED_CONNECTIONS)

        except PortBindingException as e:
            _logger.error(
                f"Could not connect to a port after "
                f"{constants.TRACKER_PORT_CONNECT_ATTEMPTS} attempts. Terminating."
            )
            return

    def handle_single_peer(self, socket: socket, peerId: int,
                           queue: queue.Queue) -> None:
        """ Handles communication with a single socket.

        Args:
            socket: A configured TCP socket to the peer.
        """

        # Wait for peer to reconnect (peer will drop connection, then connect to new
        # peer specific port)
        while constants.FOREVER:
            try:
                conn, addr = socket.accept()
                # Thread only expect a single client.
                socket.close()
                break
            except timeout:
                # Repeat indefinitely.
                continue

        # Now peer has reconnected, send it its ID.
        conn.send(str(peerId).encode())
        conn.settimeout(constants.TCP_PEER_TIMEOUT_DURATION)

        msg_queue = []

        # Initial tracker-peer handshake
        try:
            # Get the IP & port that other peers can connect with
            utils.append_to_message_queue(msg_queue, conn)

            new_peer, peer_addr, port = utils.parse_new_peer_message(
                msg_queue.pop(0))
            self.queuey.add_peer(new_peer, (peer_addr, port))

            # Get Filename and sizefrom client
            utils.append_to_message_queue(msg_queue, conn)
            print("MESSAGE", msg_queue)
            id, data = utils.parse_new_file_message(msg_queue.pop(0))
            # Update Chunky with new peer and new files.
            for file in data:
                _logger.warning(f"GETTING FILE: {file}")
                filename, chunks = file
                self.queuey.add_file(id, filename, chunks)

            # Send list of files, chunks, peers to peer.
            msg = utils.create_chunk_list_message(self.chunky.files)
            conn.send(msg)

            # Send list of peer -> (addr, port) to peer
            msg = utils.create_peer_list_message(self.queuey.peer_info)
            conn.send(msg)
        except UnexpectedMessageReceivedException as e:
            _logger.error(
                f"An error occurred in initial Peer-Tracker handshake. "
                f"Error: {str(e)}."
            )

        # Poll (until disconnection breaks loop)
        while constants.FOREVER:
            try:
                msg = conn.recv(constants.MAX_BUFFER_SIZE)
                if not msg:
                    raise timeout

                try:
                    isDone, filename, chunk = utils.parse_peer_message(msg)
                except UnexpectedMessageReceivedException as e:
                    _logger.error(
                        f"An unexpected Message was received from peer. "
                        f"Error: {str(e)}"
                    )

                # chunks = [chunk]
                if isDone:
                    _logger.warning(f"Peer {peerId} is disconnecting.")
                    self.queuey.disconnect(peerId)
                    socket.close()
                    break
                else:
                    # for chunk in chunks:
                    #     filename, chunkId = chunk
                    self.queuey.peer_acquired_chunk(peerId, filename, chunk)

            except timeout:
                # If messages to send to peer.
                if not queue.empty():
                    try:
                        message = queue.get_nowait()
                        conn.send(message)
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
                self.queuey.process_tasks(self.chunky)
                continue

            _logger.warning(f"Received new connection from peer.")
            # Create new TCP connection, send port to peer node.
            socket, port = utils.bind_TCP_port(self.addr)
            socket.listen(constants.MAX_QUEUED_CONNECTIONS)
            c.send(str(port).encode())
            c.close()

            # Add queue
            id, message_queue = self.queuey.add_thread()
            _logger.warning(f"Tracker new connection at port: {port}.")
            # Start thread to communicate with single peer
            t = threading.Thread(target=self.handle_single_peer,
                                 args=(socket, id, message_queue,))
            t.start()


def main():
    # Setup Logging
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    # _logger.addHandler(stdout_handler)

    addr = gethostbyname(gethostname())

    t = Tracker("127.0.0.1")
    t.run()


if __name__ == "__main__":
    main()
