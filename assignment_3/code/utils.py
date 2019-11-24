import json
import random
from socket import socket, AF_INET, SOCK_STREAM, error as socket_error
from typing import Tuple, Dict, List

import constants
from constants import MessageCode
from custom_exceptions import PortBindingException, UnexpectedMessageReceivedException


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
            s.settimeout(constants.TCP_TIMEOUT_DURATION)
            return (s, port)

        except socket_error:
            continue

    raise PortBindingException()

# TODO: add message code checking on parsing functions with custom erroring.

def parse_peer_message(msg: bytes) -> Tuple[bool, int]:
    """

    Args:
        message: A message received by the tracker from a peer.

    Returns:
        A tuple containing:
            * whether the peer is indicating it is done.
            * The chunk it has acquired (-1 if the message is a disconnection message)
    Raises:
        UnexpectedMessageReceivedException: If the message
    """
    message_type, chunk = msg.decode().split(constants.MESSAGE_SEPARATOR, 1)
    message_type = int(message_type)

    if message_type == MessageCode.PEER_DISCONNECT.value:
        return True, -1
    elif message_type == MessageCode.PEER_ACQUIRED_CHUNK.value:
        return False, int(chunk)
    else:
        raise UnexpectedMessageReceivedException(
            f"Message was neither a {MessageCode.PEER_DISCONNECT} or "
            f"{MessageCode.PEER_ACQUIRED_CHUNK}. Message had code: {message_type}."
        )

def create_peer_disconnect_message(peerId) -> bytes:
    """ Creates a message stating a certain peer has disconnected.

    Args:
        peerId: The peer whom has disconnected.

    Returns:
        A formatted message.
    """
    return f"{MessageCode.PEER_DISCONNECT.value} {peerId}".encode()

def parse_peer_disconnect_message(msg: bytes) -> int:
    """ Parses a peer disconnection message.

    The message is assumed to be a valid disconnect message.

    Args:
        msg: A message received by a peer.

    Returns:
         The id of the peer that has disconnected.
    """
    # TODO: custom error message.
    return msg.decode().split(constants.MESSAGE_SEPARATOR, 1)[-1]


def create_peer_acquired_chunk_message(peerId: int, filename: str, chunk: int) -> bytes:
    """ Creates a message stating a certain peer has acquired a chunk.

    Args:
        peerId: The Id of the peer.
        filename: The file corresponding file that has been acquired.
        chunk: The Id of the chunk in the filename that has been acquired.

    Returns:
        A formatted message.
    """
    return f"{MessageCode.PEER_ACQUIRED_CHUNK.value} {peerId} {filename} {chunk}".encode()


def parse_peer_acquired_chunk_message(msg: bytes) -> Tuple[int, str, int]:
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
    Id, filename, chunkId = msg.decode().split(constants.MESSAGE_SEPARATOR)[1:]
    return int(Id), filename, int(chunkId)

def create_new_file_message(peerId: int, files: List[Tuple[str, int]]) -> bytes:
    """ Creates a message stating there are new files in the system.

    Args:
        peerId: The Id of the peer with the file.
        files: A list of (filename, number of chunks) tuples


    Returns:
        A formatted message.
    """
    return f"{MessageCode.NEW_FILES_IN_SYSTEM.value} {peerId} {json.dumps(files)}".encode()


def parse_new_file_message(msg: bytes) -> Tuple[int, List[Tuple[str, int]]]:
    """ Parses a new file message.

    The message is assumed to be a valid.

    Args:
        msg: A message received by a peer.

    Returns:
        A tuple consisting of:
            * The Id of the peer with the file (must exist or file not in system)
            * A list of (filename, number of chunks) tuples
    """
    code, Id, files= msg.decode().split(constants.MESSAGE_SEPARATOR, 2)
    return int(Id), json.loads(files)

def create_file_chunk_message(filename: str, chunkId: int, chunk_data: str) -> bytes:
    """ Creates a message for sending file chunk data.

    Args:
        filename: The name of the file the chunk is from.
        chunkId: The id of the chunk.
        chunk_data: The raw data of the chunk from the specified file.

    Returns:
        A formatted message.
    """
    return f"{MessageCode.FILE_CHUNK.value} {filename} {chunkId} {chunk_data}".encode()

def parse_file_chunk_message(msg: bytes) -> Tuple[str, int, str]:
    """ Parses a file chunk message.

    Args:
        msg: A message received by a peer.

    Returns:
        A Tuple consisting of:
            * The filename the chunk belongs to.
            * The id of the file chunk
            * The raw chunk data itself.
    """
    filename, chunk_Id, data = msg.decode().split(constants.MESSAGE_SEPARATOR, 2)
    return filename, int(chunk_Id), data

def create_new_peer_message(addr: str, port: int) -> bytes:
    """ Creates a message for stating there is a new peer in the network.

    Args:
        addr: The IP address the peer is on.
        port: The port to connect with the peer via.

    Returns:
        A formatted message.
    """
    return f"{MessageCode.NEW_PEER_CONNECTION.value} {addr} {port}".encode()

def parse_new_peer_message(message: bytes) -> Tuple[str, int]:
    """ Parses a peer-tracker connection message.

    Args:
        msg: A message received by a peer.
    Returns:
        A Tuple consisting of:
            * The IP address of the new peer.
            * The port to contact the peer on.
    """
    addr, port = message.decode().split(constants.MESSAGE_SEPARATOR)[1:]
    return addr, int(port)


def create_chunk_list_message(chunk_data: Dict[str, Dict[int, List[int]]]) -> bytes:
    """ Creates a message that contains all the details of chunk data in the network.

    Args:
        chunk_data: Map from Files -> (Map from Chunks -> List[peer ID's with specific chunk from file]
        See files property of Chunky in chunky.py
    Returns:
        A formatted message.
    """
    return f"{MessageCode.CHUNK_LIST.value} {json.dumps(chunk_data)}".encode()


def parse_chunk_list_message(message: bytes) -> Dict[str, Dict[int, List[int]]]:
    """ Parses a message containing all the (addr, port) of the peers.

    Args:
        message: A message received by a peer.

    Returns:
        Map from Files -> (Map from Chunks -> List[peer ID's with specific chunk from file]
        See files property of Chunky in chunky.py
    """
    code, obj = message.decode().split(constants.MESSAGE_SEPARATOR, 1)
    return json.loads(obj)


def create_peer_list_message(peers: Dict[int, Tuple[str, int]]) -> bytes:
    """ Creates a message containing the port and addr to contact other peers via.

    Args:
        peers: A mapping from peer Ids to addr and port number.

    Returns:
        A formattted message.
    """
    return f"{MessageCode.PEER_LIST.value} {json.dumps(peers)}".encode()

def parse_peer_list_message(message: bytes) -> Dict[int, Tuple[str, int]]:
    """ Parses a message containing the connection information for all peers.

    Args:
        message: A message received from a tracker.

    Returns:
        A mapping from peer Ids to addr and port number.
    """
    code, obj = message.decode().split(constants.MESSAGE_SEPARATOR, 1)
    return json.loads(obj)
