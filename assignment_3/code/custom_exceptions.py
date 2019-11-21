
class PortBindingException(Exception):
    """ This exception is raised when a TCP port cannot be bound to after sufficient attmempts.

    Sufficient attempts is defined by constants.TRACKER_PORT_CONNECT_ATTEMPTS
    """
    pass
