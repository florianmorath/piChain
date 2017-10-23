from twisted.internet import reactor
import PaxosNode

"""
    Initialize a paxos node. 
    Parse port on which the node should listen from input or config file. 
"""

# create a paxos node which just listens on the given port
reactor.listenTCP(8001, PaxosNode.PaxosNodeFactory(4))

reactor.run()
