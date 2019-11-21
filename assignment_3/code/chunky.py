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
        

