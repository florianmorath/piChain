from twisted.internet import protocol

'''
       This class implements the underling communication between paxos nodes 
       i.e defines how a paxos node handles an incoming message. 
'''

class PaxosNode(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def dataReceived(self, data):
        print("Received data: ", data)

    def connectionMade(self):
        print("Connection made")


class PaxosNodeFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        return PaxosNode(self)
