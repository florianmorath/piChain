"""This module implements the networking between nodes.
"""

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.internet import reactor, task
from twisted.internet.endpoints import connectProtocol

import logging
import json

import argparse

from uuid import uuid4

logging.basicConfig(level=logging.DEBUG)


class Connection(LineReceiver):
    """This class keeps track of information about a connection with another node."""

    def __init__(self, factory):
        self.connection_manager = factory
        self.node_id = self.connection_manager.node_id
        self.peer_node_id = None

    def connectionMade(self):
        logging.info('Connected to %s.', str(self.transport.getPeer()))
        pass

    def connectionLost(self, reason):
        logging.info('Lost connection to %s:%s', str(self.transport.getPeer()), reason)

        # remove peer_node_id from connection_manager.peers
        if self.peer_node_id is not None and self.peer_node_id in self.connection_manager.peers:
            self.connection_manager.peers.pop(self.peer_node_id)

    def lineReceived(self, line):
        msg = json.loads(line)
        msg_type = msg['msg_type']

        if msg_type == 'HEL':
            # handshake_message: add self to connection_manager.peers if peer_node_id inside message not yet in peers
            peer_node_id = msg['nodeid']
            logging.info('Handshake from %s with peer_node_id = %s ', str(self.transport.getPeer()), peer_node_id)

            if self.peer_node_id is not None:
                # ignore message because we already did a handshake
                return
            if peer_node_id not in self.connection_manager.peers:
                self.connection_manager.peers.update({peer_node_id: self})
                self.peer_node_id = peer_node_id
            else:
                self.transport.loseConnection()

        else:
            self.connection_manager.message_callback(msg_type, line, self)

    def send_hello(self):
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
        logging.info('Connections: ')
        for key, value in self.peers.items():
            logging.info('Connection from %s (%s) to %s (%s).',
                         value.transport.getHost(), self.node_id, value.transport.getPeer(), value.peer_node_id)
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


ports = [5999, 5998, 5997]
cm = ConnectionManager()


def got_protocol(p):
    """The callback to start the protocol exchange. We let connecting
    nodes start the hello handshake"""
    p.send_hello()


def connect_to_nodes(server_port):

    for port in ports:
        if port != server_port:
            point = TCP4ClientEndpoint(reactor, 'localhost', port)
            d = connectProtocol(point, Connection(cm))
            d.addCallback(got_protocol)

    cm.connections_report()


def _show_error(failure):
    logging.debug('An error occured: %s', str(failure))


def main():
    parser = argparse.ArgumentParser()

    # start server
    parser.add_argument("server_port")
    args = parser.parse_args()

    server_port = int(args.server_port)
    endpoint = TCP4ServerEndpoint(reactor, server_port)

    endpoint.listen(cm)

    # "client part" -> connect to all servers -> add handshake callback
    reconnect_loop = task.LoopingCall(connect_to_nodes, server_port)
    deferred = reconnect_loop.start(20, False)
    deferred.addErrback(_show_error)

    # start reactor
    logging.info('start reactor')
    reactor.run()


if __name__ == "__main__":
    main()