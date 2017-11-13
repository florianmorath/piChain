"""This module implements the networking between nodes.
"""

from twisted.internet.protocol import Factory, connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.internet import reactor, task
from twisted.internet.endpoints import connectProtocol
from twisted.python import log

import logging
import json
import argparse

logging.basicConfig(level=logging.DEBUG)

# TODO: put node_ids, ports and ips into config file
node_ids = ['a60c0bc6-b85a-47ad-abaa-a59e35822de2', 'b5564ec6-fd1d-481a-b68b-9b49a0ddd38b',
            'c1469026-d386-41ee-adc5-9fd7d0bf453e']
ports = [5999, 5998, 5997]


class Connection(LineReceiver):
    """This class keeps track of information about a connection with another node. It is a subclass of `LineReceiver`
    i.e each line that's received becomes a callback to the method `lineReceived`.

    note: We always serialize objects to a JSON formatted str and encode it as a bytes object with utf-8 encoding
        before sending it to the other side.

    Attributes:
        connection_manager (Factory): The factory that created the connection. It keeps a consistent state
            among connections.
        node_id (String): Unique predefined uuid of the node on this side of the connection.
        peer_node_id (String): Unique predefined uuid of the node on the other side of the connection.

    """

    def __init__(self, factory):
        self.connection_manager = factory
        self.node_id = self.connection_manager.node_id
        self.peer_node_id = None

    def connectionMade(self):
        logging.info('Connected to %s.', str(self.transport.getPeer()))

    def connectionLost(self, reason=connectionDone):
        logging.info('Lost connection to %s:%s', str(self.transport.getPeer()), reason.getErrorMessage())

        # remove peer_node_id from connection_manager.peers
        if self.peer_node_id is not None and self.peer_node_id in self.connection_manager.peers:
            self.connection_manager.peers.pop(self.peer_node_id)
            if not self.connection_manager.reconnect_loop.running:
                logging.info('Connection synchronization restart...')
                self.connection_manager.reconnect_loop.start(10)

    def lineReceived(self, line):
        """Callback that is called as soon as a line is available.

        Args:
            line (bytes): The line received. A bytes instance containing a JSON document.

        """
        msg = json.loads(line)  # deserialize the line to a python object
        msg_type = msg['msg_type']

        if msg_type == 'HEL':
            # handle handshake message
            peer_node_id = msg['nodeid']
            logging.info('Handshake from %s with peer_node_id = %s ', str(self.transport.getPeer()), peer_node_id)

            if peer_node_id not in self.connection_manager.peers:
                self.connection_manager.peers.update({peer_node_id: self})
                self.peer_node_id = peer_node_id

            # give peer chance to add connection
            self.send_hello_ack()

        elif msg_type == 'ACK':
            # handle handshake acknowledgement
            peer_node_id = msg['nodeid']
            logging.info('Handshake ACK from %s with peer_node_id = %s ', str(self.transport.getPeer()), peer_node_id)

            if peer_node_id not in self.connection_manager.peers:
                self.connection_manager.peers.update({peer_node_id: self})
                self.peer_node_id = peer_node_id

        else:
            self.connection_manager.message_callback(msg_type, msg, self)

    def send_hello(self):
        """ Send hello/handshake message s.t other node gets to know this node.

        """
        s = json.dumps({'msg_type': 'HEL', 'nodeid': self.node_id})  # Serialize obj to a JSON formatted str
        self.sendLine(s.encode())   # str.encode() returns encoded version of string as a bytes object (utf-8 encoding)

    def send_hello_ack(self):
        """ Send hello/handshake acknowledgement message s.t other node also has a chance to add connection.

        """
        s = json.dumps({'msg_type': 'ACK', 'nodeid': self.node_id})
        self.sendLine(s.encode())

    def rawDataReceived(self, data):
        pass


class ConnectionManager(Factory):
    """Keeps a consistent state among multiple `Connection` instances. Represents a node with a unique `node_id`.

    Attributes:
        peers (dict of String: Connection): The key represents the node_id and the value the Connection to the node
            with this node_id.
        node_id (String): unique identifier of this factory which represents a node.
        message_callback (Callable with signature (msg_type, data, sender: Connection)): Received lines are delegated
            to this callback if they are not handled inside Connection itself.

    """
    def __init__(self, node_id):
        self.peers = {}
        self.node_id = node_id
        self.message_callback = self.parse_msg

    def buildProtocol(self, addr):
        return Connection(self)

    def connect_to_nodes(self, node_index):
        """Connect to other peers if not yet connected to them. Ports, ips and node ids of them are all given/predefined.

        Args:
            node_index (int): index of this node into list of ports/ips and node_ids.

        """
        self.connections_report()

        activated = False
        for index in range(len(node_ids)):
            if node_ids[index] != node_ids[node_index] and node_ids[index] not in self.peers:
                activated = True
                point = TCP4ClientEndpoint(reactor, 'localhost', ports[index])
                d = connectProtocol(point, Connection(self))
                d.addCallback(got_protocol)
                d.addErrback(self.handle_connection_error, node_ids[index])

        if not activated:
            self.reconnect_loop.stop()
            logging.info('Connection synchronization finished: Connected to all peers')

    def connections_report(self):
        logging.info('"""""""""""""""""')
        logging.info('Connections: local node id = %s', self.node_id)
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

    def parse_msg(self, msg_type, msg, sender):
        logging.info('parse_msg called')
        if msg_type == 'RQB':
            self.receive_request_blocks_message(msg)
        elif msg_type == 'TXN':
            self.receive_transaction(msg)

    @staticmethod
    def handle_connection_error(failure, node_id):
        logging.info('Peer not online (%s): peer node id = %s ', str(failure.type), node_id)

    # all the methods which will be called from parse_msg according to msg_type
    def receive_request_blocks_message(self, req):
        raise NotImplementedError("To be implemented in subclass")

    def receive_transaction(self, txn):
        raise NotImplementedError("To be implemented in subclass")

# TODO: put following code into main.py


def got_protocol(p):
    """The callback to start the protocol exchange. We let connecting nodes start the hello handshake."""
    p.send_hello()


def main():
    """
    Entry point. First starts a server listening on a given port. Then connects to other peers. Also starts the reactor.

    """
    parser = argparse.ArgumentParser()

    # start server
    parser.add_argument("node_index")
    args = parser.parse_args()
    node_index = int(args.node_index)

    cm = ConnectionManager(node_ids[node_index])

    endpoint = TCP4ServerEndpoint(reactor, ports[node_index])
    endpoint.listen(cm)

    # "client part" -> connect to all servers -> add handshake callback
    cm.reconnect_loop = task.LoopingCall(cm.connect_to_nodes, node_index)
    logging.info('Connection synchronization start...')
    deferred = cm.reconnect_loop.start(10, True)
    deferred.addErrback(log.err)

    # start reactor
    logging.info('start reactor')
    reactor.run()


if __name__ == "__main__":
    main()
