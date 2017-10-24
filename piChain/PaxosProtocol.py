import itertools
import random
from pichain.PaxosNode import PaxosNodeProtocol
from twisted.internet.task import deferLater
from twisted.internet import reactor

"""
    This module implements the logic of the paxos algorithm.
"""

QUICK = 0
MEDIUM = 1
SLOW = 2

EXPECTED_RTT = 1.
EPSILON = 0.001


class Blocktree:
    """Tree of blocks that is always in a consistent state"""
    def __init__(self):
        self.head_block = GENESIS  # deepest block in the block tree (head of the blockchain)
        self.committed_block = GENESIS  # last committed block -> will indirectly define all committed blocks so far
        self.nodes = {}  # dictionary from block_id to instance of type Block
        self.nodes.update({GENESIS.block_id: GENESIS})
        self.blocks = set()  # all blocks seen by the node (also discarded blocks are stored here)

    def reach_genesis_block(self, block):
        """Check if there is a path from block to GENESIS block. If a block on the path is not contained in
        self.nodes nor in self.blocks, we need to request it from other peers. This may happen because of a
         network partition or if a node is down for a period of time"""
        # TODO: implement reach_genesis_block (add all blocks to self.blocks)
        self.blocks.add(block)

    def ancestor(self, block_a, block_b):
        """Return True if block_a is ancestor of block_b. """
        b = block_b
        while b.parent_block_id is not None:
            if block_a.block_id == b.parent_block_id:
                return True
            b = self.nodes.get(b.parent_block_id)

        return False

    def common_ancestor(self, block_a, block_b):
        """Return common ancestor of block_a and block_b"""
        while (block_a != GENESIS or block_b != GENESIS) and block_a != block_b:
            if block_a.depth > block_b.depth:
                block_a = self.nodes.get(block_a.parent_block_id)
            else:
                block_b = self.nodes.get(block_b.parent_block_id)

        return block_a

    def valid_block(self, block):
        """Reject block if on a discarded fork (i.e commited_block is not ancestor of it)
         or not deeper than head_block"""

        # check if committed_block is ancestor of block
        if not self.ancestor(self.committed_block, block):
            return False

        # check if depth of head_block (directly given) is smaller than depth of block
        if block < self.head_block:
            return False

        return True


class Block:
    new_seq = itertools.count()

    def __init__(self, creator_id, parent_block_id, txs):
        self.creator_id = creator_id
        self.SEQ = next(Block.new_seq)
        self.block_id = int(str(self.creator_id) + str(self.SEQ))
        self.creator_state = None
        self.parent_block_id = parent_block_id  # parent block id (creator_id || SEQ)
        self.txs = txs  # list of transactions of type Transaction
        self.depth = None  # should not be directly accessed if block is not contained in blocktree

    def __lt__(self, other):
        """Compare two blocks by depth and creator ID."""
        if self.depth < other.depth:
            return True

        if self.depth > other.depth:
            return False

        return self.creator_id < other.creator_id

    def __eq__(self, other):
        return self.block_id == other.block_id

    def __hash__(self):
        return 0


GENESIS = Block(-1, None, [])


class Transaction:
    new_seq = itertools.count()

    def __init__(self, creator_id, content):
        self.creator_id = creator_id
        self.SEQ = next(Transaction.new_seq)
        self.txn_id = int(str(self.creator_id) + str(self.SEQ))
        self.content = content  # a string which can represent a command for example

    def __eq__(self, other):
        return self.txn_id == other.txn_id

    def __hash__(self):
        return 0


class Message:
    def __init__(self, msg_type, request_seq):
        self.msg_type = msg_type  # TRY, TRY_OK, PROPOSE, PROPOSE_ACK, COMMIT
        self.request_seq = request_seq

        # content variables: are assigned depending on message type
        self.new_block = None
        self.prop_block = None
        self.supp_block = None
        self.com_block = None
        self.last_committed_block = None


