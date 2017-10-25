from unittest import TestCase
from piChain.PaxosLogic import Blocktree, Block, GENESIS


class TestBlocktree(TestCase):

    def test_ancestor(self):
        # create a blocktree and add blocks to it
        bt = Blocktree()
        b1 = Block(1, GENESIS.block_id, ['a'])
        b2 = Block(2, GENESIS.block_id, ['a'])
        b3 = Block(3, b2.block_id, ['a'])
        b4 = Block(4, b3.block_id, ['a'])
        b5 = Block(5, b2.block_id, ['a'])

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
        bt = Blocktree()
        b1 = Block(1, GENESIS.block_id, ['a'])
        b2 = Block(2, GENESIS.block_id, ['a'])
        b3 = Block(3, b2.block_id, ['a'])
        b4 = Block(4, b3.block_id, ['a'])
        b5 = Block(5, b2.block_id, ['a'])

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
        bt = Blocktree()
        b1 = Block(1, GENESIS.block_id, ['a'])
        b2 = Block(2, GENESIS.block_id, ['a'])
        b3 = Block(3, b2.block_id, ['a'])
        b4 = Block(4, b3.block_id, ['a'])
        b5 = Block(5, b2.block_id, ['a'])

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
        b1 = Block(0, GENESIS.block_id, ['a'])
        block_set = set()
        block_set.add(b1)
        block_set.add(b1)

        assert len(block_set) == 1

        b2 = Block(0, GENESIS.block_id, ['a'])
        block_set.add(b2)

        assert len(block_set) == 2
