from unittest.mock import MagicMock
from twisted.internet import task
from twisted.trial.unittest import TestCase

from piChain.PaxosLogic import Node, GENESIS
from piChain.messages import PaxosMessage, Block, Transaction, RequestBlockMessage, PongMessage

import logging
import time
import os
import shutil
logging.disable(logging.CRITICAL)


class TestNode(TestCase):

    def setUp(self):
        # delete pichain folder on disk
        base_path = os.path.expanduser('~/.pichain')
        if os.path.exists(base_path):
            try:
                shutil.rmtree(base_path)
            except Exception as e:
                print(e)
                raise

        self.node = Node(0)
        self.node.blocktree.db = MagicMock()

    def test_receive_paxos_message_try(self):
        # try message
        try_msg = PaxosMessage('TRY', 1)
        try_msg.last_committed_block = GENESIS.block_id

        b = Block(1, GENESIS.block_id, ['a'], 1)
        b.depth = 1
        try_msg.new_block = b.block_id

        self.node.respond = MagicMock()
        self.node.blocktree.nodes.update({b.block_id: b})

        self.node.receive_paxos_message(try_msg, 1)
        assert self.node.respond.called
        assert self.node.s_max_block_depth == b.depth

        # obj = self.node.respond.call_args[0][0]
        # print('try_ok message = ', pprint(vars(obj)))
        # print('self.node vars = ', pprint(vars(self.node)))

    def test_receive_paxos_message_try_ok_1(self):
        # try_ok message with no prop/supp block stored locally and message does not contain a propose block
        try_ok = PaxosMessage('TRY_OK', 1)

        b = Block(1, GENESIS.block_id, ['a'], 1)
        b.depth = 1

        self.node.c_request_seq = 1
        self.node.c_new_block = b
        self.node.c_votes = 5
        self.node.broadcast = MagicMock()
        self.node.receive_paxos_message(try_ok, None)
        self.node.blocktree.nodes.update({b.block_id: b})

        assert self.node.broadcast.called
        assert self.node.c_com_block == self.node.c_new_block

    def test_receive_paxos_message_try_ok_2(self):
        # try_ok message with prop/supp block stored locally and message does not contain a propose block
        try_ok = PaxosMessage('TRY_OK', 1)

        b = Block(1, GENESIS.block_id, ['a'], 1)
        b.depth = 1

        self.node.c_request_seq = 1
        self.node.c_new_block = b
        self.node.c_votes = 5
        self.node.c_supp_block = GENESIS
        self.node.c_prop_block = GENESIS

        self.node.broadcast = MagicMock()
        self.node.receive_paxos_message(try_ok, None)

        assert self.node.broadcast.called
        assert self.node.c_supp_block == GENESIS

    def test_receive_paxos_message_try_ok_3(self):
        # try_ok message with no prop/supp block stored locally and message does contain a propose block
        try_ok = PaxosMessage('TRY_OK', 1)

        b = Block(1, GENESIS.block_id, ['a'], 1)
        b.depth = 1

        try_ok.supp_block = b.block_id
        try_ok.prop_block = b.block_id

        self.node.c_request_seq = 1
        self.node.c_new_block = b
        self.node.c_votes = 5

        self.node.broadcast = MagicMock()
        self.node.blocktree.nodes.update({b.block_id: b})
        self.node.receive_paxos_message(try_ok, None)

        assert self.node.broadcast.called
        assert self.node.c_prop_block == b

        obj = self.node.broadcast.call_args[0][0]
        assert obj.com_block == b.block_id

    def test_receive_paxos_message_propose(self):
        propose = PaxosMessage('PROPOSE', 1)

        b = Block(1, GENESIS.block_id, ['a'], 1)
        b.depth = 1

        propose.new_block = GENESIS.block_id
        propose.com_block = GENESIS.block_id

        self.node.respond = MagicMock()
        self.node.receive_paxos_message(propose, 1)

        assert self.node.respond.called
        assert self.node.s_prop_block.block_id == propose.com_block
        assert self.node.s_supp_block.block_id == propose.new_block

    def test_receive_paxos_message_propose_ack(self):
        propose_ack = PaxosMessage('PROPOSE_ACK', 1)

        b = Block(1, GENESIS.block_id, ['a'], 1)
        b.depth = 1

        propose_ack.com_block = b.block_id

        self.node.c_request_seq = 1
        self.node.c_votes = 5
        self.node.blocktree.nodes.update({b.block_id: b})

        self.node.broadcast = MagicMock()
        self.node.commit = MagicMock()
        self.node.receive_paxos_message(propose_ack, None)

        assert self.node.broadcast.called

        obj = self.node.broadcast.call_args[0][0]
        assert obj.com_block == propose_ack.com_block

    def test_create_block(self):
        # create a blocktree and add blocks to it
        b1 = Block(1, GENESIS.block_id, [Transaction(1, 'a', 1)], 1)
        b2 = Block(2, GENESIS.block_id, [Transaction(1, 'a', 2)], 2)
        b3 = Block(3, b2.block_id, [Transaction(1, 'a', 3)], 3)
        b4 = Block(4, b3.block_id, [Transaction(1, 'a', 4)], 4)
        b5 = Block(5, b2.block_id, [Transaction(1, 'a', 5)], 5)

        self.node.blocktree.add_block(b1)
        self.node.blocktree.add_block(b2)
        self.node.blocktree.add_block(b3)
        self.node.blocktree.add_block(b4)
        self.node.blocktree.add_block(b5)

        self.node.blocktree.head_block = b4

        self.node.new_txs = [Transaction(1, 'a', 6), 6]

        c = self.node.create_block()
        assert len(self.node.new_txs) == 0
        assert self.node.blocktree.nodes.get(c.block_id) == c

    def test_reach_genesis_block(self):

        b1 = Block(1, GENESIS.block_id, [Transaction(1, 'a', 1)], 1)
        b2 = Block(2, GENESIS.block_id, [Transaction(1, 'a', 2)], 2)
        b3 = Block(3, b2.block_id, [Transaction(1, 'a', 3)], 3)
        b4 = Block(4, b3.block_id, [Transaction(1, 'a', 4)], 4)
        b5 = Block(5, b2.block_id, [Transaction(1, 'a', 5)], 5)

        self.node.blocktree.add_block(b1)
        self.node.blocktree.add_block(b2)
        self.node.blocktree.add_block(b3)
        self.node.blocktree.add_block(b4)
        self.node.blocktree.add_block(b5)

        assert self.node.reach_genesis_block(b5)

        b = Block(1, 1234, [Transaction(1, 'a', 6)], 6)

        self.node.broadcast = MagicMock()
        self.node.reach_genesis_block(b)

        assert self.node.broadcast.called

    def test_receive_request_blocks_message(self):
        b1 = Block(1, GENESIS.block_id, [Transaction(1, 'a', 1)], 1)
        b2 = Block(2, GENESIS.block_id, [Transaction(1, 'a', 2)], 2)
        b3 = Block(3, b2.block_id, [Transaction(1, 'a', 3)], 3)
        b4 = Block(4, b3.block_id, [Transaction(1, 'a', 4)], 4)
        b5 = Block(5, b2.block_id, [Transaction(1, 'a', 5)], 5)

        self.node.blocktree.add_block(b1)
        self.node.blocktree.add_block(b2)
        self.node.blocktree.add_block(b3)
        self.node.blocktree.add_block(b4)
        self.node.blocktree.add_block(b5)

        req = RequestBlockMessage(b4.block_id)

        self.node.respond = MagicMock()
        self.node.receive_request_blocks_message(req, None)

        assert self.node.respond.called

    def test_move_to_block(self):
        b1 = Block(1, GENESIS.block_id, [Transaction(1, 'a', 1)], 1)
        b2 = Block(2, GENESIS.block_id, [Transaction(2, 'a', 2)], 2)
        b3 = Block(3, b2.block_id, [Transaction(3, 'a', 3)], 3)
        b4 = Block(4, b3.block_id, [Transaction(4, 'a', 4)], 4)
        b5 = Block(5, b2.block_id, [Transaction(5, 'a', 5)], 5)
        b6 = Block(6, b4.block_id, [Transaction(6, 'a', 6)], 6)

        self.node.blocktree.add_block(b1)
        self.node.blocktree.add_block(b2)
        self.node.blocktree.add_block(b3)
        self.node.blocktree.add_block(b4)
        self.node.blocktree.add_block(b5)
        self.node.blocktree.add_block(b6)

        self.node.blocktree.head_block = b4

        old = self.node.blocktree.head_block
        # should both have no effect
        self.node.move_to_block(b3)
        self.node.move_to_block(b4)
        assert self.node.blocktree.head_block == old

        self.node.move_to_block(b6)
        assert self.node.blocktree.head_block == b6

        self.node.broadcast = MagicMock()
        self.node.move_to_block(b1)

        assert self.node.broadcast.called
        assert self.node.blocktree.head_block == b1

    def test_receive_transaction(self):
        txn = Transaction(0, 'a', 1)

        # test timeout
        clock = task.Clock()
        # must use a different reactor for testing
        self.node.reactor = clock
        self.node.timeout_over = MagicMock()
        self.node.receive_transaction(txn)
        clock.advance(50)

        assert self.node.timeout_over.called

    def test_receive_pong_message(self):
        pong = PongMessage(time.time())
        self.node.receive_pong_message(pong, 'a')

        assert self.node.rtts.get('a') is not None

    def test_timeout_over(self):
        # create a blocktree and add blocks to it
        b1 = Block(1, GENESIS.block_id, [Transaction(1, 'a', 1)], 1)
        b2 = Block(2, GENESIS.block_id, [Transaction(1, 'a', 2)], 2)
        b3 = Block(3, b2.block_id, [Transaction(1, 'a', 3)], 3)
        b4 = Block(4, b3.block_id, [Transaction(1, 'a', 4)], 4)
        b5 = Block(5, b2.block_id, [Transaction(1, 'a', 5)], 5)

        self.node.blocktree.add_block(b1)
        self.node.blocktree.add_block(b2)
        self.node.blocktree.add_block(b3)
        self.node.blocktree.add_block(b4)
        self.node.blocktree.add_block(b5)

        self.node.blocktree.head_block = b4

        txn = Transaction(1, 'a', 1)
        self.node.new_txs = [txn]
        self.node.broadcast = MagicMock()
        self.node.state = 0

        clock = task.Clock()
        self.node.reactor = clock
        self.node.timeout_over(txn)
        clock.advance(50)

        assert self.node.broadcast.called
        obj = self.node.broadcast.call_args[0][0]
        assert obj.last_committed_block == self.node.blocktree.committed_block.block_id
