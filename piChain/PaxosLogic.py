"""This module implements the logic of the paxos algorithm."""

import random
import logging
import time
import json
import plyvel
import os

from piChain.PaxosNetwork import ConnectionManager
from piChain.messages import PaxosMessage, Block, RequestBlockMessage, RespondBlockMessage, Transaction
from piChain.config import peers
from twisted.internet.task import deferLater
from twisted.internet import reactor


QUICK = 0
MEDIUM = 1
SLOW = 2

EPSILON = 0.001

GENESIS = Block(-1, None, [], 0)
GENESIS.depth = 0


class Blocktree:
    """Tree of blocks."""
    def __init__(self, node_index):
        self.head_block = GENESIS  # deepest block in the block tree (head of the blockchain)
        self.committed_block = GENESIS  # last committed block -> will indirectly define all committed blocks so far
        self.nodes = {}  # dictionary from block_id to instance of type Block
        self.nodes.update({GENESIS.block_id: GENESIS})
        self.counter = 0    # gobal counter used for txn_id and block_id

        # create a db instance (s.t blocks can be recovered after a crash)
        base_path = os.path.dirname(os.getcwd()) + '/DB'
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        path = os.path.dirname(os.getcwd()) + '/DB/node_' + str(node_index)
        # path = '/tmp/pichain' + str(node_index)
        self.db = plyvel.DB(path, create_if_missing=True)

        # load blocks and counter (after crash)
        for key, value in self.db:
            if key == b'committed_block':
                msg = json.loads(value)
                block = Block.unserialize(msg)
                self.committed_block = block
            elif key == b'head_block':
                msg = json.loads(value)
                block = Block.unserialize(msg)
                self.head_block = block
            elif key == b'counter':
                self.counter = int(value.decode())
            else:   # block_id -> block
                block_id = int(key.decode())
                msg = json.loads(value)
                block = Block.unserialize(msg)
                self.nodes.update({block_id: block})

    def ancestor(self, block_a, block_b):
        """Check if `block_a` is ancestor of `block_b`. Both blocks must be included in `self.nodes`

        Args:
            block_a (Block): First block
            block_b (Block: Second block

        Returns:
            bool: True if `block_a` is ancestor of `block_b

        """
        b = block_b
        while b.parent_block_id is not None:
            if block_a.block_id == b.parent_block_id:
                return True
            b = self.nodes.get(b.parent_block_id)

        return False

    def common_ancestor(self, block_a, block_b):
        """Return common ancestor of `block_a` and `block_b`.

        Args:
            block_a (Block):
            block_b (Block):

        Returns:
            Block: common ancestor of `block_a` and `block_b.
        """
        while (block_a != GENESIS or block_b != GENESIS) and block_a != block_b:
            if block_a.depth > block_b.depth:
                block_a = self.nodes.get(block_a.parent_block_id)
            else:
                block_b = self.nodes.get(block_b.parent_block_id)

        return block_a

    def valid_block(self, block):
        """Reject `block` if on a discarded fork (i.e `self.commited_block` is not ancestor of it)
         or not deeper than head_block.

        Args:
            block (Block): Block to be tested for validity.

        Returns:
            bool: True if `block` is valid else False.

        """
        # check if committed_block is ancestor of block
        if not self.ancestor(self.committed_block, block):
            return False

        # check if depth of head_block (directly given) is smaller than depth of block
        if block < self.head_block:
            return False

        return True

    def add_block(self, block):
        """Add `block` to `self.nodes`.

        Note: Every node has a depth once created, but to facilitate testing
        depth of a block is computed based on its parent if available.

        Args:
            block (Block): Block to be added.

        """
        if block.depth is None and self.nodes.get(block.parent_block_id) is not None:
            parent = self.nodes.get(block.parent_block_id)
            block.depth = parent.depth + len(block.txs)

        if self.nodes.get(block.block_id) is None:
            self.nodes.update({block.block_id: block})

            # write block to disk
            block_id_str = str(block.block_id)
            block_id_bytes = block_id_str.encode()
            block_bytes = block.serialize()
            self.db.put(block_id_bytes, block_bytes)


