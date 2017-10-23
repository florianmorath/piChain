import itertools
import random

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
    def __init__(self, msg_type, broadcast, request_seq):
        self.msg_type = msg_type  # TRY, TRY_OK, PROPOSE, PROPOSE_ACK, COMMIT
        self.broadcast = broadcast  # bool
        self.request_seq = request_seq

        # content variables: are assigned depending on message type
        self.new_block = None
        self.prop_block = None
        self.supp_block = None
        self.com_block = None


class Node:
    new_id = itertools.count()

    def __init__(self, n):
        self.id = next(Node.new_id)
        self.state = QUICK
        self.new_txs = set()  # txs not yet in a block
        self.head_block = GENESIS  # deepest block in the block tree (head of the blockchain)
        self.blocks = set()  # all blocks seen by the node
        self.n = n  # total number of nodes

        self.committed_blocks = [GENESIS]

        # node acting as server
        self.s_max_block = GENESIS  # deepest block seen in round 1 (like T_max)
        self.s_prop_block = None  # stored block from a valid propose message
        self.s_supp_block = None  # block supporting proposed block (like T_store)

        # node acting as client
        self.c_new_block = None  # block which client (a quick node) wants to commit next
        self.c_com_block = None  # temporary compromise block
        self.c_request_seq = 0  # Voting round number
        self.c_votes = 0  # used to check if majority is already reached
        self.c_prop_block = None  # propose block with deepest support block the client has seen in round 2
        self.c_supp_block = None

    # main methods

    def receive_message(self, message):
        """Receive a message of type Message. Return answer of type Message or None of majority not yet reached"""
        if message.msg_type == 'TRY':
            if self.s_max_block < message.new_block:
                self.s_max_block = message.new_block

                # create a TRY_OK message
                try_ok = Message('TRY_OK', False, message.request_seq)
                try_ok.prop_block = self.s_prop_block
                try_ok.supp_block = self.s_supp_block
                return try_ok
            return None

        elif message.msg_type == 'TRY_OK':
            # check if message is not outdated
            if message.request_seq != self.c_request_seq:
                # outdated message
                return None

            self.c_votes += 1
            if self.c_votes > self.n / 2:

                # start new round
                self.c_votes = 0
                self.c_request_seq += 1

                # the compromise block will be the block we are going to propose in the end
                self.c_com_block = self.c_new_block

                # if TRY_OK message contains a propose block, we will support it if it is the first received
                # or if its support block is deeper than the one already stored
                if message.supp_block and self.c_supp_block and self.c_supp_block < message.supp_block:
                    self.c_supp_block = message.supp_block
                    self.c_prop_block = message.prop_block

                # check if we need to support another block instead of the new block
                if self.c_prop_block:
                    self.c_com_block = self.c_prop_block

                # create PROPOSE message
                propose = Message('PROPOSE', True, self.c_request_seq)
                propose.com_block = self.c_com_block
                propose.new_block = self.c_new_block
                return propose
            return None

        elif message.msg_type == 'PROPOSE':
            # if did not receive a try message with a deeper new block in mean time can store proposed block on server
            if message.new_block.depth == self.s_max_block.depth:
                self.s_prop_block = message.com_block
                self.s_supp_block = message.new_block

                # create a PROPOSE_ACK message
                propose_ack = Message('PROPOSE_ACK', False, message.request_seq)
                propose_ack.com_block = message.com_block
                return propose_ack
            return None

        elif message.msg_type == 'PROPOSE_ACK':
            # check if message is not outdated
            if message.request_seq != self.c_request_seq:
                # outdated message
                return None

            self.c_votes += 1
            if self.c_votes > self.n / 2:
                # ignore further answers
                self.c_request_seq += 1

                # create commit message
                commit = Message('COMMIT', True, self.c_request_seq)
                commit.com_block = message.com_block
                return commit
            return None

        elif message.msg_type == 'COMMIT':
            self.committed_blocks = message.com_block
            # TODO move_to_block and reinitialize server variables

    def receive_transaction(self, txn):
        """React on a received txn depending on state"""
        # check if txn has already been seen included in a block
        if not self.txn_seen(txn):
            # add txn to set of new txs
            self.new_txs.add(txn)

            # TODO timeout handling -> see readjust_timeout (gammachain)
            # timeout handling
            # callback after timeout of length get_patience: not txn_seen implies create_block
            # threading.Timer(self.get_patience(), self.create_block())
            # handle timeout in PaxosNode class with Twisted

    def receive_block(self, block):
        """React on a received block """

        # demote node if necessary
        if self.head_block < block or block.creator_state == QUICK:
            self.state = SLOW

        # block must be ancestor of last committed block and deeper than head_block
        # TODO reject block if on discarded fork or not deeper than head_block

        # TODO update head_block, also see move_to_block -> update known and new txs
        # add block to set of blocks seen so far
        self.blocks.add(block)

        # readjust head block if necessary
        if self.head_block < block:
            self.head_block = block

    # helper methods

    def create_block(self):
        """Create a block containing new txs and return it."""  # create block
        b = Block(self.id, self.head_block, list(self.new_txs))
        self.new_txs.clear()

        # add block to set of blocks seen so far
        self.blocks.add(b)

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
        # TODO remove self.blocks and get known txs starting from head_block and going over his parents
        txn_seen = False
        for block in self.blocks:
            for tx in block.txs:
                if tx.creator_id == txn.creator_id and tx.SEQ == txn.SEQ:
                    txn_seen = True
        return txn_seen
