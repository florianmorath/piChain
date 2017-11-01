"""This module implements the networking between nodes.
"""

from twisted.internet.protocol import Factory
from twisted.protocols.basic import IntNStringReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

import logging
import struct

from uuid import uuid4

logging.basicConfig(level=logging.DEBUG)


class Connection(IntNStringReceiver):
    """This class keeps track of information about a connection with another node."""

    structFormat = '<I'
    prefixLength = struct.calcsize(structFormat)

    def __init__(self, factory):
        self.connection_manager = factory
        self.node_id = self.connection_manager.node_id
        self.peer_node_id = None

    def connectionMade(self):
        logging.info('Connection made')

    def connectionLost(self, reason):
        pass
        # TODO: remove peer_node_id from connection_manager.peers

    def stringReceived(self, string):
        pass
        # TODO: handshake_message: add self to connection_manager.peers if peer_node_id inside message not yet in peers
        self.connection_manager.message_callback()


class ConnectionManager(Factory):
    """ keeps consistent state among multiple Connection instances. Represents a node with a unique node_id. """

    def __init__(self):
        self.peers = {}  # dict: node_id -> Connection
        self.node_id = self.generate_node_id()
        self.message_callback = self.parse_msg  # Callable with arguments (msg_type, data, sender: Connection)

    def buildProtocol(self, addr):
        return Connection(self)

    def broadcast(self, obj):
        """
        `obj` will be broadcast to all the peers.

        Args:
            obj: an instance of type Message, Block or Transaction

        """
        logging.debug('broadcast')
        # TODO: go over all connections in self.peers and call sendString on them

    def respond(self, obj, sender):
        """
        `obj` will be responded to to the peer which has send the request.

        Args:
            obj: an instance of type Message, Block or Transaction

        """
        logging.info('respond')
        # TODO: use the sender argument of message_callback

    def parse_msg(self, msg_type, data, sender):
        logging.info('parse_msg called')

    @staticmethod
    def generate_node_id():
        return str(uuid4())


def main():
    # start server
    endpoint = TCP4ServerEndpoint(reactor, 5999)
    endpoint.listen(ConnectionManager())

    # "client part" -> connect to all servers given in config file -> add handshake callback

    # start reactor
    logging.info('start reactor')
    reactor.run()


if __name__ == "__main__":
    main()