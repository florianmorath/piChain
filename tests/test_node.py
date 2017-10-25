import pytest
from unittest import TestCase
from piChain.PaxosLogic import PaxosMessage, Node, GENESIS, Block
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
        with pytest.raises(NotImplementedError):
            node.receive_paxos_message(try_msg)

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

        with pytest.raises(NotImplementedError):
            node.receive_paxos_message(try_ok)

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

        with pytest.raises(NotImplementedError):
            node.receive_paxos_message(try_ok)

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

        with pytest.raises(NotImplementedError):
            node.receive_paxos_message(try_ok)