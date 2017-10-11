from twisted.internet import protocol


class Proposer(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def dataReceived(self, data):
        print("Received data: ", data)

    def connectionMade(self):
        print("Connection made")


class ProposerFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        print("Connected")
        return Proposer(self)

