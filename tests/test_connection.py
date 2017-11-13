from twisted.trial import unittest
from twisted.test import proto_helpers
import json

from unittest.mock import MagicMock
from piChain.PaxosLogic import RequestBlockMessage, Node, Transaction


class TestConnection(unittest.TestCase):

    def setUp(self):
        """Will be called by unittest before each test method and is used for setup purposes.

        """
        self.node_id = 'a60c0bc6-b85a-47ad-abaa-a59e35822de2'
        self.node = Node(3, self.node_id)
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

    def test_RQB(self):
        """test receipt of a RequestBlockMessage.

        """

        self.node.receive_request_blocks_message = MagicMock()

        rbm = RequestBlockMessage(3)
        s = rbm.serialize()
        self.proto.lineReceived(s)

        self.assertTrue(self.node.receive_request_blocks_message.called)
        msg = self.node.receive_request_blocks_message.call_args[0][0]
        obj = RequestBlockMessage.unserialize(msg)
        self.assertEqual(type(obj), RequestBlockMessage)
        self.assertEqual(obj.block_id, 3)

    def test_TXN(self):
        """test receipt of a Transaction.

        """

        self.node.receive_transaction = MagicMock()

        txn = Transaction(0, 'command1')
        s = txn.serialize()
        self.proto.lineReceived(s)

        self.assertTrue(self.node.receive_transaction.called)
        msg = self.node.receive_transaction.call_args[0][0]
        obj = Transaction.unserialize(msg)
        self.assertEqual(type(obj), Transaction)
