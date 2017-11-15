from twisted.trial import unittest
from twisted.test import proto_helpers
import json

from unittest.mock import MagicMock
from piChain.PaxosLogic import Node
from piChain.messages import Transaction, RequestBlockMessage, Block, RespondBlockMessage, PaxosMessage


class TestConnection(unittest.TestCase):

    def setUp(self):
        """Will be called by unittest before each test method and is used for setup purposes.

        """
        node_id = 'a60c0bc6-b85a-47ad-abaa-a59e35822de2'
        self.node = Node(0, 3, node_id)
        self.proto = self.node.buildProtocol(('localhost', 0))

        # mock the transport -> we do not setup a real connection
        self.transport = proto_helpers.StringTransport()
        self.proto.makeConnection(self.transport)

    def test_handshake(self):
        """ Test receipt of a handshake message.

        """
        peer_node_id = 'b5564ec6-fd1d-481a-b68b-9b49a0ddd38b'
        s = json.dumps({'msg_type': 'HEL', 'nodeid': peer_node_id})
        self.proto.lineReceived(s)

        self.assertEqual(self.proto.peer_node_id, peer_node_id)
        self.assertIn(peer_node_id, self.proto.connection_manager.peers)

        msg = json.loads(self.transport.value())
        self.assertEqual(msg['msg_type'], 'ACK')

    def test_handshake_ack(self):
        """ Test receipt of a handshake acknowledgement message.

        """
        peer_node_id = 'b5564ec6-fd1d-481a-b68b-9b49a0ddd38b'
        s = json.dumps({'msg_type': 'ACK', 'nodeid': peer_node_id})
        self.proto.lineReceived(s)

        self.assertEqual(self.proto.peer_node_id, peer_node_id)
        self.assertIn(peer_node_id, self.proto.connection_manager.peers)

        self.assertEqual(self.transport.value(), b'')

    def test_rqb(self):
        """Test receipt of a RequestBlockMessage.

        """
        self.node.receive_request_blocks_message = MagicMock()

        rbm = RequestBlockMessage(3)
        s = rbm.serialize()
        self.proto.lineReceived(s)

        self.assertTrue(self.node.receive_request_blocks_message.called)
        obj = self.node.receive_request_blocks_message.call_args[0][0]
        self.assertEqual(type(obj), RequestBlockMessage)
        self.assertEqual(obj.block_id, 3)

    def test_txn(self):
        """Test receipt of a Transaction.

        """
        self.node.receive_transaction = MagicMock()

        txn = Transaction(0, 'command1')
        s = txn.serialize()
        self.proto.lineReceived(s)

        self.assertTrue(self.node.receive_transaction.called)
        obj = self.node.receive_transaction.call_args[0][0]
        self.assertEqual(type(obj), Transaction)
        self.assertEqual(obj, txn)

    def test_blk(self):
        """Test receipt of a Block.

        """
        self.node.receive_block = MagicMock()

        txn1 = Transaction(0, 'command1')
        txn2 = Transaction(0, 'command2')
        block = Block(0, 0, [txn1, txn2])
        s = block.serialize()
        self.proto.lineReceived(s)

        self.assertTrue(self.node.receive_block.called)
        obj = self.node.receive_block.call_args[0][0]
        self.assertEqual(type(obj), Block)
        self.assertEqual(obj.txs[0], txn1)

    def test_rsp(self):
        """Test receipt of a RespondBlockMessage.

        """
        self.node.receive_respond_blocks_message = MagicMock()

        txn1 = Transaction(0, 'command1')
        txn2 = Transaction(0, 'command2')
        block = Block(0, 0, [txn1, txn2])

        txn3 = Transaction(0, 'command3')
        block2 = Block(1, 1, [txn1, txn3])

        rsb = RespondBlockMessage([block, block2])

        s = rsb.serialize()
        self.proto.lineReceived(s)

        self.assertTrue(self.node.receive_respond_blocks_message.called)
        obj = self.node.receive_respond_blocks_message.call_args[0][0]
        self.assertEqual(type(obj), RespondBlockMessage)
        self.assertEqual(obj.blocks[0].txs[0], txn1)

    def test_pam(self):
        """Test receipt of a PaxosMessage.

        """
        self.node.receive_paxos_message = MagicMock()

        txn1 = Transaction(0, 'command1')
        txn2 = Transaction(0, 'command2')
        block = Block(0, 0, [txn1, txn2])

        txn3 = Transaction(0, 'command3')
        block2 = Block(1, 1, [txn1, txn3])

        pam = PaxosMessage('TRY', 2)
        pam.new_block = block
        pam.last_committed_block = block2

        s = pam.serialize()
        self.proto.lineReceived(s)

        self.assertTrue(self.node.receive_paxos_message.called)
        obj = self.node.receive_paxos_message.call_args[0][0]
        self.assertEqual(type(obj), PaxosMessage)
        self.assertEqual(obj.new_block.txs[0], txn1)
        self.assertEqual(obj.last_committed_block.txs[1], txn3)

    def test_broadcast(self):
        # setup another connection
        proto2 = self.node.buildProtocol(('localhost', 2))
        transport2 = proto_helpers.StringTransport()
        proto2.makeConnection(transport2)

        # peer 1 connects/sends hello handshake
        s = json.dumps({'msg_type': 'HEL', 'nodeid': 'b5564ec6-fd1d-481a-b68b-9b49a0ddd38b'})
        self.proto.lineReceived(s.encode())

        # peer 2 connects/sends hello handshake
        s = json.dumps({'msg_type': 'HEL', 'nodeid': 'c5564ec6-fd1d-481a-b68b-9b49a0ddd38b'})
        proto2.lineReceived(s.encode())

        # clear the transport
        self.proto.transport.clear()
        proto2.transport.clear()

        rbm = RequestBlockMessage(3)
        self.node.broadcast(rbm)

        s = json.loads(self.proto.transport.value())
        obj = RequestBlockMessage.unserialize(s)

        s2 = json.loads(proto2.transport.value())
        obj2 = RequestBlockMessage.unserialize(s2)

        self.assertEqual(rbm.block_id, obj.block_id)
        self.assertEqual(rbm.block_id, obj2.block_id)

    def test_respond(self):
        rbm = RequestBlockMessage(3)
        self.node.respond(rbm, self.proto)

        s = json.loads(self.proto.transport.value())
        obj = RequestBlockMessage.unserialize(s)

        self.assertEqual(rbm.block_id, obj.block_id)