class Node(ConnectionManager):

    def __init__(self, node_index):

        super().__init__(node_index)

        self.reactor = reactor  # must be parametrized for testing (default = global reactor)

        self.rtts = {}  # dict: peer_node_id -> RTT
        self.expected_rtt = 1

        self.state = SLOW

        # fields set by app service
        self.tx_committed = None   # callable defined by app service
        # self.tx_committed_deferred = None   # deferred defined by app service

        # ensure that exactly one node will be QUICK in beginning
        if self.id == 0:
            self.state = QUICK

        self.n = len(peers)  # total number of nodes

        self.blocktree = Blocktree(node_index)

        self.sync_mode = False  # True if node is looking for a missing block

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

    def receive_paxos_message(self, message, sender):
        """React on a received `message`. This method implements the main functionality of the paxos algorithm.

        Args:
            message (PaxosMessage): Message received.
            sender (Connection): Connection instance of the sender.

        """
        logging.debug('message type = %s', message.msg_type)
        if message.msg_type == 'TRY':
            # make sure last commited block of sender is also committed by this node
            self.commit(message.last_committed_block)

            if self.s_max_block < message.new_block:
                self.s_max_block = message.new_block

                # create a TRY_OK message
                try_ok = PaxosMessage('TRY_OK', message.request_seq)
                try_ok.prop_block = self.s_prop_block
                try_ok.supp_block = self.s_supp_block
                self.respond(try_ok, sender)

        elif message.msg_type == 'TRY_OK':
            # check if message is not outdated
            if message.request_seq != self.c_request_seq:
                # outdated message
                return

            # if TRY_OK message contains a propose block, we will support it, if it is the first received
            # or if its support block is deeper than the one already stored
            if message.supp_block and self.c_supp_block is None:
                self.c_supp_block = message.supp_block
                self.c_prop_block = message.prop_block
            elif message.supp_block and self.c_supp_block and self.c_supp_block < message.supp_block:
                self.c_supp_block = message.supp_block
                self.c_prop_block = message.prop_block

            self.c_votes += 1
            if self.c_votes > self.n / 2:

                # start new round
                self.c_votes = 0
                self.c_request_seq += 1

                # the compromise block will be the block we are going to propose in the end
                self.c_com_block = self.c_new_block

                # check if we need to support another block instead of the new block
                if self.c_prop_block:
                    self.c_com_block = self.c_prop_block

                # create PROPOSE message
                propose = PaxosMessage('PROPOSE', self.c_request_seq)
                propose.com_block = self.c_com_block
                propose.new_block = self.c_new_block
                self.broadcast(propose, 'PROPOSE')

        elif message.msg_type == 'PROPOSE':
            # if did not receive a try message with a deeper new block in mean time can store proposed block on server
            if message.new_block.depth == self.s_max_block.depth:
                self.s_prop_block = message.com_block
                self.s_supp_block = message.new_block

                # create a PROPOSE_ACK message
                propose_ack = PaxosMessage('PROPOSE_ACK', message.request_seq)
                propose_ack.com_block = message.com_block
                self.respond(propose_ack, sender)

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
                commit = PaxosMessage('COMMIT', self.c_request_seq)
                commit.com_block = message.com_block
                self.broadcast(commit, 'COMMIT')
                self.commit(commit.com_block)

                # allow new paxos instance
                self.commit_running = False

        elif message.msg_type == 'COMMIT':
            self.commit(message.com_block)

            # reinitialize server variables
            self.s_supp_block = None
            self.s_prop_block = None
            self.s_max_block = GENESIS
            self.commit_running = False

    def receive_transaction(self, txn):
        """React on a received `txn` depending on state.

        Args:
            txn (Transaction): Transaction received.

        """
        # check if txn has already been seen
        if txn not in self.known_txs:
            logging.debug('txn has not yet been seen')
            # add txn to set of seen txs
            self.known_txs.add(txn)

            # timeout handling
            self.new_txs.append(txn)
            if len(self.new_txs) == 1:
                self.oldest_txn = txn
                # start a timeout
                logging.debug('start timeout')
                deferLater(self.reactor, self.get_patience(), self.timeout_over, txn)
        else:
            logging.debug('txn has already been seen')

    def receive_block(self, block):
        """React on a received `block`.

        Args:
            block (Block): Received block.

        """
        # make sure block is reachable
        if not self.reach_genesis_block(block):
            logging.debug('block not reachable')
            return

        # demote node if necessary
        if self.blocktree.head_block < block or block.creator_state == QUICK:
            if self.state != SLOW:
                logging.debug('Demoted to slow. Previous State = %s', str(self.state))
            self.state = SLOW

        if not self.blocktree.valid_block(block):
            logging.debug('block invalid')
            return

        self.move_to_block(block)

        # timeout readjustment
        self.readjust_timeout()

    def receive_request_blocks_message(self, req, sender):
        """A node is missing a block. Send him the missing block if node has it. Also send him the five ancestors
         of the missing block s.t he can recover faster in case he is missing more blocks.

        Args:
            req (RequestBlockMessage): Message that requests a missing block.
            sender (Connection): Connection instance form the sender.

        """
        if self.blocktree.nodes.get(req.block_id) is not None:
            blocks = [self.blocktree.nodes.get(req.block_id)]

            # add five ancestors to blocks
            b = self.blocktree.nodes.get(req.block_id)
            i = 0
            while i < 5 and b != GENESIS:
                i = i + 1
                b = self.blocktree.nodes.get(b.parent_block_id)
                if b != GENESIS:
                    blocks.append(b)

            # send blocks back
            respond = RespondBlockMessage(blocks)
            self.respond(respond, sender)

    def receive_respond_blocks_message(self, resp):
        """Receive the blocks that are missing from a peer. Can directly be added to `self.nodes`.

        Args:
            resp (RespondBlockMessage): may contain the missing blocks s.t the node can recover.

        """
        blocks = resp.blocks
        if self.sync_mode:
            for b in blocks:
                self.blocktree.add_block(b)
            # sync finished
            self.sync_mode = False

    def receive_pong_message(self, message, peer_node_id):
        """Receive PongMessage and update RRT's accordingly.

        Args:
            message (PongMessage): Received PongMessage
            peer_node_id (str): uuid of peer who send the pong message

        """
        rtt = round(time.time() - message.time, 3)  # in seconds
        # logging.debug('PongMessage received, rtt = %s', str(rtt))

        # update RTT's
        self.rtts.update({peer_node_id: rtt})
        self.expected_rtt = max(self.rtts.values()) + 1
        # logging.debug('overall expected rtt (max) = %s', str(self.expected_rtt))

    def move_to_block(self, target):
        """Change to `target` block as new `head_block`. If `target` is found on a forked path, have to broadcast txs
         that wont be on the path from `GENESIS` to new `head_block` anymore.

        Args:
            target (Block): will be the new `head_block`

        """
        # make sure target is reachable
        if not self.reach_genesis_block(target):
            return

        if (not self.blocktree.ancestor(target, self.blocktree.head_block)) and target != self.blocktree.head_block:
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
                    if tx in self.new_txs:
                        self.new_txs.remove(tx)
                to_broadcast -= set(b.txs)
                b = self.blocktree.nodes.get(b.parent_block_id)

            # target is now the new head_block
            self.blocktree.head_block = target

            # write changes to disk (add headblock)
            block_bytes = target.serialize()
            self.blocktree.db.put(b'head_block', block_bytes)
            # broadcast txs in to_broadcast
            for tx in to_broadcast:
                self.broadcast(tx, 'TXN')
            self.readjust_timeout()

    def commit(self, block):
        """Commit `block`

        Args:
            block (Block): Block to be committed.

        """
        # make sure block is reachable
        if not self.reach_genesis_block(block):
            return

        if not self.blocktree.ancestor(block, self.blocktree.committed_block) and \
           block != self.blocktree.committed_block:
            logging.debug('committing a block: with block id = %s', str(block.block_id))
            self.blocktree.committed_block = block
            self.move_to_block(block)

            # write changes to disk (add committed block)
            block_bytes = block.serialize()
            self.blocktree.db.put(b'committed_block', block_bytes)

            # print out ids of all committed blocks so far (-> testing purpose)
            self.committed_blocks_report()

            # call callable of app service, better: fire deferred ?
            commands = []
            for txn in block.txs:
                commands.append(txn.content)
            self.tx_committed(commands)

    def reach_genesis_block(self, block):
        """Check if there is a path from `block` to `GENESIS` block. If a block on the path is not contained in
        `self.nodes`, we need to request it from other peers.
        This may happen because of a network partition or if a node is down for a period of time.

        Args:
            block (Block): From this block we want to find a path to GENESIS block.

        Returns:
            bool: True if `GENESIS` block was reached.
        """
        self.blocktree.add_block(block)
        b = block
        while b != GENESIS:
            if self.blocktree.nodes.get(b.parent_block_id) is not None:
                b = self.blocktree.nodes.get(b.parent_block_id)
            else:
                self.sync_mode = True
                req = RequestBlockMessage(b.parent_block_id)
                self.broadcast(req, 'RQB')
                return False
        return True

    def create_block(self):
        """Create a block containing `new_txs` and return it.

        Returns:
            Block: The block that was created.

        """
        logging.debug('create a block')
        # store depth of current head_block (will be parent of new block)
        d = self.blocktree.head_block.depth

        # create block
        self.blocktree.counter += 1
        b = Block(self.id, self.blocktree.head_block.block_id, self.new_txs, self.blocktree.counter)
        self.blocktree.db.put(b'counter', str(self.blocktree.counter).encode())

        # compute its depth (will be fixed -> depth field is only set once)
        b.depth = d + len(b.txs)

        # create a new, empty list (do not use clear!)
        self.new_txs = []

        # add block to blocktree
        self.blocktree.add_block(b)

        # promote node
        if self.state != QUICK:
            self.state = max(QUICK, self.state - 1)
            logging.debug('Got promoted. State = %s', str(self.state))

        # add state of creator node to block
        b.creator_state = self.state

        return b

    def get_patience(self):
        """Returns the time a node has to wait before creating a new block.
        Corresponds to the nodes eagerness to create a new block.

        Returns:
            int: time node has to wait

        """
        if self.state == QUICK:
            patience = 0

        elif self.state == MEDIUM:
            patience = (1 + EPSILON) * self.expected_rtt

        else:
            if self.slow_timeout is None:
                patience = random.uniform((2. + EPSILON) * self.expected_rtt,
                                          (2. + EPSILON) * self.expected_rtt +
                                          self.n * self.expected_rtt * 0.5)
                self.slow_timeout = patience
            else:
                patience = self.slow_timeout
        return patience

    def timeout_over(self, txn):
        """This function is called once a timeout is over. Will check if in the meantime the node received
        the `txn`. If not it is allowed to ceate a new block and broadcast it.

        Args:
            txn (Transaction): This txn triggered the timeout

        """
        logging.debug('timeout_over called')
        if txn in self.new_txs:
            # create a new block
            b = self.create_block()
            self.move_to_block(b)
            self.broadcast(b, 'BLK')

            #  if quick node then start a new instance of paxos
            if self.state == QUICK and not self.commit_running:
                logging.debug('start an new instance of paxos')
                self.commit_running = True
                self.c_votes = 0
                self.c_request_seq += 1
                self.c_supp_block = None
                self.c_prop_block = None
                self.c_new_block = b

                # create try message
                try_msg = PaxosMessage('TRY', self.c_request_seq)
                try_msg.last_committed_block = self.blocktree.committed_block
                try_msg.new_block = self.c_new_block
                self.broadcast(try_msg, 'TRY')

    def readjust_timeout(self):
        """Is called if `new_txs` changed and thus the `oldest_txn` may be removed."""
        if len(self.new_txs) != 0 and self.new_txs[0] != self.oldest_txn:
                self.oldest_txn = self.new_txs[0]
                # start a new timeout
                deferLater(self.reactor, self.get_patience(), self.timeout_over, self.new_txs[0])

    def committed_blocks_report(self):
        """Print out all ids of committed blocks so far. For testing purpose."""
        b = self.blocktree.committed_block
        logging.debug('***********************')
        logging.debug('All committed blocks: ')
        logging.debug('block = %s:', str(b.serialize()))
        print('block = %s:', str(b.serialize()))

        while b != GENESIS:
            b = self.blocktree.nodes.get(b.parent_block_id)
            logging.debug('block = %s:', str(b.serialize()))
            print('block = %s:', str(b.serialize()))
        logging.debug('***********************')

    # methods used by the app

    def make_txn(self, command):
        """This method is called by the app with the command to be committed.

        Args:
            command (str): command to be commited

        """

        self.blocktree.counter += 1
        txn = Transaction(self.id, command, self.blocktree.counter)
        self.blocktree.db.put(b'counter', str(self.blocktree.counter).encode())
        self.broadcast(txn, 'TXN')
