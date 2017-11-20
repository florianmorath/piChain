"""This module contains test scenarios that are used as integration "tests" of PaxosLogic and PaxosNetwork."""

import logging

from twisted.internet import reactor
from twisted.internet.task import deferLater

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
        # create a Transaction and broadcast it
        txn = Transaction(2, 'command1')
        self.broadcast(txn, 'TXN')


def scenario3(self):
    """A node brodcasts multiple transactions simultaneously.

    This scenario assumes a healthy state i.e one quick node and the others are slow.

    Args:
        self (ConnectionManager): The ConnectionManager of the Node calling this method

    """
    if self.id == 2:
        # create Transactions and broadcast them
        txn = Transaction(2, 'command1')
        txn2 = Transaction(2, 'command2')
        self.broadcast(txn, 'TXN')
        self.broadcast(txn2, 'TXN')


def scenario4(self):
    """A node brodcasts multiple transactions with a short delay between them.

    This scenario assumes a healthy state i.e one quick node and the others are slow.

    Args:
        self (ConnectionManager): The ConnectionManager of the Node calling this method

    """
    if self.id == 2:
        # create Transactions and broadcast them
        txn = Transaction(2, 'command1')
        txn2 = Transaction(2, 'command2')
        self.broadcast(txn, 'TXN')

        deferLater(reactor, 0.1, self.broadcast, txn2, 'TXN')


def scenario5(self):
    """Multiple nodes broadcast a transaction.

    This scenario assumes a healthy state i.e one quick node and the others are slow.

    Args:
        self (ConnectionManager): The ConnectionManager of the Node calling this method

    """
    if self.id == 2:
        # create a Transaction and broadcast it
        txn = Transaction(2, 'command1')
        self.broadcast(txn, 'TXN')

    elif self.id == 1:
        # create a Transaction and broadcast it
        txn = Transaction(1, 'command2')
        self.broadcast(txn, 'TXN')


def scenario6(self):
    """Quick node broadcasts a transaction.

    This scenario assumes a healthy state i.e one quick node and the others are slow.

    Args:
        self (ConnectionManager): The ConnectionManager of the Node calling this method

    """
    if self.id == 0:
        # create a Transaction and broadcast it
        txn = Transaction(0, 'command1')
        self.broadcast(txn, 'TXN')
