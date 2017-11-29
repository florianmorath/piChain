
from twisted.internet import reactor
from twisted.internet.task import deferLater

from piChain.PaxosLogic import Node
from tests.integration_scenarios import IntegrationScenarios

import argparse
import logging


def tx_committed(commands):
    """Called once a block is committed.

    Args:
        commands (list): list of commands inside committed block (one per Transaction)

    """
    # for command in commands:
    #     logging.debug('command committed: %s', command)


def main():
    """
    Entry point. First starts a server listening on a port given in confg file. Then connect to other peers.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("node_index", type=int, help='Index of node in config.py')
    parser.add_argument("--test", dest='test_scenario', type=int)

    args = parser.parse_args()
    node_index = args.node_index
    logging.debug('start node %s', str(node_index))

    node = Node(node_index)
    node.tx_committed = tx_committed
    node.start_server()

    if args.test_scenario is not None:
        # start the paxos algorithm with given test scenario
        scenario = 'scenario' + str(args.test_scenario)
        deferLater(reactor, 5, getattr(IntegrationScenarios, scenario), node)

    # start reactor
    logging.info('start reactor')
    reactor.run()


if __name__ == "__main__":
    main()
