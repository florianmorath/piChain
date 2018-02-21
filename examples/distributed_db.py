"""This module implements a distributed database as an example usage of the piChain package. It's a key-value storage
that can handle keys and values that are arbitrary byte arrays. Supported operations are put(key,value), get(key) and
delete(key).

note: If you want to delete the local database and the internal datastructure piChain uses delete the ~/.pichain
directory.
"""

import logging
import argparse
import os

import plyvel
from twisted.internet.protocol import Factory, connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

from piChain import Node

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DatabaseProtocol(LineReceiver):
    """Object representing a connection with another node."""

    def __init__(self, factory):
        """
        Args:
            factory (DatabaseFactory): Twisted Factory used to keep a shared state among multiple connections.
        """
        self.factory = factory

    def connectionMade(self):
        self.factory.connections.update({self.transport.getPeer(): self})
        logger.debug('client connection made')

    def connectionLost(self, reason=connectionDone):
        self.factory.connections.pop(self.transport.getPeer())
        logger.debug('client connection lost')

    def lineReceived(self, line):
        """ The `line` represents the database operation send by a client. Put and delete operations have to be
        committed first by calling `make_txn(operation)` on the node instance stored in the factory. Get operations
        can be directly executed locally.

        Args:
            line (bytes): received command str encoded in bytes.
        """
        txn_command = line.decode()
        logger.debug('received command from client: %s', txn_command)

        c_list = txn_command.split()
        if c_list[0] == 'put' or c_list[0] == 'delete':
            self.factory.node.make_txn(txn_command)

        elif c_list[0] == 'get':
            # get command is directly locally executed and will not be committed
            key = c_list[1]
            value = self.factory.db.get(key.encode())
            if value is None:
                message = 'key "%s" does not exist' % key
                self.sendLine(message.encode())
            else:
                self.sendLine(value)

    def rawDataReceived(self, data):
        pass


class DatabaseFactory(Factory):
    """Object managing all connections. This is a twisted Factory used to listen for incoming connections. It keeps a
    Node instance `self.node` as a shared object among multiple connections.

    Attributes:
        connections (dict): Maps an IAddress (representing an address of a remote peer) to a DatabaseProtocol instance
            (representing the connection between the local node and the peer).
        node (Node): A Node instance representing the local node.
        db (pyvel db): A plyvel db instance used to store the key-value pairs (python implementation of levelDB).
    """
    def __init__(self, node_index, c_size):
        """Setup of a Node instance: A peers dictionary containing an (ip,port) pair for each node must be defined. The
        `node_index` argument defines the node that will run locally. The `tx_committed` field of the Node instance is a
        callable that is called once a block has been committed. By calling `start_server()` on the Node instance the
        local node will try to connect to its peers.

        Args:
            node_index (int):  Index of node in the given peers dict.
            c_size (int): Cluster size.
        """
        self.connections = {}
        peers = {}
        for i in range(0, c_size):
            peers.update({str(i): {'ip': 'localhost', 'port': (7000 + i)}})

        self.node = Node(node_index, peers)

        self.node.tx_committed = self.tx_committed

        # create a db instance
        base_path = os.path.expanduser('~/.pichain/distributed_DB')
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        path = base_path + '/node_' + str(node_index)
        self.db = plyvel.DB(path, create_if_missing=True)

    def buildProtocol(self, addr):
        return DatabaseProtocol(self)

    def broadcast(self, line):
        for con in self.connections.values():
            con.sendLine(line.encode())

    def tx_committed(self, commands):
        """Called once a transaction has been committed. Since the delete and put operations have now been committed,
        they can be executed locally.

        Args:
            commands (list): list of commands inside committed block (one per Transaction)

        """
        for command in commands:
            c_list = command.split()
            if c_list[0] == 'put':
                key = c_list[1]
                value = c_list[2]
                self.db.put(key.encode(), value.encode())
                message = 'stored key-value pair = ' + key + ': ' + value
                self.broadcast(message)
            elif c_list[0] == 'delete':
                key = c_list[1]
                self.db.delete(key.encode())
                message = 'deleted key = ' + key
                self.broadcast(message)


def main():
    # get node index as an argument
    parser = argparse.ArgumentParser()
    parser.add_argument("node_index", help='Index of node in the given peers dict.')
    parser.add_argument("clustersize")
    args = parser.parse_args()
    node_index = args.node_index
    cluster_size = args.clustersize
    # setup node instance
    db_factory = DatabaseFactory(int(node_index), int(cluster_size))

    # Any of the nodes may receive commands
    if node_index == '0':
        reactor.listenTCP(8000, db_factory)
    elif node_index == '1':
        reactor.listenTCP(8001, db_factory)
    elif node_index == '2':
        reactor.listenTCP(8002, db_factory)

    db_factory.node.start_server()


if __name__ == "__main__":
    main()