class Node(PaxosNodeProtocol):
    new_id = itertools.count()

    def __init__(self, n, factory):

        super().__init__(factory)

        self.id = next(Node.new_id)
        self.state = SLOW
        self.n = n  # total number of nodes

        self.blocktree = Blocktree()

        self.known_txs = set()  # all txs seen so far
        self.new_txs = []  # txs not yet in a block, behaving like a queue

        self.slow_timeout = None    # fix timeout of a slow node (u.a.r only once)
        self.oldest_txn = None  # txn which started a timeout

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

        self.commit_running = False

    # main methods

    def broadcast(self, obj):
        """obj is an instance of type Message, Block or Transaction which will be broadcast to all peers.
         Method will be implemented in superclass."""
        raise NotImplementedError("Superclass should implement this!")

    def respond(self, obj):
        """obj is an instance of type Message, Block or Transaction which will be responded to to the peer
        which has send the request. Method will be implemented in superclass."""
        raise NotImplementedError("Superclass should implement this!")

    def receive_message(self, message):
        """Receive a message of type Message"""
        if message.msg_type == 'TRY':
            # make sure last commited block of sender is also commited by this node
            self.commit(message.last_committed_block)

            if self.s_max_block < message.new_block:
                self.s_max_block = message.new_block

                # create a TRY_OK message
                try_ok = Message('TRY_OK', message.request_seq)
                try_ok.prop_block = self.s_prop_block
                try_ok.supp_block = self.s_supp_block
                self.respond(try_ok)

        elif message.msg_type == 'TRY_OK':
            # check if message is not outdated
            if message.request_seq != self.c_request_seq:
                # outdated message
                return

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
                propose = Message('PROPOSE', self.c_request_seq)
                propose.com_block = self.c_com_block
                propose.new_block = self.c_new_block
                self.broadcast(propose)

        elif message.msg_type == 'PROPOSE':
            # if did not receive a try message with a deeper new block in mean time can store proposed block on server
            if message.new_block.depth == self.s_max_block.depth:
                self.s_prop_block = message.com_block
                self.s_supp_block = message.new_block

                # create a PROPOSE_ACK message
                propose_ack = Message('PROPOSE_ACK', message.request_seq)
                propose_ack.com_block = message.com_block
                self.respond(propose_ack)

        elif message.msg_type == 'PROPOSE_ACK':
            # check if message is not outdated
            if message.request_seq != self.c_request_seq:
                # outdated message
                return

            self.c_votes += 1
            if self.c_votes > self.n / 2:
                # ignore further answers
                self.c_request_seq += 1

                # create commit message
                commit = Message('COMMIT', self.c_request_seq)
                commit.com_block = message.com_block
                self.broadcast(commit)

                # allow new paxos instance
                self.commit_running = False

        elif message.msg_type == 'COMMIT':
            self.commit(message.com_block)

            # reinitialize server variables
            self.s_supp_block = None
            self.s_prop_block = None
            self.s_max_block = None

    def receive_transaction(self, txn):
        """React on a received txn depending on state"""
        # check if txn has already been seen
        if txn not in self.known_txs:
            # add txn to set of seen txs
            self.known_txs.add(txn)

            # timeout handling
            self.new_txs.append(txn)
            if len(self.new_txs) == 1:
                self.oldest_txn = txn
                # start a timeout
                deferLater(reactor, self.get_patience(), self.timeout_over(), txn)

    def receive_block(self, block):
        """React on a received block """

        # make sure block is reachable
        self.blocktree.reach_genesis_block(block)

        # demote node if necessary
        if self.blocktree.head_block < block or block.creator_state == QUICK:
            self.state = SLOW

        # add block to set of blocks seen so far
        # self.blocktree.blocks.add(block)

        if not self.blocktree.valid_block(block):
            return

        self.move_to_block(block)

        # timeout readjustment
        self.readjust_timeout()

    def move_to_block(self, target):
        """Change to target block as new head block. If target is found on a forked path, have to broadcast txs
         that wont be on the path from GENESIS to new head block anymore. """

        # make sure target is reachable
        self.blocktree.reach_genesis_block(target)

        if not self.blocktree.ancestor(target, self.blocktree.head_block):
            common_ancestor = self.blocktree.common_ancestor(self.blocktree.head_block, target)
            to_broadcast = set()

            # go from head_block to common ancestor: add txs to to_broadcast
            b = self.blocktree.head_block
            while b != common_ancestor:
                to_broadcast |= set(b.txs)
                b = self.blocktree.nodes.get(b.parent_block_id)

            # go from target to common ancestor: remove txs from to_broadcast and new_txs, add to known_txs
            b = target
            while b != common_ancestor:
                self.known_txs |= set(b.txs)
                for tx in b.txs:
                    self.new_txs.pop(tx, None)
                to_broadcast -= set(b.txs)
                b = self.nodes.get(b.parent_block_id)

            # target is now the new head_block
            self.blocktree.head_block = target

            # broadcast txs in to_broadcast
            for tx in to_broadcast:
                self.broadcast(tx)
            self.readjust_timeout()

    def commit(self, block):
        """Commit block"""
        # make sure block is reachable
        self.blocktree.reach_genesis_block(block)

        if not self.blocktree.ancestor(block, self.blocktree.committed_block):
            self.blocktree.committed_block = block
            self.move_to_block(block)

    # helper methods

    def create_block(self):
        """Create a block containing new txs and return it."""
        # store depth of current head_block (will be parent of new block)
        d = self.blocktree.head_block.depth

        # create block
        b = Block(self.id, self.blocktree.head_block, list(self.new_txs))

        # compute its depth (will be fixed -> depth field is only set once)
        b.depth = d + len(b.txs)

        self.new_txs.clear()

        # add block to set of blocks seen so far
        self.blocktree.blocks.add(b)

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
            if self.slow_timeout is None:
                patience = random.uniform((2. + EPSILON) * EXPECTED_RTT,
                                          (2. + EPSILON) * EXPECTED_RTT +
                                          self.n * EXPECTED_RTT * 0.5)
                self.slow_timeout = patience
            else:
                patience = self.slow_timeout
        return patience

    def timeout_over(self, txn):
        """This function is called once a timeout is over."""
        if txn in self.new_txs:
            # create a new block
            b = self.create_block()

            self.move_to_block(b)
            self.broadcast(b)

            #  if quick node then start a new instance of paxos
            if self.state == QUICK and not self.commit_running:
                self.commit_running = True
                self.c_votes = 0
                self.c_request_seq += 1

                # create try message
                try_msg = Message('TRY', self.c_request_seq)
                try_msg.last_committed_block = self.blocktree.committed_block
                self.broadcast(try_msg)

    def readjust_timeout(self):
        """Is called if new_txs changed and thus the oldest_txn may be removed"""
        if len(self.new_txs) != 0 and self.new_txs[0] != self.oldest_txn:
                self.oldest_txn = self.new_txs[0]
                # start a new timeout
                deferLater(reactor, self.get_patience(), self.timeout_over(), self.new_txs[0])
