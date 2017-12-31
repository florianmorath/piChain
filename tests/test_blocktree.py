from unittest import TestCase
from unittest.mock import MagicMock
from piChain.blocktree import Blocktree, GENESIS
from piChain.messages import Block

import logging
import os
import shutil
logging.disable(logging.CRITICAL)


class TestBlocktree(TestCase):

    def setUp(self):
        self.procs = []

        # delete level db on disk
        base_path = os.path.expanduser('~/.pichain')
        if os.path.exists(base_path):
            try:
                shutil.rmtree(base_path)
            except Exception as e:
                print(e)
                raise

    def tearDown(self):

        # delete level db on disk
        base_path = os.path.expanduser('~/.pichain')
        if os.path.exists(base_path):
            try:
                shutil.rmtree(base_path)
            except Exception as e:
                print(e)
                raise

    def test_ancestor(self):
        # create a blocktree and add blocks to it
        bt = Blocktree(0)
        bt.db = MagicMock()
        b1 = Block(1, GENESIS.block_id, ['a'], 1)
        b2 = Block(2, GENESIS.block_id, ['a'], 2)
        b3 = Block(3, b2.block_id, ['a'], 3)
        b4 = Block(4, b3.block_id, ['a'], 4)
        b5 = Block(5, b2.block_id, ['a'], 5)

        bt.add_block(b1)
        bt.add_block(b2)
        bt.add_block(b3)
        bt.add_block(b4)
        bt.add_block(b5)

        assert bt.ancestor(GENESIS, b1)
        assert bt.ancestor(GENESIS, b4)
        assert bt.ancestor(b2, b5)
        assert not bt.ancestor(b1, b4)
        assert not bt.ancestor(b5, GENESIS)

    def test_common_ancestor(self):
        # create a blocktree and add blocks to it
        bt = Blocktree(0)
        bt.db = MagicMock()
        b1 = Block(1, GENESIS.block_id, ['a'], 1)
        b2 = Block(2, GENESIS.block_id, ['a'], 2)
        b3 = Block(3, b2.block_id, ['a'], 3)
        b4 = Block(4, b3.block_id, ['a'], 4)
        b5 = Block(5, b2.block_id, ['a'], 5)

        bt.add_block(b1)
        bt.add_block(b2)
        bt.add_block(b3)
        bt.add_block(b4)
        bt.add_block(b5)

        assert bt.common_ancestor(b1, b2) == GENESIS
        assert bt.common_ancestor(b4, b5) == b2
        assert bt.common_ancestor(b3, b4) == b3

    def test_valid_block(self):
        # create a blocktree and add blocks to it
        bt = Blocktree(0)
        bt.db = MagicMock()
        b1 = Block(1, GENESIS.block_id, ['a'], 1)
        b2 = Block(2, GENESIS.block_id, ['a'], 2)
        b3 = Block(3, b2.block_id, ['a'], 3)
        b4 = Block(4, b3.block_id, ['a'], 4)
        b5 = Block(5, b2.block_id, ['a'], 5)

        bt.add_block(b1)
        bt.add_block(b2)
        bt.add_block(b3)
        bt.add_block(b4)
        bt.add_block(b5)

        bt.committed_block = b2
        bt.head_block = b3
        assert bt.valid_block(b4)

        bt.committed_block = b1
        bt.head_block = b1
        assert not bt.valid_block(b3)

        bt.committed_block = b3
        bt.head_block = b4
        assert not bt.valid_block(b3)
        assert not bt.valid_block(b2)

    def test_block_set(self):
        # test that __hash__ and __eq__ were implemented correctly
        b1 = Block(0, GENESIS.block_id, ['a'], 1)
        block_set = set()
        block_set.add(b1)
        block_set.add(b1)

        assert len(block_set) == 1

        b2 = Block(0, GENESIS.block_id, ['a'], 2)
        block_set.add(b2)

        assert len(block_set) == 2
