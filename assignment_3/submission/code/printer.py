from threading import Lock
from typing import List, Tuple


class TrackerPrinter(object):
    """Class for printing all Tracker messages to stdout using a mutex to avoid
        interrupted or corrupted message display."""

    def __init__(self):
        self.mutex = Lock()


    def print_new_peer(self, peer_id: int , files: List[Tuple[str, int] ]) -> None:
        """ Print statement for a new peer connecting to the tracker.

        Args:
            peer_id: The id of the peer
            files: A list of file tuples containing the name of the file and the
                number of chunks it has.
        """
        if self.mutex.acquire():
            print(f"PEER {peer_id} CONNECT: OFFERS {len(files)}")
            for f in files:
                filename, chunks = f
                print(f"{peer_id}    {filename} {chunks}")
        self.mutex.release()


    def print_peer_acquire_chunk(self, peer_id, chunk_id, num_chunks, filename) -> None:
        """ Print statment for a peer acquiring a new chunk.

        Args:
            peer_id: The id of the peer
            chunk_id: Id of the chunk within a file.
            num_chunks: The number of chunks a file has.
            filename: The name of the file.
        """
        if self.mutex.acquire():
            print(f"PEER {peer_id} ACQUIRED: {chunk_id}/{num_chunks} {filename}")
        self.mutex.release()

    def print_peer_disconnect(self, peer_id:int , filenames: List[str]) -> None:
        """ Print Statement for a peer disconnecting.

        Args:
            peer_id: The id of the peer that has disconnected.
            filenames: The files the peer has acquired.
        """
        if self.mutex.acquire():
            print(f"PEER {peer_id} DISCONNECT: RECEIVED {len(filenames)}")
            for f in filenames:
                print(f"{peer_id}    {f}")
        self.mutex.release()

class PeerPrinter(object):
    """Class for printing all Peer messages to stdout."""

    @staticmethod
    def print_peer_disconnect(peer_id: int, filenames: List[str]) -> None:
        """ Print Statement for a peer disconnecting.

        Args:
            peer_id: The id of the peer that has disconnected.
            filenames: The files the peer has acquired.
        """
        print(f"PEER {peer_id} DISCONNECT: RECEIVED {len(filenames)}")
        for f in filenames:
            print(f"{peer_id}    {f}")
