from twisted.internet import reactor
import Acceptor
import Proposer

'''
    Initialize a paxos node consisting of an acceptor and a proposer. 
    Parse proposer port and acceptor port from input or config file. 
'''

# create an acceptor which just listens on the given port
reactor.listenTCP(8001, Acceptor.AcceptorFactory())

# create a proposer which listens on the given port (to handle request messages)
reactor.listenTCP(8002, Proposer.ProposerFactory())


reactor.run()