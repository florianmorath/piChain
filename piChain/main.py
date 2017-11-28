from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor, task
from twisted.internet.task import deferLater
from twisted.python import log

from piChain.PaxosLogic import Node
from piChain.config import peers
from tests.integration_scenarios import IntegrationScenarios

import argparse
import logging


def main():
    """
    Entry point. First starts a server listening on a port given in confg file. Then connect to other peers.

    """
    parser = argparse.ArgumentParser()

    # start server
    parser.add_argument("node_index", help='Index of node in config.py')
    args = parser.parse_args()
    node_index = args.node_index

    node = Node(int(node_index))

    endpoint = TCP4ServerEndpoint(reactor, peers.get(node_index).get('port'))
    endpoint.listen(node)

    # "client part" -> connect to all servers -> add handshake callback
    node.reconnect_loop = task.LoopingCall(node.connect_to_nodes, node_index)
    logging.info('Connection synchronization start...')
    deferred = node.reconnect_loop.start(5, True)
    deferred.addErrback(log.err)

    # start the paxos algorithm with some test scenarios (test purpose -> will be deleted)
    deferLater(reactor, 11, IntegrationScenarios.scenario4, node)

    # start reactor
    logging.info('start reactor')
    reactor.run()


if __name__ == "__main__":
    main()
