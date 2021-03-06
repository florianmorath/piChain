"""Test the receipt of message objects (defined in messages.py) and the broadcast and respond functionality implemented
in the PaxosNetwork module. """

import json
import time
import logging

from twisted.trial import unittest
from twisted.test import proto_helpers
from unittest.mock import MagicMock

from piChain.PaxosLogic import Node
from piChain.messages import Transaction, RequestBlockMessage, Block, RespondBlockMessage, PaxosMessage, PongMessage, \
    PingMessage

logging.disable(logging.CRITICAL)


class TestConnection(unittest.TestCase):

    def setUp(self):
        """Will be called by unittest before each test method and is used for setup purposes.
        """
        peers = {
            '0': {'ip': '127.0.0.1', 'port': 7982},
            '1': {'ip': '127.0.0.1', 'port': 7981},
            '2': {'ip': '127.0.0.1', 'port': 7980}
        }
        self.node = Node(0, peers)
        self.node.blocktree.db = MagicMock()
        self.proto = self.node.buildProtocol(('localhost', 0))
        self.proto.lc_ping = MagicMock()

        # mock the transport -> we do not setup a real connection
        self.transport = proto_helpers.StringTransport()
        self.proto.makeConnection(self.transport)

    def test_handshake(self):
        """ Test receipt of a handshake message.
        """
        peer_node_id = '0'
        s = json.dumps({'nodeid': peer_node_id})
        self.proto.stringReceived(b'HEL' + s.encode())

        self.assertEqual(self.proto.peer_node_id, peer_node_id)
        self.assertIn(peer_node_id, self.proto.connection_manager.peers)

        self.assertEqual(b'ACK{"nodeid": "0"}', self.transport.value()[4:])

    def test_handshake_ack(self):
        """ Test receipt of a handshake acknowledgement message.
        """
        peer_node_id = '0'
        s = json.dumps({'nodeid': peer_node_id})
        self.proto.stringReceived(b'ACK' + s.encode())

        self.assertEqual(self.proto.peer_node_id, peer_node_id)
        self.assertIn(peer_node_id, self.proto.connection_manager.peers)

        self.assertEqual(self.transport.value(), b'')

    def test_rqb(self):
        """Test receipt of a RequestBlockMessage.
        """
        self.node.receive_request_blocks_message = MagicMock()

        rbm = RequestBlockMessage(3)
        s = rbm.serialize()
        self.proto.stringReceived(s)

        self.assertTrue(self.node.receive_request_blocks_message.called)
        obj = self.node.receive_request_blocks_message.call_args[0][0]
        self.assertEqual(type(obj), RequestBlockMessage)
        self.assertEqual(obj.block_id, 3)

    def test_txn(self):
        """Test receipt of a Transaction.
        """
        self.node.receive_transaction = MagicMock()

        txn = Transaction(0, 'command1', 1)
        s = txn.serialize()
        self.proto.stringReceived(s)

        self.assertTrue(self.node.receive_transaction.called)
        obj = self.node.receive_transaction.call_args[0][0]
        self.assertEqual(type(obj), Transaction)
        self.assertEqual(obj, txn)

    def test_blk(self):
        """Test receipt of a Block.
        """
        self.node.receive_block = MagicMock()

        txn1 = Transaction(0, 'command1', 1)
        txn2 = Transaction(0, 'command2', 2)
        block = Block(0, 0, [txn1, txn2], 1)
        s = block.serialize()
        self.proto.stringReceived(s)

        self.assertTrue(self.node.receive_block.called)
        obj = self.node.receive_block.call_args[0][0]
        self.assertEqual(type(obj), Block)
        self.assertEqual(obj.txs[0], txn1)

    def test_rsp(self):
        """Test receipt of a RespondBlockMessage.
        """
        self.node.receive_respond_blocks_message = MagicMock()

        txn1 = Transaction(0, 'command1', 1)
        txn2 = Transaction(0, 'command2', 2)
        block = Block(0, 0, [txn1, txn2], 1)

        txn3 = Transaction(0, 'command3', 3)
        block2 = Block(1, 1, [txn1, txn3], 2)

        rsb = RespondBlockMessage([block, block2])

        s = rsb.serialize()
        self.proto.stringReceived(s)

        self.assertTrue(self.node.receive_respond_blocks_message.called)
        obj = self.node.receive_respond_blocks_message.call_args[0][0]
        self.assertEqual(type(obj), RespondBlockMessage)
        self.assertEqual(obj.blocks[0].txs[0], txn1)

    def test_pam(self):
        """Test receipt of a PaxosMessage.
        """
        self.node.receive_paxos_message = MagicMock()

        txn1 = Transaction(0, 'command1', 1)
        txn2 = Transaction(0, 'command2', 2)
        block = Block(0, 0, [txn1, txn2], 1)

        txn3 = Transaction(0, 'command3', 3)
        block2 = Block(1, 1, [txn1, txn3], 2)

        pam = PaxosMessage('TRY', 2)
        pam.new_block = block.block_id
        pam.last_committed_block = block2.block_id

        s = pam.serialize()
        self.proto.stringReceived(s)

        self.assertTrue(self.node.receive_paxos_message.called)
        obj = self.node.receive_paxos_message.call_args[0][0]
        self.assertEqual(type(obj), PaxosMessage)
        self.assertEqual(obj.new_block, block.block_id)
        self.assertEqual(obj.last_committed_block, block2.block_id)

    def test_PON(self):
        """Test receipt of a PongMessage.
        """
        self.node.receive_pong_message = MagicMock()

        pong = PongMessage(time.time())
        s = pong.serialize()
        self.proto.stringReceived(s)

        self.assertTrue(self.node.receive_pong_message.called)

    def test_PIN(self):
        """Test receipt of a PingMessage.
        """
        timestamp = time.time()
        ping = PingMessage(timestamp)
        s = ping.serialize()
        self.proto.stringReceived(s)

        print(self.proto.transport.value())
        obj = PongMessage.unserialize(self.proto.transport.value()[4:])
        self.assertEqual(obj.time, timestamp)

    def test_broadcast(self):
        # setup another connection
        proto2 = self.node.buildProtocol(('localhost', 2))
        proto2.lc_ping = MagicMock()
        transport2 = proto_helpers.StringTransport()
        proto2.makeConnection(transport2)

        # peer 1 connects/sends hello handshake
        s = json.dumps({'nodeid': '1'})
        self.proto.stringReceived(b'HEL' + s.encode())

        # peer 2 connects/sends hello handshake
        s = json.dumps({'nodeid': '2'})
        proto2.stringReceived(b'HEL' + s.encode())

        # clear the transport
        self.proto.transport.clear()
        proto2.transport.clear()

        rbm = RequestBlockMessage(3)
        self.node.broadcast(rbm, 'RQB')

        obj = RequestBlockMessage.unserialize(self.proto.transport.value()[4:])

        obj2 = RequestBlockMessage.unserialize(proto2.transport.value()[4:])

        self.assertEqual(rbm.block_id, obj.block_id)
        self.assertEqual(rbm.block_id, obj2.block_id)

    def test_respond(self):
        rbm = RequestBlockMessage(3)
        self.node.respond(rbm, self.proto)

        obj = RequestBlockMessage.unserialize(self.proto.transport.value()[4:])

        self.assertEqual(rbm.block_id, obj.block_id)
