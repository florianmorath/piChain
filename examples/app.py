"""This module shows how the piChain package can be used."""

import logging
import argparse

from twisted.internet import reactor
from twisted.internet.task import deferLater

from piChain import Node


def tx_committed(commands):
    """Called once a block has been committed.

    Args:
        commands (list): List of Transaction commands inside committed block.
    """
    for command in commands:
        logging.debug('command committed: %s', command)


def main():
    """Setup of a Node instance: A peers dictionary containing an (ip,port) pair for each node must be defined. With
    the `node_index` argument one can select the node that will run locally. Optionally one can set the `tx_committed`
    field of the Node instance which is a callable that is called once a block has been committed. By calling
    `start_server()` on the Node instance the local node will try to connect to its peers. Transactions can be committed
    by calling `make_txn(txn)` on the Node instance.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("node_index", help='Index of node in the given peers dict.')
    args = parser.parse_args()
    node_index = args.node_index

    peers = {
        '0': {'ip': '127.0.0.1', 'port': 7982},
        '1': {'ip': '127.0.0.1', 'port': 7981},
        '2': {'ip': '127.0.0.1', 'port': 7980}
    }
    node = Node(int(node_index), peers)
    node.tx_committed = tx_committed
    node.start_server()

    if node_index == '0':
        deferLater(reactor, 3, node.make_txn, 'sql_command1')
        deferLater(reactor, 5, node.make_txn, 'sql_command2')

    reactor.run()


if __name__ == "__main__":
    main()
