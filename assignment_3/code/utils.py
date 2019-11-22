import random
from socket import socket, AF_INET, SOCK_STREAM, error as socket_error
from typing import Tuple

import constants
from constants import MessageCode
from custom_exceptions import PortBindingException


def bind_TCP_port(addr: str) -> Tuple[socket, int]:
    """ Attempts to bind to an arbitrary port on the given address.


    Args:

        addr: The IP address to bind with.

    Returns:
         A tuple consisting of:
            * A socket configured for TCP traffic to a random port number.
            * The port number the socket is connected to.

    Raises:
        PortBindingException: If a port could not be binded to after sufficient
            attempts.
    """
    s = socket(AF_INET, SOCK_STREAM)
    for i in range(constants.TRACKER_PORT_CONNECT_ATTEMPTS):
        try:
            port = random.randint(constants.MIN_PORT_NUMBER,
                                  constants.MAX_PORT_NUMBER)
            s.bind((addr, port))
            return (s, port)

            # TODO: fix this code smell (i.e. find actual exceptions)
        except socket_error:
            continue

    raise PortBindingException()

def create_peer_disconnect_message(peerId) -> str:
    """ Creates a message stating a certain peer has disconnected.

    Args:
        peerId: The peer whom has disconnected.

    Returns:
        A formatted message.
    """
    return f"{MessageCode.PEER_DISCONNECT.value} {peerId}"

def parse_peer_disconnect_message(msg) -> int:
    """ Parses a peer disconnection message.

    The message is assumed to be a valid disconnect message.

    Args:
        msg: A message received by a peer.

    Returns:
         The id of the peer that has disconnected.
    """
    # TODO: custom error message.
    return msg.split(constants.MESSAGE_SEPARATOR, 1)[-1]


def create_peer_acquired_chunk_message(peerId: int, filename: str, chunk: int) -> str:
    """ Creates a message stating a certain peer has acquired a chunk.

    Args:
        peerId: The Id of the peer.
        filename: The file corresponding file that has been acquired.
        chunk: The Id of the chunk in the filename that has been acquired.

    Returns:
        A formatted message.
    """
    return f"{MessageCode.PEER_ACQUIRED_CHUNK.value} {peerId} {filename} {chunk}"


def parse_peer_acquired_chunk_message(msg: str) -> Tuple[int, str, int]:
    """ Parses a peer acquire chunk message.

    The message is assumed to be a valid.

    Args:
        msg: A message received by a peer.

    Returns:
        A tuple consisting of:
            * The Id of the peer
            * The filename
            * The Chunk in the file that the peer has acquired.
    """
    Id, filename, chunkId = msg.split(constants.MESSAGE_SEPARATOR)[1:]
    return int(Id), filename, int(chunkId)

def create_new_file_message(peerId: int, filename: str, chunks: int) -> str:
    """ Creates a message stating there is a new file in the system.

    Args:
        peerId: The Id of the peer with the file.
        filename: The name of the file.
        chunks: The number of chunks the file has.

    Returns:
        A formatted message.
    """
    return f"{MessageCode.NEW_FILE_IN_SYSTEM.value} {peerId} {filename} {chunks}"


def parse_new_file_message(msg: str) -> Tuple[int, str, int]:
    """ Parses a new file message.

    The message is assumed to be a valid.

    Args:
        msg: A message received by a peer.

    Returns:
        A tuple consisting of:
            * The Id of the peer with the file (must exist or file not in system)
            * The filename
            * The number of chunks the file has.
    """
    Id, filename, no_chunks = msg.split(constants.MESSAGE_SEPARATOR)[1:]
    return int(Id), filename, int(no_chunks)

def create_file_chunk_message(filename: str, chunkId: int, chunk_data: str) -> str:
    """ Creates a message for sending file chunk data.

    Args:
        filename: The name of the file the chunk is from.
        chunkId: The id of the chunk.
        chunk_data: The raw data of the chunk from the specified file.

    Returns:
        A formatted message.
    """
    return f"{MessageCode.FILE_CHUNK.value} {filename} {chunkId} {chunk_data}"

def parse_file_chunk_message(msg: str) -> Tuple[str, int, str]:
    """ Parses a file chunk message.

    Args:
        msg: A message received by a peer.

    Returns:
        A Tuple consisting of:
            * The filename the chunk belongs to.
            * The id of the file chunk
            * The raw chunk data itself.
    """
    filename, chunk_Id, data = msg.split(constants.MESSAGE_SEPARATOR, 2)
    return filename, int(chunk_Id), data
