from unittest import TestCase
from piChain.PaxosLogic import Blocktree, GENESIS
from piChain.messages import Block

import plyvel
import logging
import os
import shutil
logging.disable(logging.CRITICAL)


class TestBlocktree(TestCase):

    def setUp(self):
        # delete level db on disk
        path = os.path.dirname(os.getcwd()) + '/DB/'
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(e)
                raise

        self.bt = Blocktree(0)

    def tearDown(self):
        if self.bt.db.closed:
            path = os.path.dirname(os.getcwd()) + '/DB/node_0'
            self.bt.db = plyvel.DB(path, create_if_missing=True)

        # delete level db on disk
        path = os.path.dirname(os.getcwd()) + '/DB/'
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(e)
                raise

    def test_write(self):

        b1 = Block(1, GENESIS.block_id, ['a'], 1)
        b2 = Block(2, GENESIS.block_id, ['a'], 2)
        b3 = Block(3, b2.block_id, ['a'], 3)
        b4 = Block(4, b3.block_id, ['a'], 4)
        b5 = Block(5, b2.block_id, ['a'], 5)

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
        b1 = Block(1, GENESIS.block_id, ['a'], 1)
        b2 = Block(2, GENESIS.block_id, ['a'], 2)
        b3 = Block(3, b2.block_id, ['a'], 3)
        b4 = Block(4, b3.block_id, ['a'], 4)
        b5 = Block(5, b2.block_id, ['a'], 5)

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
