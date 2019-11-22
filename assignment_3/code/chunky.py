from typing import List, Dict

class Chunky(object):
    """ Data Structure to manage chunks."""
    def __init__(self):
        """ Constructor.

        """
        # Map from Files -> (Map from Chunks -> List[peer ID's with specific chunk from file]
        # {
        #     "file1": {
        #         1: [1, 2, 5],  # User 1,2,5 have Chunk 1
        #         2: [1],  # User 1 has Chunk 2
        #         ...
        #     },
        #     "file2": {
        #         ...
        #     },
        #     ...
        # }
        self.files = Dict[str, Dict[int, List[int]]]
        self.peers = 0

    def add_chunk_to_peer(self, peerId: int, filename: str, chunkId: int) -> None:
        """ Assigns that a peer has a certain chunk from a file.

        Args:
            peerId: The Id of the peer.
            filename: The file corresponding file that has been acquired.
            chunkId: The Id of the chunk in the filename that has been acquired.
        """
        self.files[filename][chunkId].append(peerId)

    def remove_peer(self, peerId: int) -> None:
        """ Removes a peer from Chunky.

        Args:
            peerId: The peer to remove from Chunky.
        """
        for chunks in self.files.values():
            for chunk in chunks.values():
                if peerId in chunk:
                    chunk.remove(peerId)


    def add_file(self, peerId: int, filename: str, chunks: int) -> None:
        """ Adds a new file to chunky.

        It is assumed filename conflicts will not occur.

        Args:
            peerId: The Id of the peer with the file.
            filename: The name of the file.
            chunks: The number of chunks the file has.
        """
        self.files[filename] = dict([(i, peerId) for i in range(chunks)])

