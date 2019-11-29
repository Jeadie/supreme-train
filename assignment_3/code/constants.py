from enum import Enum


FOREVER=True
TRACKER_PORT_CONNECT_ATTEMPTS = 12
MIN_PORT_NUMBER = 20000
MAX_PORT_NUMBER = 60000
MESSAGE_SEPARATOR = " "
PEER_FILE_DIRECTORY = "Shared/"
TCP_TIMEOUT_DURATION = 10
TCP_PEER_TIMEOUT_DURATION = 2
TRACKER_PORT_FILENAME = "port.txt"
MAX_QUEUED_CONNECTIONS = 2
MAX_BUFFER_SIZE  =2048
CHUNK_SIZE = 512
TRACKER_OUTPUT_LOGGING_LEVEL = 100

class MessageCode(Enum):
    PEER_DISCONNECT = 1
    PEER_ACQUIRED_FILE = 2
    NEW_FILES_IN_SYSTEM = 3
    FILE_CHUNK = 4
    NEW_PEER_CONNECTION = 5
    CHUNK_LIST = 6
    PEER_LIST = 7
    CHUNK_REQUEST = 8
    PEER_ACQUIRED_CHUNK = 9