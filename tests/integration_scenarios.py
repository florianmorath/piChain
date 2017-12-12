"""This module contains test scenarios that are used as integration "tests" of PaxosLogic and PaxosNetwork.

basic behavior:
- Scenarios 1-6 test the healthy state.
- Scenarios 7-12 test each possible unhealthy state the system can be in.

crash behavior:
- Scenarios 20-21 test node crashes.

partition bahavior:
- Scenarios 30-

note: Can for example use Multirun plugin of pyCharm or write a script to start all nodes at exactly the same time,
this avoids the problem of initializing the state of the nodes at different times.

note: currently the tests only work locally
"""

import logging

from twisted.internet import reactor
from twisted.internet.task import deferLater

from piChain.messages import Transaction
from piChain.config import peers
from piChain.PaxosLogic import Node


class IntegrationScenarios:

    """ basic behavior
    """

    @staticmethod
    def scenario1(node):
        """Start the paxos algorithm by bringing a Transaction in circulation. A node sends it directly to the single
        quick node.

        This scenario assumes a healthy state i.e one quick node and the others are slow.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 1')
        if node.id == 2:
            # create a Transaction and send it to node with id == 0 (the quick node)
            txn = Transaction(2, 'command1', 1)
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
        logging.debug('start test scenario 2')

        if node.id == 2:
            # create a Transaction and broadcast it
            txn = Transaction(2, 'command1', 1)
            node.broadcast(txn, 'TXN')

    @staticmethod
    def scenario3(node):
        """A node brodcasts multiple transactions simultaneously.

        This scenario assumes a healthy state i.e one quick node and the others are slow.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 3')
        if node.id == 2:
            # create Transactions and broadcast them
            txn = Transaction(2, 'command1', 1)
            txn2 = Transaction(2, 'command2', 3)
            node.broadcast(txn, 'TXN')
            node.broadcast(txn2, 'TXN')

    @staticmethod
    def scenario4(node):
        """A node brodcasts multiple transactions with a short delay between them.

        This scenario assumes a healthy state i.e one quick node and the others are slow.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 4')
        if node.id == 2:
            # create Transactions and broadcast them
            txn = Transaction(2, 'command1', 1)
            txn2 = Transaction(2, 'command2', 2)
            node.broadcast(txn, 'TXN')

            deferLater(reactor, 1, node.broadcast, txn2, 'TXN')

    @staticmethod
    def scenario5(node):
        """Multiple nodes broadcast a transaction.

        This scenario assumes a healthy state i.e one quick node and the others are slow.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 5')
        if node.id == 2:
            # create a Transaction and broadcast it
            txn = Transaction(2, 'command1', 1)
            node.broadcast(txn, 'TXN')

        elif node.id == 1:
            # create a Transaction and broadcast it
            txn = Transaction(1, 'command2', 2)
            node.broadcast(txn, 'TXN')

            # create another Transaction and broadcast it
            txn3 = Transaction(1, 'command3', 3)
            node.broadcast(txn, 'TXN')
            deferLater(reactor, 1, node.broadcast, txn3, 'TXN')

    @staticmethod
    def scenario6(node):
        """Quick node broadcasts a transaction.

        This scenario assumes a healthy state i.e one quick node and the others are slow.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 6')
        if node.id == 0:
            # create a Transaction and broadcast it
            txn = Transaction(0, 'command1', 1)
            node.broadcast(txn, 'TXN')

    @staticmethod
    def scenario7(node):
        """Unhealthy state: q = 0 and m = 1. Medium node will create a block and promote itself. Thus we are in a
         healthy state again. Because the node is quick it will directly start a paxos instance.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 7')
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
            txn = Transaction(2, 'command1', 1)
            deferLater(reactor, 0.1, node.broadcast, txn, 'TXN')

    @staticmethod
    def scenario8(node):
        """Unhealthy state: q = 1 and m > 1. Quick node will create a block which demotes other medium nodes. Thus
        we are back in a healthy state again.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 8')
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
            txn = Transaction(2, 'command1', 1)
            deferLater(reactor, 0.1, node.broadcast, txn, 'TXN')

    @staticmethod
    def scenario9(node):
        """Unhealthy state: q = 0 and m = 0. At least one slow node will create a block. They will all promote to
        medium. If there are more than one they will see each others blocks and since only one is the deepest, all but
        one will demote to slow. The single medium node promotes to quick once it created another block.
        Thus we are eventually back in a healthy state.

        note: to test case where more than one slow nodes creates a block (simultaneously) remove random perturbation
        of patience of slow nodes.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 9')
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
            txn = Transaction(2, 'command1', 1)
            deferLater(reactor, 0.1, node.broadcast, txn, 'TXN')

            # create another Transaction a little bit later and broadcast it
            txn2 = Transaction(2, 'command2', 2)
            deferLater(reactor, 1, node.broadcast, txn2, 'TXN')

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
        logging.debug('start test scenario 10')
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
            txn = Transaction(2, 'command1', 1)
            deferLater(reactor, 0.1, node.broadcast, txn, 'TXN')

    @staticmethod
    def scenario11(node):
        """Unhealthy state: q > 1. This scenario can happen because of a partition. The quick nodes will all
        create blocks immediately and start a paxos instance (here is where the consistency guarantee of paxos is
        needed because we have multiple paxos clients competing for their block to be committed).
        Since a receipt of a block created by a quick node results in demoting to slow, all nodes will demote to slow
        and we are in the scenario q = 0 / m = 0 described above. Thus we are eventually back in a healthy state.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 11')
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
            txn = Transaction(2, 'command1', 1)
            deferLater(reactor, 0.1, node.broadcast, txn, 'TXN')

            # create another Transaction a little bit later and broadcast it
            txn2 = Transaction(2, 'command2', 2)
            deferLater(reactor, 2, node.broadcast, txn2, 'TXN')

            # create another Transaction a little bit later and broadcast it
            txn3 = Transaction(2, 'command3', 3)
            deferLater(reactor, 4, node.broadcast, txn3, 'TXN')

    @staticmethod
    def scenario12(node):
        """Unhealthy state: q = 0 and m > 1. All the medium nodes will create a block and promote to quick. Since a
        receipt of a block where the creator state was quick demotes a node to slow, all nodes demote to slow and we
        are in scenario q = 0/m = 0 described above.  Thus we are eventually back in a healthy state.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 12')
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
            txn = Transaction(2, 'command1', 1)
            deferLater(reactor, 0.1, node.broadcast, txn, 'TXN')

            # create another Transaction a little bit later and broadcast it
            txn2 = Transaction(2, 'command2', 2)
            deferLater(reactor, 2, node.broadcast, txn2, 'TXN')

            # create another Transaction a little bit later and broadcast it
            txn3 = Transaction(2, 'command3', 3)
            deferLater(reactor, 4, node.broadcast, txn3, 'TXN')

    """ crash behavior 
    """

    @staticmethod
    def scenario20(node):
        """Test Node crashes. Crash a slow node after a commit.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 20')
        if node.id == 0:

            # create a Transaction and broadcast it
            txn = Transaction(0, 'command1', 1)
            deferLater(reactor, 0.1, node.broadcast, txn, 'TXN')

            # create another Transaction after crashed node recovered
            txn2 = Transaction(0, 'command2', 2)
            deferLater(reactor, 6, node.broadcast, txn2, 'TXN')

    @staticmethod
    def scenario21(node):
        """Test Node crashes. Crash the quick node after a commit.

        Args:
            node (Node): Node calling this method

        """
        logging.debug('start test scenario 21')
        if node.id == 1:

            # create a Transaction and broadcast it
            txn = Transaction(1, 'command1', 1)
            deferLater(reactor, 0.1, node.broadcast, txn, 'TXN')

            # create another Transaction after crashed node recovered
            txn2 = Transaction(1, 'command2', 2)
            deferLater(reactor, 6, node.broadcast, txn2, 'TXN')

    """ partition behavior 
    """

    @staticmethod
    def broadcast(self, obj, msg_type):
        """
        This method overrides the broadcast method and simulates a partition if 'self.partitioned' is set to True.
        The partition separates node 4 from node 0-3.

        `obj` will be broadcast to all the peers.

        Args:
            self: an instance of ConnectionManager
            obj: an instance of type Message, Block or Transaction
            msg_type (str): 3 char description of message type

        """
        if self.id == 4 and self.partitioned:
            # do not broadcast to other nodes
            pass
        else:
            # do not broadcast to node 4

            logging.debug('broadcast: %s', msg_type)
            # go over all connections in self.peers and call sendLine on them
            for k, v in self.peers.items():
                if k == peers.get('4').get('uuid') and self.partitioned:
                    pass
                else:
                    data = obj.serialize()
                    v.sendLine(data)

        # if obj is a Transaction then the node also has to send it to itself
        if msg_type == 'TXN':
            self.receive_transaction(obj)

    @staticmethod
    def resolvePartition():
        Node.partitioned = False

    @staticmethod
    def scenario30(node):
        """Test a partition. On the majority site a txn is broadcast which leads in committing a block containing the
        txn. After the resolution of the partition another transaction is brodcast which leads in committing another
        block containing the txn. The minority site will learn about the missed commit.

        Args:
            node (Node): Node calling this method

        """
        # class patching
        Node.broadcast = IntegrationScenarios.broadcast
        Node.partitioned = True

        logging.debug('start test scenario 30')

        # partition will be resolved after given time
        deferLater(reactor, 2, IntegrationScenarios.resolvePartition)

        if node.id == 2:
            # create a Transaction and broadcast it
            txn = Transaction(2, 'command1', 1)
            deferLater(reactor, 0.1, node.broadcast, txn, 'TXN')

            # create a Transaction and broadcast it
            txn2 = Transaction(2, 'command2', 2)
            deferLater(reactor, 4, node.broadcast, txn2, 'TXN')

    @staticmethod
    def scenario31(node):
        """Test a partition. Both in the majority site and in the minority site a block is created because of a received
        transaction. The majority site will commit their block and the minority site will not. After the resolution of
        the partition, a node in the majority site will broadcast a transaction which results in committing this block.
        The minority site finds out about the missed commit and will commit the missed block. This results in a change
        of the head block on the minority site and a broadcast of the transaction on the discarded fork. This broadcast
        leads to a commit of another block eventually.

        Args:
            node (Node): Node calling this method

        """
        # class patching
        Node.broadcast = IntegrationScenarios.broadcast
        Node.partitioned = True

        logging.debug('start test scenario 31')

        # partition will be resolved after given time
        deferLater(reactor, 2, IntegrationScenarios.resolvePartition)

        if node.id == 2:
            # create a Transaction and broadcast it
            txn = Transaction(2, 'command1', 1)
            deferLater(reactor, 0.1, node.broadcast, txn, 'TXN')

            # create a Transaction and broadcast it
            txn2 = Transaction(2, 'command2', 2)
            deferLater(reactor, 4, node.broadcast, txn2, 'TXN')
        elif node.id == 4:
            # create a Transaction and broadcast it
            txn3 = Transaction(4, 'command3', 3)
            deferLater(reactor, 0.1, node.broadcast, txn3, 'TXN')
