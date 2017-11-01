"""This module implements the networking between nodes.
"""

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.internet import reactor
from twisted.internet.endpoints import connectProtocol

import logging
import struct
import json

from uuid import uuid4

logging.basicConfig(level=logging.DEBUG)


class Connection(LineReceiver):
    """This class keeps track of information about a connection with another node."""

    structFormat = '<I'
    prefixLength = struct.calcsize(structFormat)

    def __init__(self, factory):
        self.connection_manager = factory
        self.node_id = self.connection_manager.node_id
        self.peer_node_id = None

    def connectionMade(self):
        logging.info('Connected to %s.', str(self.transport.getPeer()))

    def connectionLost(self, reason):
        logging.info('Lost connection to %s:%s', str(self.transport.getPeer()), reason)
        # remove peer_node_id from connection_manager.peers
        if self.peer_node_id is not None and self.peer_node_id in self.connection_manager.peers:
            self.connection_manager.peers.pop(self.peer_node_id)

        self.connection_manager.connections_report()

    def lineReceived(self, line):
        logging.info('lineReceived called')
        msg = json.loads(line)
        msg_type = msg['msg_type']

        if msg_type == 'HEL':
            # handshake_message: add self to connection_manager.peers if peer_node_id inside message not yet in peers
            peer_node_id = msg['nodeid']
            logging.info('Handshake from %s with peer_node_id = %s ', str(self.transport.getPeer()), peer_node_id)

            if peer_node_id == self.node_id:
                logging.info('Connected to myself')
                self.transport.loseConnection()
            if peer_node_id not in self.connection_manager.peers:
                self.connection_manager.peers.update({peer_node_id: self})
                self.peer_node_id = peer_node_id
            else:
                # already connected to that peer
                self.transport.loseConnection()
                
            self.connection_manager.connections_report()

        else:
            self.connection_manager.message_callback(msg_type, line, self)

    def send_hello(self):
        logging.info('send_hello called')
        s = json.dumps({'msg_type': 'HEL', 'nodeid': self.node_id})
        self.sendLine(s.encode())


class ConnectionManager(Factory):
    """ keeps consistent state among multiple Connection instances. Represents a node with a unique node_id. """

    def __init__(self):
        self.peers = {}  # dict: node_id -> Connection
        self.node_id = self.generate_node_id()
        self.message_callback = self.parse_msg  # Callable with arguments (msg_type, data, sender: Connection)

    def buildProtocol(self, addr):
        return Connection(self)

    def connections_report(self):
        logging.info('"""""""""""""""""')
        for key, value in self.peers.items():
            logging.info('Connection from %s to %s.', value.transport.getHost(), value.transport.getPeer())
        logging.info('"""""""""""""""""')

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


def got_protocol(p):
    """The callback to start the protocol exchange. We let connecting
    nodes start the hello handshake"""
    p.send_hello()


def main():
    # start server
    endpoint = TCP4ServerEndpoint(reactor, 5999)
    cm1 = ConnectionManager()
    endpoint.listen(cm1)

    # "client part" -> connect to all servers given in config file -> add handshake callback
    point = TCP4ClientEndpoint(reactor, "localhost", 5999)
    cm2 = ConnectionManager()
    d = connectProtocol(point, Connection(cm2))
    d.addCallback(got_protocol)

    point = TCP4ClientEndpoint(reactor, "localhost", 5999)
    cm3 = ConnectionManager()
    d = connectProtocol(point, Connection(cm3))
    d.addCallback(got_protocol)

    # start reactor
    logging.info('start reactor')
    reactor.run()





if __name__ == "__main__":
    main()