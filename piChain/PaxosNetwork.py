"""This class implements the networking between PaxosNodes.
"""
from twisted.internet import protocol
#from pichain.PaxosLogic import Node

class PaxosNodeProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def dataReceived(self, data):
        print("Received data: ", data)

    def connectionMade(self):
        print("Connection made")
        # add self to peers if no connection to this peer yet

    def broadcast(self, obj):
        for peer in self.factory.peers.items():
            if peer[1] != self:
                print('broadcast')
                # peer[1].transport.write(...)

    def respond(self, obj):
        """obj is an instance of type Message, Block or Transaction which will be responded to to the peer
        which has send the request. """


class PaxosNodeFactory(protocol.ClientFactory):
    """ keeps consistent state among multiple PaxosNodeProtocol instances. """

    def __init__(self, n):
        # self.node = Node(n)
        # dict: node id -> PaxosNode (can be used to broadcast messages: self.factory.peers[data] = self)
        self.peers = {}

    def buildProtocol(self, addr):
        return PaxosNodeProtocol(self)
