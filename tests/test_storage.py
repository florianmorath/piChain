from unittest import TestCase
from piChain.PaxosLogic import Blocktree, GENESIS
from piChain.messages import Block

import plyvel
import logging
logging.disable(logging.CRITICAL)


class TestBlocktree(TestCase):

    def setUp(self):
        self.bt = Blocktree(0)

    def tearDown(self):
        if self.bt.db.closed:
            path = '/tmp/pichain0'
            self.bt.db = plyvel.DB(path, create_if_missing=True)

        for k, v in self.bt.db:
            self.bt.db.delete(k)
        self.bt.db.close()

    def test_write(self):
        b1 = Block(1, GENESIS.block_id, ['a'])
        b2 = Block(2, GENESIS.block_id, ['a'])
        b3 = Block(3, b2.block_id, ['a'])
        b4 = Block(4, b3.block_id, ['a'])
        b5 = Block(5, b2.block_id, ['a'])

        self.bt.add_block(b1)
        self.bt.add_block(b2)
        self.bt.add_block(b3)
        self.bt.add_block(b4)
        self.bt.add_block(b5)

        assert self.bt.db.get(str(b1.block_id).encode()) == b1.serialize()
        assert self.bt.db.get(str(b2.block_id).encode()) == b2.serialize()
        assert self.bt.db.get(str(b3.block_id).encode()) == b3.serialize()
        assert self.bt.db.get(str(b4.block_id).encode()) == b4.serialize()
        assert self.bt.db.get(str(b5.block_id).encode()) == b5.serialize()

    def test_read(self):
        b1 = Block(1, GENESIS.block_id, ['a'])
        b2 = Block(2, GENESIS.block_id, ['a'])
        b3 = Block(3, b2.block_id, ['a'])
        b4 = Block(4, b3.block_id, ['a'])
        b5 = Block(5, b2.block_id, ['a'])

        self.bt.add_block(b1)
        self.bt.add_block(b2)
        self.bt.add_block(b3)
        self.bt.add_block(b4)
        self.bt.add_block(b5)

        self.bt.db.close()

        # create another BLocktree wich should load the blocks stored by self.bt
        bt2 = Blocktree(0)

        assert bt2.db.get(str(b1.block_id).encode()) == b1.serialize()
        assert bt2.db.get(str(b2.block_id).encode()) == b2.serialize()
        assert bt2.db.get(str(b3.block_id).encode()) == b3.serialize()
        assert bt2.db.get(str(b4.block_id).encode()) == b4.serialize()
        assert bt2.db.get(str(b5.block_id).encode()) == b5.serialize()

        bt2.db.close()
