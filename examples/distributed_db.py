"""This module implements a distributed database as an example usage of the pichain package.

note: don't forget to delete ~/.pichain directory before module is used.
"""

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet.protocol import connectionDone

from piChain.PaxosLogic import Node

import logging
import argparse
import os
import plyvel


class DatabaseProtocol(LineReceiver):

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.connections.update({self.transport.getPeer(): self})
        logging.debug('client connection made')

    def connectionLost(self, reason=connectionDone):
        self.factory.connections.pop(self.transport.getPeer())
        logging.debug('client connection lost')

    def lineReceived(self, line):
        txn_command = line.decode()
        logging.debug('received command from client: %s', txn_command)

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
    def __init__(self, node_index):
        self.connections = {}
        self.node = Node(node_index)

        self.node.tx_committed = self.tx_committed
        self.node.start_server()

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
        """Called once a block is committed.

        Args:
            commands (list): list of commands inside committed block (one per Transaction)

        """
        for command in commands:
            logging.debug('command committed: %s', command)

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
    parser.add_argument("node_index", help='Index of node in config.py')
    args = parser.parse_args()
    node_index = args.node_index

    # setup node instance
    db_factory = DatabaseFactory(int(node_index))

    # Any of the nodes may receive commands
    if node_index == '0':
        reactor.listenTCP(8000, db_factory)
    elif node_index == '1':
        reactor.listenTCP(8001, db_factory)
    elif node_index == '2':
        reactor.listenTCP(8002, db_factory)

    reactor.run()


if __name__ == "__main__":
    main()
