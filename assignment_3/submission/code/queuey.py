import queue
from asyncio.queues import QueueEmpty as QEmpty
import logging
from typing import Tuple

from chunky import Chunky
import constants
import utils

queue_logger = logging.getLogger(f"Queuey")
queue_logger.setLevel(logging.ERROR)


class Queuey(object):
    """Handle messages to and from peer threads queues."""

    def __init__(self):
        self.thread_count = 0
        self.outbound_message_queues = []
        self.peer_info = {}

        # Queue holds funcs: Callable[Chunky] -> str; where str is a message to broadcast to all peers.
        self.task_queue = queue.Queue()

    def process_tasks(self, chunky: Chunky) -> None:
        """ Processes all tasks in the queue.

        Args:
            chunky: A Chunk management object.
        """
        # if self.has_tasks():
        while constants.FOREVER:
            try:
                t = self.task_queue.get_nowait()

                if t is None:
                    break

                message = t(chunky)
                queue_logger.warning(f"[QUEUEY] - Broadcast message: {message}.")
                self.broadcast_message(message)

                # An asynico Queue specific requirement.
                self.task_queue.task_done()

            except (queue.Empty, QEmpty) :
                return None

    def broadcast_message(self, message: bytes) -> None:
        """ Broadcasts a message to all peers.

        Args:
            message: An arbitrary message to send to all peers.

        Returns:
            None.
        """
        for queue in self.outbound_message_queues:
            queue.put(message)

    def has_tasks(self) -> bool:
        """ Returns True if there is at least one task in the queue, False otherwise."""
        return not self.task_queue.empty()

    def add_thread(self) -> Tuple[int, queue.Queue]:
        """ Prepare a new thread to be added to the queueing system.

        Returns:
            A tuple consisting of:
                * An ID to use to handle all future interactions with Queuey.
                * A message queue that the thread will receive message to forward on
                    to its peer.
        """
        Id = self.thread_count
        self.thread_count += 1
        q = queue.Queue()
        self.outbound_message_queues.append(q)
        return Id, q

   #####################################################################################
   ############################## TASK CREATION FUNCTIONS ##############################
   #####################################################################################

    def add_peer(self, peerId: int, socket_info: Tuple[str, int]):
        """

        Args:
            peerId: The id of the peer.
            socket_info: A tuple containing the address and port to contact the peer via.
        """
        self.peer_info[peerId] = socket_info
        addr, port = socket_info

        def apply_add_peer(chunky):
            return utils.create_new_peer_message(peerId, addr, port)

        self.task_queue.put(apply_add_peer)

    def add_file(self, peerId: int, filename: str, chunks: int ) -> None:
        """ Adds a file to Chunky and add the peer to all corresponding chunks.

        Args:
            peerId: The ID of the peer whom has all chunks from a file.
            filename: The filename of the file to reference.
            chunks: The number of chunks the file has.
        """
        def apply_add_file(chunky):
            if peerId > chunky.peers:
                chunky.add_peer(peerId)
            chunky.add_file(peerId, filename, chunks)
            return utils.create_new_file_message(peerId, [(filename, chunks)])

        self.task_queue.put(apply_add_file)

    def disconnect(self, peerId: int) -> None:
        """ Handles when a peer disconnects.

        Sends messages to all remaining peers that peer with peerId has disconnected.

        Args:
            peerId: The ID of the peer that has disconnected.
        """

        def apply_disconnect(chunky):
            chunky.remove_peer(peerId)
            self.peer_info.pop(peerId)
            return utils.create_peer_disconnect_message(peerId)

        self.task_queue.put(apply_disconnect)

    def peer_acquired_chunk(self, peerId: int, filename: str, chunkId: int) -> None:
        """ Handles when a peer has acquired a file chunk.

        Sends a message to all other peers that the peer with peerId now has a specific
        chunk from a specific file.

        Args:
            peerId: The Id of the peer whom has acquired the file.
            filename: The name of the file that has had a chunk acquired.
            chunkId:  The specific chunk from the file that has been acquired.
        """

        def apply_peer_acquired_chunk(chunky):
            chunky.add_chunk_to_peer(peerId, filename, chunkId)
            return utils.create_peer_acquired_chunk_message(peerId, filename, chunkId)


        self.task_queue.put(apply_peer_acquired_chunk)