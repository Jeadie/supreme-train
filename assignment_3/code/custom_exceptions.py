class PortBindingException(Exception):
    """ This exception is raised when a TCP port cannot be bound to after sufficient attempts.

    Sufficient attempts is defined by constants.TRACKER_PORT_CONNECT_ATTEMPTS
    """
    pass


class UnexpectedMessageReceivedException(Exception):
    """ This exception is raised when a message was received that was not of the
    expected format or type (type referring to an unexpected MessageCode)

    """
    pass
