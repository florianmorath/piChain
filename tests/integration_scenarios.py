"""This module contains test scenarios that are used as integration "tests" of PaxosLogic and PaxosNetwork.
All scenarios are based on three running nodes with node id 0,1 and 2. Scenarios 1-6 test the healthy state and
scenarios 7-11 test each possible unhealthy state the system can be in.

note: Can for example use Multirun plugin of pyCharm or write a script to start all nodes at exactly the same time,
this avoids the problem of initializing the state of the nodes at different times."""

import logging

from twisted.internet import reactor
from twisted.internet.task import deferLater

from piChain.messages import Transaction
from piChain.config import peers


class IntegrationScenarios:

    @staticmethod
    def scenario1(node):
        """Start the paxos algorithm by bringing a Transaction in circulation. A node sends it directly to the single
        quick node.

        This scenario assumes a healthy state i.e one quick node and the others are slow.

        Args:
            node (Node): Node calling this method

        """
        if node.id == 2:
            # create a Transaction and send it to node with id == 0 (the quick node)
            txn = Transaction(2, 'command1')
            connection = node.peers.get(peers.get('0').get('uuid'))
            if connection is not None:
                logging.debug('txn send to node 0')
                connection.sendLine(txn.serialize())

    @staticmethod
    def scenario2(node):
        """Start the paxos algorithm by bringing a Transaction in circulation. A node broadcasts the transaction.

        This scenario assumes a healthy state i.e one quick node and the others are slow.

        Args:
            node (Node): Node calling this method

        """
        if node.id == 2:
            # create a Transaction and broadcast it
            txn = Transaction(2, 'command1')
            node.broadcast(txn, 'TXN')

    @staticmethod
    def scenario3(node):
        """A node brodcasts multiple transactions simultaneously.

        This scenario assumes a healthy state i.e one quick node and the others are slow.

        Args:
            node (Node): Node calling this method

        """
        if node.id == 2:
            # create Transactions and broadcast them
            txn = Transaction(2, 'command1')
            txn2 = Transaction(2, 'command2')
            node.broadcast(txn, 'TXN')
            node.broadcast(txn2, 'TXN')

    @staticmethod
    def scenario4(node):
        """A node brodcasts multiple transactions with a short delay between them.

        This scenario assumes a healthy state i.e one quick node and the others are slow.

        Args:
            node (Node): Node calling this method

        """
        if node.id == 2:
            # create Transactions and broadcast them
            txn = Transaction(2, 'command1')
            txn2 = Transaction(2, 'command2')
            node.broadcast(txn, 'TXN')

            deferLater(reactor, 0.1, node.broadcast, txn2, 'TXN')

    @staticmethod
    def scenario5(node):
        """Multiple nodes broadcast a transaction.

        This scenario assumes a healthy state i.e one quick node and the others are slow.

        Args:
            node (Node): Node calling this method

        """
        if node.id == 2:
            # create a Transaction and broadcast it
            txn = Transaction(2, 'command1')
            node.broadcast(txn, 'TXN')

        elif node.id == 1:
            # create a Transaction and broadcast it
            txn = Transaction(1, 'command2')
            node.broadcast(txn, 'TXN')

    @staticmethod
    def scenario6(node):
        """Quick node broadcasts a transaction.

        This scenario assumes a healthy state i.e one quick node and the others are slow.

        Args:
            node (Node): Node calling this method

        """
        if node.id == 0:
            # create a Transaction and broadcast it
            txn = Transaction(0, 'command1')
            node.broadcast(txn, 'TXN')

    @staticmethod
    def scenario7(node):
        """Unhealthy state: q = 0 and m = 1. Medium node will create a block and promote itself. Thus we are in a
         healthy state again. Because the node is quick it will directly start a paxos instance.

        Args:
            node (Node): Node calling this method

        """
        if node.id == 0:
            # medium node
            node.state = 1

        elif node.id == 1:
            # slow node
            node.state = 2

        elif node.id == 2:
            # slow node
            node.state = 2

            # create a Transaction and broadcast it
            txn = Transaction(2, 'command1')
            node.broadcast(txn, 'TXN')

    @staticmethod
    def scenario8(node):
        """Unhealthy state: q = 1 and m > 1. Quick node will create a block which demotes other medium nodes. Thus
        we are back in a healthy state again.

        Args:
            node (Node): Node calling this method

        """
        if node.id == 0:
            # quick node
            node.state = 0

        elif node.id == 1:
            # medium node
            node.state = 1

        elif node.id == 2:
            # medium node
            node.state = 1

            # create a Transaction and broadcast it
            txn = Transaction(2, 'command1')
            node.broadcast(txn, 'TXN')

    @staticmethod
    def scenario9(node):
        """Unhealthy state: q = 0 and m = 0. At least one slow node will create a block. They will all promote to
        medium. If there are more than one they will see each others blocks and since only one is the deepest, all but
        one will demote to slow. The single medium node promotes to quick once it created another block.
        Thus we are eventually back in a healthy state.

        note: to test case where more than one slow nodes creates a block (simultaneously) remove random perturbation
        of patience to slow nodes.

        Args:
            node (Node): Node calling this method

        """
        if node.id == 0:
            # slow node
            node.state = 2

        elif node.id == 1:
            # slow node
            node.state = 2

        elif node.id == 2:
            # slow node
            node.state = 2

            # create a Transaction and broadcast it
            txn = Transaction(2, 'command1')
            node.broadcast(txn, 'TXN')

            # create another Transaction a little bit later and broadcast it
            txn2 = Transaction(2, 'command2')
            deferLater(reactor, 20, node.broadcast, txn2, 'TXN')

    @staticmethod
    def scenario10(node):
        """Unhealthy state: q > 1. This scenario can happen because of a partition. The quick nodes will all
        create blocks immediately and start a paxos instance (here is where the consistency guarantee of paxos is
        needed because we have multiple paxos clients competing for their block to be committed).
        Since a receipt of a block created by a quick node results in demoting to slow, all nodes will demote to slow
        and we are in the scenario q = 0 / m = 0 described above. Thus we are eventually back in a healthy state.

        Args:
            node (Node): Node calling this method

        """
        if node.id == 0:
            # quick node
            node.state = 0

        elif node.id == 1:
            # quick node
            node.state = 0

        elif node.id == 2:
            # quick node
            node.state = 0

            # create a Transaction and broadcast it
            txn = Transaction(2, 'command1')
            node.broadcast(txn, 'TXN')

            # create another Transaction a little bit later and broadcast it
            txn2 = Transaction(2, 'command2')
            deferLater(reactor, 20, node.broadcast, txn2, 'TXN')

            # create another Transaction a little bit later and broadcast it
            txn3 = Transaction(2, 'command3')
            deferLater(reactor, 40, node.broadcast, txn3, 'TXN')

    @staticmethod
    def scenario11(node):
        """Unhealthy state: q = 0 and m > 1. All the medium nodes will create a block and promote to quick. Since a
        receipt of a block where the creator state was quick demotes a node to slow, all nodes demote to slow and we
        are in scenario q = 0/m = 0 described above.  Thus we are eventually back in a healthy state.

        Args:
            node (Node): Node calling this method

        """
        if node.id == 0:
            # medium node
            node.state = 1

        elif node.id == 1:
            # medium node
            node.state = 1

        elif node.id == 2:
            # medium node
            node.state = 1

            # create a Transaction and broadcast it
            txn = Transaction(2, 'command1')
            node.broadcast(txn, 'TXN')

            # create another Transaction a little bit later and broadcast it
            txn2 = Transaction(2, 'command2')
            deferLater(reactor, 20, node.broadcast, txn2, 'TXN')

            # create another Transaction a little bit later and broadcast it
            txn3 = Transaction(2, 'command3')
            deferLater(reactor, 40, node.broadcast, txn3, 'TXN')
