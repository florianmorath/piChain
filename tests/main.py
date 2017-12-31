"""This script is used to be able to start paxos instances with the subproccesses module for testing purposes."""

import argparse
import logging

from twisted.internet import reactor
from twisted.internet.task import deferLater

from piChain.PaxosLogic import Node
from tests.integration_scenarios import IntegrationScenarios


def main():
    """
    Entry point. First starts a server listening on the given port. Then connect to other peers.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("node_index", type=int, help='Index of node')
    parser.add_argument("--test", dest='test_scenario', type=int)
    parser.add_argument("--clustersize", dest='clustersize', type=int)

    args = parser.parse_args()
    node_index = args.node_index
    logging.debug('start node %s', str(node_index))

    peers = {
        '0': {'ip': '127.0.0.1', 'port': 7982},
        '1': {'ip': '127.0.0.1', 'port': 7981},
        '2': {'ip': '127.0.0.1', 'port': 7980}
    }

    if args.clustersize is not None:
        peers = {}
        for i in range(0, args.clustersize):
            peers.update({str(i): {'ip': '127.0.0.1', 'port': (7000 + i)}})

    node = Node(node_index, peers)
    node.start_server()

    if args.test_scenario is not None:
        # start the paxos algorithm with given test scenario
        scenario = 'scenario' + str(args.test_scenario)
        deferLater(reactor, 1.5, getattr(IntegrationScenarios, scenario), node)

    # start reactor
    logging.info('start reactor')
    reactor.run()


if __name__ == "__main__":
    main()
