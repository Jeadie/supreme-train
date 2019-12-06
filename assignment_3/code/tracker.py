import logging
import queue
from socket import socket, timeout, gethostbyname, gethostname
import sys
import threading

from chunky import Chunky
import constants
from constants import MessageCode
from custom_exceptions import PortBindingException, UnexpectedMessageReceivedException
from queuey import Queuey
from printer import TrackerPrinter
import utils

logging.basicConfig(format='[TRACKER] - %(message)s')
_logger = logging.getLogger(f"Tracker")
_logger.setLevel(logging.ERROR)


class Tracker(object):
    """Tracker service for the P2P network."""

    def __init__(self, addr):
        """ Constructor.

        Selects a port to bind to and saves the port number to file.
        """
        self.addr = addr

        # Initiate chunk data structure, queue manager and printer
        self.chunky = Chunky()
        self.queuey = Queuey()

        # TODO: Maybe printer should be handled in Queuey?
        self.printer = TrackerPrinter()

        # Choose and save port number to file (assignment requirement).
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

    def handle_single_peer(self, socket: socket, connPeerId: int,
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
        conn.send(str(connPeerId).encode())
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

            id, data = utils.parse_new_file_message(msg_queue.pop(0))
            # Update Chunky with new peer and new files.
            for file in data:
                _logger.warning(f"GETTING FILE: {file}")
                filename, chunks = file
                self.queuey.add_file(id, filename, chunks)
            self.printer.print_new_peer(id, data)

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
        _logger.warning(f"{connPeerId} starting to loop")
        while constants.FOREVER:
            try:
                msg = conn.recv(constants.MAX_BUFFER_SIZE)
                if not msg:
                    raise timeout

                try:
                    msg_code = utils.parse_peer_message(msg)

                except UnexpectedMessageReceivedException as e:
                    _logger.error(
                        f"An unexpected Message was received from peer. "
                        f"Error: {str(e)}"
                    )

                _logger.warning(f"{connPeerId} handling message: {msg_code}, {msg}")
                if msg_code == MessageCode.PEER_DISCONNECT:
                    try:
                        msg_int, msg_chunk = msg.decode().split(
                            constants.MESSAGE_SEPARATOR, 1)
                        peer_id = int(msg_chunk)
                    except ValueError:
                        _logger.error(f"Peer Disconnect message has invalid payload: {msg_chunk}.")
                        break

                    _logger.warning(f"Peer {peer_id} is disconnecting.")
                    self.queuey.disconnect(peer_id)
                    self.printer.print_peer_disconnect(peer_id, self.chunky.get_peers_files(peer_id))
                    if peer_id == connPeerId:
                        socket.close()
                        return

                elif msg_code == MessageCode.PEER_ACQUIRED_CHUNK:
                    peer_id, filename, chunk = utils.parse_peer_acquired_chunk_message(msg)
                    self.queuey.peer_acquired_chunk(connPeerId, filename, chunk)
                    self.printer.print_peer_acquire_chunk(
                        connPeerId,
                        chunk,
                        self.chunky.get_num_chunks(filename),
                        filename
                    )

                _logger.warning(f"{connPeerId} handling queue")
                msgs = utils.get_messages_from_queue(queue)
                for m in msgs:
                    _logger.warning(f"{connPeerId} sent message {m}.")
                    conn.send(m)
                if len(msgs) == 0:
                    _logger.warning(f"{connPeerId} queue empty.")


            except timeout:
                _logger.warning(f"{connPeerId} handling queue 2")
                # If messages to send to peer.
                msgs = utils.get_messages_from_queue(queue)
                for m in msgs:
                    _logger.warning(f"{connPeerId} sent message {m}.")
                    conn.send(m)
                if len(msgs) == 0:
                    _logger.warning(f"{connPeerId} queue empty.")



        _logger.error(f"TRACKER THREAD DONE: {connPeerId}")


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
    stdout_handler.setLevel(logging.ERROR)
    # _logger.addHandler(stdout_handler)

    addr = gethostbyname(gethostname())


    t = Tracker("127.0.0.1")
    t.run()


if __name__ == "__main__":
    main()
