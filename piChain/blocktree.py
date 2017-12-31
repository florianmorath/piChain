"""This module implements the Blocktree class which represents a tree of blocks. It keeps track of special blocks like
 the last committed block and the head block of the tree. It provides operations like adding blocks, checking
 for the validity of a new block and checking if a block is an ancestor of another one."""

import logging
import json
import os

import jsonpickle
import plyvel

from piChain.messages import Block

# genesis block
GENESIS = Block(-1, None, [], 0)
GENESIS.depth = 0


class Blocktree:
    """Tree of blocks.

    Args:
          node_index (int): index of node owning this blocktree (to avoid concurrency problems with mult. local nodes).

    Attributes:
        genesis (Block): the genesis block (adjusted over time to safe memory).
        head_block (Block): deepest block in the blocktree (head of the blockchain).
        committed_block (Block): last committed block.
        committed_blocks (set): ids of all committed blocks so far.
        nodes (dict): dictionary from block_id to instance of type Block. Contains all blocks seen so far.
        counter (int): gobal counter used for txn_id and block_id
        ack_commits (dict): dict from block_id to int that counts how many times a block has been committed.
    """
    def __init__(self, node_index):
        self.genesis = GENESIS
        self.head_block = GENESIS
        self.committed_block = GENESIS
        self.committed_blocks = set()
        self.nodes = {}
        self.nodes.update({GENESIS.block_id: GENESIS})
        self.counter = 0
        self.ack_commits = {}

        # create a db instance (s.t blocks can be recovered after a crash)
        base_path = os.path.expanduser('~/.pichain')
        path = base_path + '/node_' + str(node_index)
        if not os.path.exists(path):
            os.makedirs(path)
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
            elif key == b'genesis':
                msg = json.loads(value)
                block = Block.unserialize(msg)
                self.genesis = block
            elif key == b'committed_blocks':
                block_ids = jsonpickle.decode(value.decode())
                self.committed_blocks = block_ids
                logging.debug(self.committed_blocks)
            elif key != b's_max_block_depth' and key != b's_prop_block' and key != b's_supp_block':
                # block_id -> block
                block_id = int(key.decode())
                msg = json.loads(value)
                block = Block.unserialize(msg)
                self.nodes.update({block_id: block})

    def ancestor(self, block_a, block_b):
        """Check if `block_a` is ancestor of `block_b`. Both blocks must be included in `self.nodes`.

        Args:
            block_a (Block): First block.
            block_b (Block: Second block.

        Returns:
            bool: True if `block_a` is ancestor of `block_b.

        """
        b = block_b
        while b != self.genesis:
            if block_a.block_id == b.parent_block_id:
                return True
            b = self.nodes.get(b.parent_block_id)
        return False

    def common_ancestor(self, block_a, block_b):
        """Return common ancestor of `block_a` and `block_b`.

        Args:
            block_a (Block): First block.
            block_b (Block): Second block.

        Returns:
            Block: common ancestor of `block_a` and `block_b.
        """
        while (block_a != self.genesis or block_b != self.genesis) and block_a != block_b:
            if block_a.depth > block_b.depth:
                block_a = self.nodes.get(block_a.parent_block_id)
            else:
                block_b = self.nodes.get(block_b.parent_block_id)
        return block_a

    def valid_block(self, block):
        """Reject the `block` argument if it is on a discarded fork (i.e `self.commited_block` is not ancestor of it) or
        if it is not deeper than the `head_block`.

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

        Note: Every node has a depth once created, but to facilitate testing depth of a block is computed based on its
        parent if available.

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
