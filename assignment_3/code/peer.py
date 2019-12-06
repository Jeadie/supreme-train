from argparse import ArgumentParser
import logging
import math
import os
from socket import gethostbyname, gethostname, timeout, socket
import sys
import tempfile
import threading
import time
from typing import List, Tuple, Dict

from chunky import Chunky
import constants
from constants import MessageCode
from custom_exceptions import (
    PortBindingException,
    TrackerHandshakeException,
    UnexpectedMessageReceivedException
)
from printer import PeerPrinter
import utils

logging.basicConfig(format='[PEER] - %(message)s')
_logger = logging.getLogger(f"Peer")
_logger.setLevel(logging.ERROR)

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

        # Flag used to check if the peer has given data in a time period.
        self.giving_data = False

        # Mapping of files -> chunks
        self.acquired_files = {}


    def get_tracker_port(self) -> int:
        """ Connects to the tracker via TCP and receive the port to reconnect to.

        Returns:
             A port number to connect to via.
        """
        try:
            socket, self_port = utils.bind_TCP_port("")
            socket.connect((self.tracker_addr, self.main_tracker_port))
        except PortBindingException:
            _logger.error(f"Could select a port to bind to.")
            return -1
        except ConnectionRefusedError as e:
            _logger.error(f"Could not connect to tracker node to set up individual port. Error: {str(e)}.")
            return -1

        msg = socket.recv(constants.MAX_BUFFER_SIZE).decode()
        try:
            port = int(msg)
        except ValueError:
            socket.close()
            return -1
        else:
            socket.close()
            return port

    def handle_handshake(self, shard_dir) -> Tuple[socket, socket]:
        """ Handles initial handshake with tracker.

        Args:
            shard_dir:

        Returns:
            A tuple containing:
                * A socket connected with TCP to the tracker
                * A socket prepared to listen for UDP data from other peers.
        Raises:
            TrackerHandshakeException: If there is an error establishing a connection
                with the tracker and communicating the necessary messages.
        """
        ## Receive new port.
        tracker_port = self.get_tracker_port()
        if tracker_port < 0:
            _logger.error("Could not establish a TCP port for the peer.")
            raise TrackerHandshakeException()
        _logger.warning(f"Received new port from tracker: {tracker_port}.")

        ## Disconnect and create new TCP to tracker.
        try:
            tracker_socket, peer_tracker_port = utils.bind_TCP_port("")
        except PortBindingException:
            _logger.error(
                f"While attempting to connect to new Tracker connection, either could"
                f" not create or bind to port locally."
            )
            raise TrackerHandshakeException()

        tracker_socket.connect((self.tracker_addr, tracker_port))
        _logger.warning(f"Connected to individual connection of thread. ")

        # Get id of self from tracker
        self_ID = tracker_socket.recv(constants.MAX_BUFFER_SIZE).decode()
        try:
            self.id = int(self_ID)
        except ValueError:
            _logger.error(f"Invalid ID from tracker: {self_ID}. Exiting.")
            raise TrackerHandshakeException()

        ## Send addr & port for other peers to connect to you with
        try:
            server_socket, peer_port = utils.bind_UDP_port("")

        except PortBindingException:
            _logger.error(
                f"While attempting to connect to new Tracker connection, either could"
                f" not create or bind to port locally."
            )
            raise TrackerHandshakeException()

        msg = utils.create_new_peer_message(self.id, self.addr, peer_port)
        tracker_socket.send(msg)
        _logger.warning(f"[{self.id}]: Sent Tracker new peer message")

        ## Send filename and number of chunks
        files = os.listdir(constants.PEER_FILE_DIRECTORY)
        _logger.warning(f"Peer {self.id} has files: {files}.")
        file_sizes = [os.path.getsize(f"{constants.PEER_FILE_DIRECTORY}{f}") for f in
                      files]
        no_chunks = [math.ceil(size / constants.CHUNK_SIZE) for size in file_sizes]

        msg = utils.create_new_file_message(self.id, [(file, chunks) for file, chunks in
                                                      zip(files, no_chunks)])
        tracker_socket.send(msg)
        for file, chunks in zip(files, no_chunks):
            self.acquired_files[file] = list(range(chunks))

            # Shard file chunks
            with open(f"{constants.PEER_FILE_DIRECTORY}{file}", "r") as f:
                for chunk in self.acquired_files[file]:
                    f.seek(constants.CHUNK_SIZE * chunk)
                    data = f.read(constants.CHUNK_SIZE)
                    self.shard_file_chunk(shard_dir, file, chunk, data)


        _logger.warning(f"[{self.id}]: Sent Tracker filename and chunk count.")

        ## Get all files, chunks from tracker
        msg = tracker_socket.recv(constants.MAX_BUFFER_SIZE)
        chunk_data = utils.parse_chunk_list_message(msg)
        self.chunky = Chunky.create_Chunky(chunk_data)
        _logger.warning(f"[{self.id}]: Received chunk data from tracker: {chunk_data}.")

        ## Get list of (addr, port) for other peers.
        msg = tracker_socket.recv(constants.MAX_BUFFER_SIZE)
        self.peer_info = utils.parse_peer_list_message(msg)
        _logger.warning(
            f"[{self.id}]: Received peer data from tracker: {self.peer_info}.")

        return tracker_socket, server_socket

    def shard_file_chunk(self, tmp_dir: str, filename: str, chunk: id, data: str) -> None:
        """ Shards a file chunk to disk.

        Args:
            tmp_dir: Directory to store temporary shards
            filename: The name of the originl file
            chunk: The chunk id
            data: The data to save to file.
        """
        with open (f"{tmp_dir}/{filename}_{chunk}.chunk", "w") as f:
            f.write(data)

    def load_shard_file_chunk(self, tmp_dir: str, filename: str, chunk: id) -> str:
        """ Loads data from a chunk to file.

        Args:
            tmp_dir: Directory to store temporary shards
            filename: The name of the originl file
            chunk: The chunk id

        Returns:
            Data from a shard
        """
        with open (f"{tmp_dir}/{filename}_{chunk}.chunk", "r") as f:
            return f.read()

    def run(self) -> None:
        """ Runs the peer until it has acquired all files, is not exchanging chunks
            with any other peer and has waited an additional amount of time
            (min_alive_time).
        """
        with tempfile.TemporaryDirectory() as shard_directory:
            self.shard_dir = shard_directory
            try:
                tracker_socket, server_socket = self.handle_handshake(shard_directory)
            except TrackerHandshakeException:
                _logger.error(f"Tracker handshake failed. Peer terminating.")
                return None

            # Setup giving thread.
            giving_t = threading.Thread(target=self.handle_giving_port, args=(server_socket, shard_directory))
            giving_t.start()

            # Acquire files or wait to exit.
            while constants.FOREVER:
                self.handle_messages_from_tracker(tracker_socket)

                if self.chunky.has_all_files(self.acquired_files):
                    _logger.warning(f"[{self.id}]: Have all files, sleeping")

                    # Check if peer gives data whilst sleeping.
                    self.giving_data = False
                    time.sleep(self.min_alive_time)

                    # Check for new messages
                    self.handle_messages_from_tracker(tracker_socket)
                    _logger.warning(f"[{self.id}]: Handled any extra tracker messages")

                    # Check if no new files are in system and peer has not given data whilst asleep.
                    if self.chunky.has_all_files(self.acquired_files) and not self.giving_data:

                        # Else disconnect.
                        tracker_socket.send(utils.create_peer_disconnect_message(self.id))
                        _logger.info(f"[{self.id}]: Peer has disconnected.")
                        tracker_socket.close()
                        server_socket.close()

                        self.save_files(self.acquired_files, self.shard_dir)

                        # Assume peer has no partial files.
                        PeerPrinter.print_peer_disconnect(self.id, self.acquired_files.keys())
                        return

                # Get files from peer
                else:
                    _logger.warning(f"Peer {self.id} acquiring files. Has {self.acquired_files}")
                    self.acquire_files(tracker_socket)

    def save_files(self, acquired_files: Dict[str, List[int]], shard_dir: str) -> None:
        """ Saves files in data folder, from temporary shards.

        Args:
            acquired_files: A mapping of filenames to a list of chunk numbers.
            shard_dir: The directory containing the file shards.
        """
        for file, chunks in acquired_files.items():
            chunks.sort()

            # Save time by not remaking own files from shards.
            if not os.path.exists(f"{constants.PEER_FILE_DIRECTORY}{file}"):
                with open(f"{constants.PEER_FILE_DIRECTORY}{file}", "w") as whole_file:
                    for c in chunks:
                        with open(f"{shard_dir}/{file}_{c}.chunk", "r") as shard_file:
                            whole_file.write(shard_file.read())


    def acquire_files(self, tracker_socket):
        """ Attempts to acquire all files from other peers.
        """
        while not self.chunky.has_all_files(self.acquired_files):
            # Ask for file
            peerId, filename, chunks = self.chunky.get_next_peer(self.acquired_files)
            _logger.warning(f"Peer {self.id} asking for {filename} {chunks} from {peerId}. {self.peer_info}.")
            chunks = self.ask_for_file(self.peer_info[peerId], filename, chunks)
            for c in chunks:
                self.chunky.add_chunk_to_peer(self.id, filename, c)
                tracker_socket.send(utils.create_peer_acquired_chunk_message(self.id, filename, c))
            has_chunks =self.acquired_files.get(filename, False)
            if has_chunks:
                self.acquired_files[filename].extend(chunks)
            else:
                self.acquired_files[filename] = chunks

            # Handle messages from Tracker.
            self.handle_messages_from_tracker(tracker_socket)

    def handle_messages_from_tracker(self, tracker_socket):
        """ Handles any new messages from the tracker and updates the peer's state
        accordingly.

        Args:
            tracker_socket: A socket connected to the tracker via TCP.
        """
        msg_queue = []
        utils.append_to_message_queue(msg_queue, tracker_socket)

        while len(msg_queue) != 0:
            try:
                msg = msg_queue.pop(0)
                utils.append_to_message_queue(msg_queue, tracker_socket)
            except timeout:
                return
            _logger.warning(f"[{self.id}]: Deconstructing message: {msg}")
            code, _ = msg.decode().split(constants.MESSAGE_SEPARATOR, 1)
            code = int(code)
            if code == MessageCode.PEER_DISCONNECT.value:
                peer = utils.parse_peer_disconnect_message(msg)
                self.chunky.remove_peer(peer)

            elif code == MessageCode.PEER_ACQUIRED_FILE.value:
                PeerId, file, chunk = utils.parse_peer_acquired_chunk_message(msg)
                self.chunky.add_file(PeerId, file, [chunk])

            elif code == MessageCode.NEW_FILES_IN_SYSTEM.value:
                peer_ID, files = utils.parse_new_file_message(msg)
                for file in files:
                    filename, no_chunks = file
                    self.chunky.add_file(peer_ID, filename, no_chunks)

            elif code == MessageCode.PEER_ACQUIRED_CHUNK.value:
                peer_ID, filename, chunkId = utils.parse_peer_acquired_chunk_message(msg)
                self.chunky.add_chunk_to_peer(peer_ID, filename, chunkId)


            elif code == MessageCode.NEW_PEER_CONNECTION.value:
                new_id, addr, port = utils.parse_new_peer_message(msg)
                _logger.warning(f"[{self.id}]: {new_id} {addr} {port}")
                if self.peer_info.get(new_id, None):
                    _logger.warning(f"[{self.id}]: Overwriting network details for peer: {new_id}.")
                try:
                    port = int(port)
                except ValueError:
                    return
                self.peer_info[int(new_id)] = (addr, port)
            else:
                _logger.warning(f"[{self.id}]: Received message from tracker with unexpected code: {code}.")


    def ask_for_file(self, peer_info: Tuple[str, int], filename: str, chunks: List[int]) -> List[int]:
        """ Asks a peer for a given file.

        Args:
            peer_info: The address and port of a peer.
            filename: The filename to ask the peer for.
            chunks: The list of chunks to ask the peer for.

        Returns:
            The list of chunk Ids acquired for the file.
        """
        # Create new TCP socket
        try:
            socket, port = utils.bind_UDP_port("")
        except PortBindingException:
            return False


        # Ask for chunks
        socket.sendto(utils.create_chunk_request_message(filename, chunks), peer_info)

        # Get each file, store in memory
        chunks_data = []
        try:
            msg, addr = socket.recvfrom(constants.MAX_BUFFER_SIZE)
            filename, c_id, data = utils.parse_file_chunk_message(msg)
            self.shard_file_chunk(self.shard_dir, filename, c_id, data)
            chunks_data.append(c_id)
        except timeout:
            _logger.info(f"Timeout occured when waiting for file: {filename}.")

        return chunks_data

    def handle_giving_port(self, socket: socket, shard_directory: str):
        """ A thread dedicated to listening for other peers communicating with it and
        sending them file chunks that this peer has locally.

        Args:
            socket: A configured socket ready to accept TCP connections.
            shard_directory: The temporary directory containing file shards.
        """

        while constants.FOREVER:
            try:
                msg, peer_addr = socket.recvfrom(constants.MAX_BUFFER_SIZE)
                self.giving_data = True
                filename, chunks = utils.parse_chunk_request_message(msg)

            # No new messages.
            except timeout:
                continue

            # Main thread has ended. Terminate likewise
            except OSError:
                return

            except UnexpectedMessageReceivedException as e:
                _logger.error(f"Error while parsing message from peer. Error: {str(e)}")
                continue

            for chunk in chunks:
                with open(f"{shard_directory}/{filename}_{chunk}.chunk", "r") as f:
                    data = f.read(constants.CHUNK_SIZE)
                    socket.sendto(utils.create_file_chunk_message(filename, chunk, data), peer_addr)

            self.giving_data = True

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
    stdout_handler.setLevel(logging.ERROR)
    # _logger.addHandler(stdout_handler)


    # Run Client
    peer = Peer(args.tracker_address, args.tracker_port, args.min_alive_time)
    peer.run()


if __name__ == "__main__":
    main()
