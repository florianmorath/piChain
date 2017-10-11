from twisted.internet import protocol


class Acceptor(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def dataReceived(self, data):
        print("Received data: ", data)

    def connectionMade(self):
        print("Connection made")


class AcceptorFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Acceptor(self)
