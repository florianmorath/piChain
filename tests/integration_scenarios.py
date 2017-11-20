"""This module contains test scenarios that are used as integration "tests" of PaxosLogic and PaxosNetwork."""

import logging
from piChain.messages import Transaction
from piChain.config import peers


def scenario1(self):
    """Start the paxos algorithm by bringing a Transaction in circulation. A node sends it directly to the single
    quick node.

    This scenario assumes a healthy state i.e one quick node and the others are slow.

    Args:
        self (ConnectionManager): The ConnectionManager of the Node calling this method

    """
    if self.id == 2:
        logging.debug('scenario1 called')

        # create a Transaction and send it to node with id == 0 (the quick node)
        txn = Transaction(2, 'command1')
        connection = self.peers.get(peers.get('0').get('uuid'))
        if connection is not None:
            logging.debug('txn send to node 0')
            connection.sendLine(txn.serialize())


def scenario2(self):
    """Start the paxos algorithm by bringing a Transaction in circulation. A node broadcasts the transaction.

    This scenario assumes a healthy state i.e one quick node and the others are slow.

    Args:
        self (ConnectionManager): The ConnectionManager of the Node calling this method

    """
    if self.id == 2:
        logging.debug('scenario2 called')

        # create a Transaction and broadcast it
        txn = Transaction(2, 'command1')
        self.broadcast(txn, 'TXN')
