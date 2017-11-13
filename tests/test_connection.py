from twisted.trial import unittest
from twisted.test import proto_helpers
import json

from piChain.PaxosNetwork import ConnectionManager

import logging
logging.disable(logging.CRITICAL)


class TestConnection(unittest.TestCase):

    def setUp(self):
        """Will be called by unittest before each test method and is used for setup purposes.

        """
        self.node_id = 'a60c0bc6-b85a-47ad-abaa-a59e35822de2'
        self.factory = ConnectionManager(self.node_id)
        self.proto = self.factory.buildProtocol(('localhost', 0))

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
