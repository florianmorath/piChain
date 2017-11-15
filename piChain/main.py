from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor, task
from twisted.python import log
from piChain.PaxosLogic import Node
from piChain.config import peers

import argparse
import logging


def main():
    """
    Entry point. First starts a server listening on a port given in confg file. Then connects to other peers.

    """
    parser = argparse.ArgumentParser()

    # start server
    parser.add_argument("node_index", help='Index of node in config.py')
    args = parser.parse_args()
    node_index = args.node_index

    node = Node(int(node_index), len(peers), peers.get(node_index)[2])

    endpoint = TCP4ServerEndpoint(reactor, peers.get(node_index)[1])
    endpoint.listen(node)

    # "client part" -> connect to all servers -> add handshake callback
    node.reconnect_loop = task.LoopingCall(node.connect_to_nodes, node_index)
    logging.info('Connection synchronization start...')
    deferred = node.reconnect_loop.start(10, True)
    deferred.addErrback(log.err)

    # start reactor
    logging.info('start reactor')
    reactor.run()


if __name__ == "__main__":
    main()
