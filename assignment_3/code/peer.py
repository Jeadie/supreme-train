from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
import sys

import constants


class Peer(object):

    def __init__(self, tracker_addr, tracker_port, minimum_alive_time):
        """Constructor.

        Args:


        """
        self.tracker_addr = tracker_addr
        self.main_tracker_port = tracker_addr
        self.min_alive_time = minimum_alive_time

    def run(self) -> None:
        """ Runs the peer until it has acquired all files, is not exchanging chunks
            with any other peer and has waited an additional amount of time
            (min_alive_time).
        """

        ## Connect to Tracker

        ## Receive new port.

        ## Disconnect and create new TCP to tracker.

        ## Send addr & port for other peers to connect to you with

        ## Send filename and number of chunks

        ## Get all files, chunks from tracker

        ## Get list of (addr, port) for other peers.


def main():
    # Parse arguments
    parser = ArgumentParser(description='Peer')
    parser.add_argument("tracker_address", type=str, help="The address of the tracker to connect to.")
    parser.add_argument("tracker_port", type=int, help="The port of the tracker to connect to.")
    parser.add_argument("min_alive_time", type=int, help="The minimum time to stay alive after acquiring all files.")
    args = parser.parse_args()

    # Run Client
    peer = Peer(args.tracker_address, args.tracker_port, args.min_alive_time)
    peer.run()

if __name__ == "__main__":
    main()