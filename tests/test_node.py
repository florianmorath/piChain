from unittest import TestCase
from unittest.mock import MagicMock

from piChain.PaxosLogic import PaxosMessage, Node, GENESIS, Block, Transaction, Blocktree, RequestBlockMessage
from piChain.PaxosNetwork import PaxosNodeFactory


class TestNode(TestCase):

    def test_receive_paxos_message_try(self):
        # try message
        try_msg = PaxosMessage('TRY', 1)
        try_msg.last_committed_block = GENESIS

        b = Block(1, GENESIS.block_id, ['a'])
        b.depth = 1
        try_msg.new_block = b

        factory = PaxosNodeFactory()
        node = Node(10, factory)
        node.respond = MagicMock()

        node.receive_paxos_message(try_msg)
        assert node.respond.called
        assert node.s_max_block == b

        # obj = node.respond.call_args[0][0]
        # print('try_ok message = ', pprint(vars(obj)))
        # print('node vars = ', pprint(vars(node)))

    def test_receive_paxos_message_try_ok_1(self):
        # try_ok message with no prop/supp block stored locally and message does not contain a propose block
        try_ok = PaxosMessage('TRY_OK', 1)

        factory = PaxosNodeFactory()
        b = Block(1, GENESIS.block_id, ['a'])
        b.depth = 1

        node = Node(10, factory)
        node.c_request_seq = 1
        node.c_new_block = b
        node.c_votes = 5
        node.broadcast = MagicMock()
        node.receive_paxos_message(try_ok)

        assert node.broadcast.called
        assert node.c_com_block == node.c_new_block

    def test_receive_paxos_message_try_ok_2(self):
        # try_ok message with prop/supp block stored locally and message does not contain a propose block
        try_ok = PaxosMessage('TRY_OK', 1)

        factory = PaxosNodeFactory()
        b = Block(1, GENESIS.block_id, ['a'])
        b.depth = 1

        node = Node(10, factory)
        node.c_request_seq = 1
        node.c_new_block = b
        node.c_votes = 5
        node.c_supp_block = GENESIS
        node.c_prop_block = GENESIS

        node.broadcast = MagicMock()
        node.receive_paxos_message(try_ok)

        assert node.broadcast.called
        assert node.c_supp_block == GENESIS

    def test_receive_paxos_message_try_ok_3(self):
        # try_ok message with no prop/supp block stored locally and message does contain a propose block
        try_ok = PaxosMessage('TRY_OK', 1)

        factory = PaxosNodeFactory()
        b = Block(1, GENESIS.block_id, ['a'])
        b.depth = 1

        try_ok.supp_block = b
        try_ok.prop_block = b

        node = Node(10, factory)
        node.c_request_seq = 1
        node.c_new_block = b
        node.c_votes = 5

        node.broadcast = MagicMock()
        node.receive_paxos_message(try_ok)

        assert node.broadcast.called
        assert node.c_prop_block == b

        obj = node.broadcast.call_args[0][0]
        assert obj.com_block == b

    def test_receive_paxos_message_propose(self):
        propose = PaxosMessage('PROPOSE', 1)

        factory = PaxosNodeFactory()
        b = Block(1, GENESIS.block_id, ['a'])
        b.depth = 1

        propose.new_block = GENESIS
        propose.com_block = GENESIS

        node = Node(10, factory)
        node.respond = MagicMock()
        node.receive_paxos_message(propose)

        assert node.respond.called
        assert node.s_prop_block == propose.com_block
        assert node.s_supp_block == propose.new_block

    def test_receive_paxos_message_propose_ack(self):
        propose_ack = PaxosMessage('PROPOSE_ACK', 1)

        factory = PaxosNodeFactory()
        b = Block(1, GENESIS.block_id, ['a'])
        b.depth = 1

        propose_ack.com_block = b

        node = Node(10, factory)
        node.c_request_seq = 1
        node.c_votes = 5

        node.broadcast = MagicMock()
        node.receive_paxos_message(propose_ack)

        assert node.broadcast.called

        obj = node.broadcast.call_args[0][0]
        assert obj.com_block == propose_ack.com_block

    def test_receive_transaction(self):
        txn = Transaction(0, 'a')

        factory = PaxosNodeFactory()
        node = Node(10, factory)
        node.receive_transaction(txn)
        # TODO: test timeout

    def test_create_block(self):
        # create a blocktree and add blocks to it
        bt = Blocktree()
        b1 = Block(1, GENESIS.block_id, [Transaction(1, 'a')])
        b2 = Block(2, GENESIS.block_id, [Transaction(1, 'a')])
        b3 = Block(3, b2.block_id, [Transaction(1, 'a')])
        b4 = Block(4, b3.block_id, [Transaction(1, 'a')])
        b5 = Block(5, b2.block_id, [Transaction(1, 'a')])

        bt.add_block(b1)
        bt.add_block(b2)
        bt.add_block(b3)
        bt.add_block(b4)
        bt.add_block(b5)

        bt.head_block = b4

        factory = PaxosNodeFactory()
        node = Node(10, factory)
        node.new_txs = [Transaction(1, 'a')]
        node.blocktree = bt

        c = node.create_block()
        assert len(node.new_txs) == 0
        assert node.blocktree.nodes.get(c.block_id) == c

    def test_reach_genesis_block(self):
        bt = Blocktree()
        b1 = Block(1, GENESIS.block_id, [Transaction(1, 'a')])
        b2 = Block(2, GENESIS.block_id, [Transaction(1, 'a')])
        b3 = Block(3, b2.block_id, [Transaction(1, 'a')])
        b4 = Block(4, b3.block_id, [Transaction(1, 'a')])
        b5 = Block(5, b2.block_id, [Transaction(1, 'a')])

        bt.add_block(b1)
        bt.add_block(b2)
        bt.add_block(b3)
        bt.add_block(b4)
        bt.add_block(b5)

        factory = PaxosNodeFactory()
        node = Node(10, factory)
        node.blocktree = bt

        assert node.reach_genesis_block(b5)

        b = Block(1, 1234, [Transaction(1, 'a')])

        node.broadcast = MagicMock()
        node.reach_genesis_block(b)

        assert node.broadcast.called

    def test_receive_request_blocks_message(self):
        bt = Blocktree()
        b1 = Block(1, GENESIS.block_id, [Transaction(1, 'a')])
        b2 = Block(2, GENESIS.block_id, [Transaction(1, 'a')])
        b3 = Block(3, b2.block_id, [Transaction(1, 'a')])
        b4 = Block(4, b3.block_id, [Transaction(1, 'a')])
        b5 = Block(5, b2.block_id, [Transaction(1, 'a')])

        bt.add_block(b1)
        bt.add_block(b2)
        bt.add_block(b3)
        bt.add_block(b4)
        bt.add_block(b5)

        factory = PaxosNodeFactory()
        node = Node(10, factory)
        node.blocktree = bt

        req = RequestBlockMessage(b4.block_id)

        node.respond = MagicMock()
        node.receive_request_blocks_message(req)

        assert node.respond.called

    def test_move_to_block(self):
        bt = Blocktree()
        b1 = Block(1, GENESIS.block_id, [Transaction(1, 'a')])
        b2 = Block(2, GENESIS.block_id, [Transaction(2, 'a')])
        b3 = Block(3, b2.block_id, [Transaction(3, 'a')])
        b4 = Block(4, b3.block_id, [Transaction(4, 'a')])
        b5 = Block(5, b2.block_id, [Transaction(5, 'a')])
        b6 = Block(6, b4.block_id, [Transaction(6, 'a')])

        bt.add_block(b1)
        bt.add_block(b2)
        bt.add_block(b3)
        bt.add_block(b4)
        bt.add_block(b5)
        bt.add_block(b6)

        bt.head_block = b4

        factory = PaxosNodeFactory()
        node = Node(10, factory)
        node.blocktree = bt

        old = node.blocktree.head_block
        # should both have no effect
        node.move_to_block(b3)
        node.move_to_block(b4)
        assert node.blocktree.head_block == old

        node.move_to_block(b6)
        assert node.blocktree.head_block == b6

        node.broadcast = MagicMock()
        node.move_to_block(b1)

        assert node.broadcast.called
        assert node.blocktree.head_block == b1
