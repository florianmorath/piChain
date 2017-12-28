"""This module implements the networking between nodes.
"""

from twisted.internet.protocol import Factory, connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint
from twisted.internet import reactor, task
from twisted.internet.endpoints import connectProtocol
from twisted.internet.task import LoopingCall
from twisted.python import log

from piChain.messages import RequestBlockMessage, Transaction, Block, RespondBlockMessage, PaxosMessage, PingMessage, \
    PongMessage, AckCommitMessage
from piChain.config import peers

import logging
import json
import time
import sys


logging.basicConfig(level=logging.DEBUG)


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
        self.lc_ping = LoopingCall(self.send_ping)

        # init max message size to 5 Megabyte
        self.MAX_LENGTH = 5000000

    def connectionMade(self):
        logging.info('Connected to %s.', str(self.transport.getPeer()))

    def connectionLost(self, reason=connectionDone):
        logging.info('Lost connection to %s with id %s: %s',
                     str(self.transport.getPeer()), self.peer_node_id, reason.getErrorMessage())

        # remove peer_node_id from connection_manager.peers
        if self.peer_node_id is not None and self.peer_node_id in self.connection_manager.peers:
            self.connection_manager.peers.pop(self.peer_node_id)
            if not self.connection_manager.reconnect_loop.running:
                logging.info('Connection synchronization restart...')
                self.connection_manager.reconnect_loop.start(10)

        # stop the ping loop
        if self.lc_ping.running:
            self.lc_ping.stop()

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

                # start ping loop
                if not self.lc_ping.running:
                    self.lc_ping.start(20, now=True)

            # give peer chance to add connection
            self.send_hello_ack()

        elif msg_type == 'ACK':
            # handle handshake acknowledgement
            peer_node_id = msg['nodeid']
            logging.info('Handshake ACK from %s with peer_node_id = %s ', str(self.transport.getPeer()), peer_node_id)

            if peer_node_id not in self.connection_manager.peers:
                self.connection_manager.peers.update({peer_node_id: self})
                self.peer_node_id = peer_node_id

                # start ping loop
                if not self.lc_ping.running:
                    self.lc_ping.start(20, now=True)

        elif msg_type == 'PIN':
            obj = PingMessage.unserialize(msg)
            pong = PongMessage(obj.time)
            data = pong.serialize()
            self.sendLine(data)

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

    def send_ping(self):
        """Send ping message to estimate RTT.

        """
        ping = PingMessage(time.time())
        data = ping.serialize()
        self.sendLine(data)

    def rawDataReceived(self, data):
        pass


