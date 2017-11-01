from twisted.internet import reactor
from piChain.PaxosNetwork import ConnectionManager

"""
    Initialize a paxos node. 
    Parse port on which the node should listen from input or config file. 
"""

# create a paxos node which just listens on the given port
reactor.listenTCP(8001, ConnectionManager())

reactor.run()
