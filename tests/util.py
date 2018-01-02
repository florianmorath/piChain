"""Integration test utility module. Consist of helper methods and classes that can be used by all integration test
classes.
"""

import signal
import shutil
import os
from sys import stdout
from subprocess import PIPE, Popen

from twisted.trial.unittest import TestCase


class NodeProcess:
    """
    Args:
        name (str): name of the node e.g node 1.
        args (str): positional arguments used as arguments to the main.py script.

    Attributes:
        proc (POpen): instance of POpen class representing a process.
    """
    def __init__(self, name, *args):
        self.name = name
        path = os.path.dirname(os.path.abspath(__file__)) + '/main.py'
        self.proc = Popen(["python", path] + list(args), stdout=PIPE, stderr=PIPE, universal_newlines=True)

    def shutdown(self):
        self.proc.send_signal(signal.SIGINT)
        self.proc.wait()
        print('')
        print("==========")
        print("Node process %s terminated with code %i." % (self.name, self.proc.returncode))
        stdout.write(self.proc.stderr.read())
        return self.proc.returncode


class MultiNodeTest(TestCase):
    """Can be subclassed by concrete TestCase classes."""

    def setUp(self):
        self.procs = []

        # delete level db on disk
        base_path = os.path.expanduser('~/.pichain')
        if os.path.exists(base_path):
            try:
                shutil.rmtree(base_path)
            except Exception as e:
                print(e)
                raise

    def tearDown(self):
        print("====================== stderr =======================")
        if any(proc.shutdown() for proc in self.procs):
            pass

        # delete level db on disk
        base_path = os.path.expanduser('~/.pichain')
        if os.path.exists(base_path):
            try:
                shutil.rmtree(base_path)
            except Exception as e:
                print(e)
                raise

    def start_processes_with_test_scenario(self, scenario_number, cluster_size):
        """
        Args:
            scenario_number (int): the scenario to be executed inside the integration_scenarios.py module.
            cluster_size (int): number of nodes used in the test scenario.
        """
        for i in range(cluster_size):
            self.procs.append(NodeProcess("node %i" % i, str(i), "--test", str(scenario_number), "--clustersize",
                                          str(cluster_size)))

    def start_single_process_with_test_scenario(self, scenario_number, i, cluster_size):
        """
        Args:
            scenario_number (int): the scenario to be executed inside the integration_scenarios.py module.
            i (int): index of node to be started inside a process.
            cluster_size (int): number of nodes used in the test scenario.
        """
        self.procs.append(NodeProcess("node %i" % i, str(i), "--test", str(scenario_number), "--clustersize",
                                      str(cluster_size)))

    def terminate_processes(self):
        for node_proc in self.procs:
            node_proc.proc.terminate()

    def terminate_single_process(self, i):
        """
        Args:
            i (int): index of node to be terminated.
        """
        node_name = 'node ' + str(i)
        for node_proc in self.procs:
            if node_proc.name == node_name:
                node_proc.proc.terminate()
                print("====================== stderr =======================")
                node_proc.shutdown()

    def extract_committed_blocks_single_process(self, i):
        """
        Args:
            i (int): index of node.
        """
        node_lines = []
        node_name = 'node ' + str(i)
        for node_proc in self.procs:
            if node_proc.name == node_name:
                node_lines = node_proc.proc.stdout.readlines()

        node_blocks = []

        print("====================== stdout =======================")
        print('')
        print("==========")
        print('node %s:' % i)
        for line in node_lines:
            print(line)
            if 'block =' in line:
                node_blocks.append(line)

        return node_blocks