class ConnectionManager(Factory):
    """Keeps a consistent state among multiple `Connection` instances. Represents a node with a unique `node_id`.

    Attributes:
        peers (dict of String: Connection): The key represents the node_id and the value the Connection to the node
            with this node_id.
        node_id (String): unique identifier of this factory which represents a node (uuid).
        message_callback (Callable with signature (msg_type, data, sender: Connection)): Received lines are delegated
            to this callback if they are not handled inside Connection itself.
        id (int): index of this node into list of peers in config.py.

    """
    def __init__(self, index):
        self.peers = {}
        self.node_id = peers.get(str(index)).get('uuid')
        self.message_callback = self.parse_msg
        self.id = index
        self.reconnect_loop = None

    def buildProtocol(self, addr):
        return Connection(self)

    @staticmethod
    def got_protocol(p):
        """The callback to start the protocol exchange. We let connecting nodes start the hello handshake."""
        p.send_hello()

    def connect_to_nodes(self, node_index):
        """Connect to other peers if not yet connected to them. Ports, ips and node ids of them are all given/predefined.

        Args:
            node_index (str): index of this node into list of peers in config.py.

        """
        self.connections_report()

        activated = False
        for index in range(len(peers)):
            if peers.get(str(index)).get('uuid') != peers.get(node_index).get('uuid') and \
                            peers.get(str(index)).get('uuid') not in self.peers:
                activated = True
                point = TCP4ClientEndpoint(reactor, peers.get(str(index)).get('ip'), peers.get(str(index)).get('port'))
                d = connectProtocol(point, Connection(self))
                d.addCallback(self.got_protocol)
                d.addErrback(self.handle_connection_error, peers.get(str(index)).get('uuid'))

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

    def broadcast(self, obj, msg_type):
        """
        `obj` will be broadcast to all the peers.

        Args:
            obj: an instance of type Message, Block or Transaction
            msg_type (str): 3 char description of message type

        """
        logging.debug('broadcast: %s', msg_type)
        logging.debug('size = %s', str(sys.getsizeof(obj.serialize())))
        # go over all connections in self.peers and call sendLine on them
        for k, v in self.peers.items():
            data = obj.serialize()
            v.sendLine(data)

        # if obj is a Transaction then the node also has to send it to itself
        if msg_type == 'TXN':
            self.receive_transaction(obj)

        # if obj is a AckCommitMessage then the node also has to send it to itself
        if msg_type == 'ACM':
            self.receive_ack_commit_message(obj)

        # if obj is a PaxosMessage then the node also has to send it to itself
        if msg_type == 'TRY' or msg_type == 'PROPOSE' or msg_type == 'COMMIT':
            self.receive_paxos_message(obj, None)

    @staticmethod
    def respond(obj, sender):
        """
        `obj` will be responded to to the peer which has send the request.

        Args:
            obj: an instance of type Message, Block or Transaction.
            sender (Connection): The connection between this node and the sender of the message.
        """
        logging.info('respond')
        data = obj.serialize()
        logging.debug('size = %s', str(sys.getsizeof(data)))
        sender.sendLine(data)

    def parse_msg(self, msg_type, msg, sender):
        if msg_type != 'PON':
            logging.info('parse_msg called with msg_type = %s', msg_type)
        if msg_type == 'RQB':
            obj = RequestBlockMessage.unserialize(msg)
            self.receive_request_blocks_message(obj, sender)
        elif msg_type == 'TXN':
            obj = Transaction.unserialize(msg)
            self.receive_transaction(obj)
        elif msg_type == 'BLK':
            obj = Block.unserialize(msg)
            self.receive_block(obj)
        elif msg_type == 'RSB':
            obj = RespondBlockMessage.unserialize(msg)
            self.receive_respond_blocks_message(obj)
        elif msg_type == 'PAM':
            obj = PaxosMessage.unserialize(msg)
            self.receive_paxos_message(obj, sender)
        elif msg_type == 'PON':
            obj = PongMessage.unserialize(msg)
            self.receive_pong_message(obj, sender.peer_node_id)
        elif msg_type == 'ACM':
            obj = AckCommitMessage.unserialize(msg)
            self.receive_ack_commit_message(obj)

    @staticmethod
    def handle_connection_error(failure, node_id):
        logging.info('Peer not online (%s): peer node id = %s ', str(failure.type), node_id)

    # all the methods which will be called from parse_msg according to msg_type
    def receive_request_blocks_message(self, req, sender):
        raise NotImplementedError("To be implemented in subclass")

    def receive_transaction(self, txn):
        raise NotImplementedError("To be implemented in subclass")

    def receive_block(self, block):
        raise NotImplementedError("To be implemented in subclass")

    def receive_respond_blocks_message(self, resp):
        raise NotImplementedError("To be implemented in subclass")

    def receive_paxos_message(self, message, sender):
        raise NotImplementedError("To be implemented in subclass")

    def receive_pong_message(self, message, peer_node_id):
        raise NotImplementedError("To be implemented in subclass")

    def receive_ack_commit_message(self, message):
        raise NotImplementedError("To be implemented in subclass")

    # methods used by the app

    def start_server(self):
        """First starts a server listening on a port given in confg file. Then connect to other peers.

        """

        endpoint = TCP4ServerEndpoint(reactor, peers.get(str(self.id)).get('port'))
        d = endpoint.listen(self)
        d.addErrback(log.err)

        # "client part" -> connect to all servers -> add handshake callback
        self.reconnect_loop = task.LoopingCall(self.connect_to_nodes, str(self.id))
        logging.info('Connection synchronization start...')
        deferred = self.reconnect_loop.start(0.1, True)
        deferred.addErrback(log.err)
