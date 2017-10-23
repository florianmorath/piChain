from twisted.internet import protocol
from PaxosProtocol import Node

"""
       This class implements the underling communication between paxos nodes 
       i.e defines how a paxos node handles an incoming message. 
"""


class PaxosNodeProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def dataReceived(self, data):
        print("Received data: ", data)

    def connectionMade(self):
        print("Connection made")
        # add self to peers if no connection to this peer yet

    def broadcast(self):
        for peer in self.factory.peers.items():
            if peer[1] != self:
                print('broadcast')
                # peer[1].transport.write(...)


class PaxosNodeFactory(protocol.ClientFactory):
    """ keeps consistent state among multiple PaxosNodeProtocol instances. """

    def __init__(self, n):
        self.node = Node(n)
        # dict: node id -> PaxosNodeProtocol (can be used to broadcast messages: self.factory.peers[data] = self)
        self.peers = {}

    def buildProtocol(self, addr):
        return PaxosNodeProtocol(self)
