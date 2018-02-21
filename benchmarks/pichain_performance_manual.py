"""This module is used to test the performance of the piChain package. It connect to a database node instance and runs a
predefined number of seconds. Each second it sends a predefined number of transactions. After all transactions have been
committed, the time elapsed is computed and printed to the standard output.

Note: This script requires already running distributed_db processes (see module examples/distributed_db.py) where a
process listens on (localhost: 8000) for connections.
Note: set TESTING to False inside config.py to reach optimal performance.
"""

import time

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor
from twisted.internet.task import deferLater
from twisted.protocols.basic import LineReceiver


# Number of seconds, the script will send txns
ITERATIONS = 30
# Requests per second
RPS = 8000
# Keeps track of how many transactions have been committed
txn_count = 0
# Variables used for timing
start_time = None
end_time = None
started = False


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
        """Called once connection with node has been made. This initiates the process of txns beeing send. It will call
        each second `send_batch()` which will send a batch of transactions. """
        global started
        global start_time

        if not started:
            start_time = time.time()
            started = True

        for i in range(0, ITERATIONS):
            deferLater(reactor, i, self.send_batch, i)

    def send_batch(self, i):
        """Sends a predefined number (= RPS) of transactions as a batch to the node."""
        print('start iteration %s' % str(i))
        for j in range(0, RPS):
            self.send_msg(i, j)
        print('iteration %s finished' % str(i))
        print('sleep')

    def send_msg(self, i, j):
        msg = 'put k%i_%i v' % (i, j)
        self.sendLine(msg.encode())


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
