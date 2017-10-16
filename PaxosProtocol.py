import itertools
import random
import threading

"""
    This module implements the logic of the paxos algorithm.
"""

QUICK = 0
MEDIUM = 1
SLOW = 2

EXPECTED_RTT = 1.
EPSILON = 0.001


class Block:
    new_seq = itertools.count()

    def __init__(self, creator_id, parent, txs):
        self.creator_id = creator_id
        self.SEQ = next(Block.new_seq)
        self.creator_state = None
        self.parent = parent  # parent block
        self.txs = txs  # list of transactions of type Transaction

        if parent:
            self.depth = parent.depth + len(txs)
        else:
            self.depth = 0

    def __lt__(self, other):
        """Compare two blocks by depth and creator ID."""
        if self.depth < other.depth:
            return True

        if self.depth > other.depth:
            return False

        return self.creator_id < other.creator_id


GENESIS = Block(-1, None, [])


class Transaction:
    new_seq = itertools.count()

    def __init__(self, creator_id, content):
        self.creator_id = creator_id
        self.SEQ = next(Transaction.new_seq)
        self.content = content  # a string which can represent a command for example


class Message:
    def __init__(self, message_type):
        self.message_type = message_type  # try, ok, propose, ack, commit


class Node:
    new_id = itertools.count()

    def __init__(self, n):
        self.id = next(Node.new_id)
        self.state = QUICK
        self.new_txs = set()  # txs not yet in a block
        self.head_block = GENESIS  # deepest block in the block tree (head of the blockchain)
        self.blocks = set()  # all blocks seen by the node
        self.n = n  # total number of nodes

    # main methods

    def receive_message(self, message):
        """Receive a message of type Message. Return answer of type Message."""
        # TODO implement receive message

    # def receive_transaction(self, txn):
    #     """React on a received txn depending on state"""
    #     # check if txn has already been seen included in a block
    #     if not self.txn_seen(txn):
    #         # add txn to set of new txs
    #         self.new_txs.add(txn)
    #
    #         # callback after timeout of length get_patience: not txn_seen implies create_block
    #         threading.Timer(self.get_patience(), self.create_block())

    def receive_block(self, block):
        """React on a received block """
        # add block to set of blocks seen so far
        self.blocks.add(block)

        # readjust head block if necessary
        if self.head_block < block:
            self.head_block = block

        # demote node if necessary
        if self.head_block < block or block.creator_state == QUICK:
            self.state = SLOW

    # helper methods

    def create_block(self):
        """Create a block containing new txs and return it."""  # create block
        b = Block(self.id, self.head_block, list(self.new_txs))
        self.new_txs.clear()

        # promote node
        self.state = max(QUICK, self.state - 1)

        # add state of creator node to block
        b.creator_state = self.state

        return b

    def get_patience(self):
        """Returns the time a node has to wait before creating a new block.
        Corresponds to the nodes eagerness to create a new block. """
        if self.state == QUICK:
            patience = 0

        elif self.state == MEDIUM:
            patience = (1 + EPSILON) * EXPECTED_RTT

        else:
            patience = random.uniform((2. + EPSILON) * EXPECTED_RTT,
                                      (2. + EPSILON) * EXPECTED_RTT +
                                      self.n * EXPECTED_RTT * 0.5)
        return patience

    def txn_seen(self, txn):
        """Check if the txn has already been included in a block. Return True if yes."""
        # TODO implement txn_seen
        return True
