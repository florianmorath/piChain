"""This module shows how the pichain package can be used."""

from piChain.PaxosLogic import Node
from twisted.internet import reactor
from twisted.internet.task import deferLater
from twisted.internet import defer

import logging
import argparse


def tx_committed(commands):
    """Called once a block is committed.

    Args:
        commands (list): list of commands inside committed block (one per Transaction)

    """
    for command in commands:
        logging.debug('command committed: %s', command)


def main():

    parser = argparse.ArgumentParser()

    # start server
    parser.add_argument("node_index", help='Index of node in config.py')
    args = parser.parse_args()
    node_index = args.node_index

    deferred = defer.Deferred()
    deferred.addCallback(tx_committed)

    node = Node(int(node_index))

    # node.tx_committed = tx_committed
    node.tx_committed_deferred = deferred

    node.start_server()

    if node_index == '0':
        deferLater(reactor, 20, node.make_txn, 'sql_command')

    reactor.run()


if __name__ == "__main__":
    main()
