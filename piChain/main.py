from twisted.internet import reactor
from pichain.PaxosNode import PaxosNodeFactory

"""
    Initialize a paxos node. 
    Parse port on which the node should listen from input or config file. 
"""

# create a paxos node which just listens on the given port
reactor.listenTCP(8001, PaxosNodeFactory(4))

reactor.run()
