from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

from piChain.PaxosLogic import Node

import logging
import argparse
import os
import shutil
import plyvel
import jsonpickle


class DatabaseProtocol(LineReceiver):

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.connections.update({self.transport.getPeer(): self})

    def connectionLost(self, reason):
        self.factory.connections.pop(self.transport.getPeer())

    def lineReceived(self, line):
        command_str = line.decode()
        peer_str = jsonpickle.encode(self.transport.getPeer())
        logging.debug(peer_str)
        txn_command = command_str + ' ' + peer_str
        logging.debug(txn_command)
        self.factory.node.make_txn(txn_command)

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
            elif c_list[0] == 'get':
                key = c_list[1]
                value = self.db.get(key.encode())

                peer_cmd_list = c_list[2:]
                peer_cmd = ''
                for l in peer_cmd_list:
                    peer_cmd += l
                logging.debug(peer_cmd)
                peer = jsonpickle.decode(peer_cmd)
                logging.debug(peer)
                for c in self.connections.values():
                    if c.transport.getPeer() == peer:
                        c.sendLine(value)


def main():

    # get node index as an argument
    parser = argparse.ArgumentParser()
    parser.add_argument("node_index", help='Index of node in config.py')
    args = parser.parse_args()
    node_index = args.node_index

    # setup node instance
    db_factory = DatabaseFactory(int(node_index))

    # delete level db on disk
    base_path = os.path.expanduser('~/.pichain/DB')
    if os.path.exists(base_path):
        try:
            shutil.rmtree(base_path)
        except Exception as e:
            print(e)
            raise

    # quick node (node index = 0) receives the commands (could be any node)
    if node_index == '0':
        reactor.listenTCP(8000, db_factory)
    elif node_index == '1':
        reactor.listenTCP(8001, db_factory)
    elif node_index == '2':
        reactor.listenTCP(8002, db_factory)

    reactor.run()


if __name__ == "__main__":
    main()

