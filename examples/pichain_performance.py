from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet.task import deferLater

import time

ITERATIONS = 5
RPS = 110
txn_count = 0
started = False
start_time = None
end_time = None


class Connection(LineReceiver):

    def lineReceived(self, line):
        global start_time
        global end_time
        global txn_count

        print(line.decode())

        txn_count += 1
        if txn_count == RPS * ITERATIONS:
            end_time = time.time()
            elapsed_time = round(end_time - start_time, 3)
            print('elapsed time = %s' % str(elapsed_time))

    def rawDataReceived(self, data):
        pass

    def connectionMade(self):
        self.send_txns()

    def send_txns(self):
        global started
        global start_time

        if not started:
            start_time = time.time()
            started = True

        for i in range(0, ITERATIONS):
            deferLater(reactor, i, self.send_batch, i)

    def send_batch(self, i):
        print('start iteration %s' % str(i))
        for j in range(0, RPS):
            msg = 'put k%i_%i v' % (i, j)
            self.sendLine(msg.encode())
        print('iteration %s finished' % str(i))
        print('sleep')


class ClientFactory(ReconnectingClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def buildProtocol(self, addr):
        print('Connected.')
        print('Resetting reconnection delay')
        self.resetDelay()
        return Connection()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection.  Reason:', reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)


reactor.connectTCP('localhost', 8000, ClientFactory())
reactor.run()
