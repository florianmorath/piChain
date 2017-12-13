"""Integration test module. Can be subclassed by concrete TestCase classes.
note: currently the tests only work locally i.e all nodes must have IP address 127.0.0.1
"""

from twisted.trial.unittest import TestCase
from subprocess import PIPE, Popen
from sys import stdout
from piChain.config import peers

import signal
import shutil
import os


class NodeProcess:
    def __init__(self, name, *args):
        self.name = name
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/piChain/main.py'
        self.proc = Popen(["python", path] + list(args), stdout=PIPE, stderr=PIPE, universal_newlines=True)

    def shutdown(self):
        self.proc.send_signal(signal.SIGINT)
        self.proc.wait(1)
        print('')
        print("==========")
        print("Node process %s terminated with code %i." % (self.name, self.proc.returncode))

        stdout.write(self.proc.stderr.read())
        return self.proc.returncode


class MultiNodeTest(TestCase):

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
            raise Exception("Subprocess failed!")

        # delete level db on disk
        base_path = os.path.expanduser('~/.pichain')
        if os.path.exists(base_path):
            try:
                shutil.rmtree(base_path)
            except Exception as e:
                print(e)
                raise

    def start_processes_with_test_scenario(self, scenario_number):
        for i in range(len(peers)):
            self.procs.append(NodeProcess("node %i" % i, str(i), "--test", str(scenario_number)))

    def start_single_process_with_test_scenario(self, scenario_number, i):
        self.procs.append(NodeProcess("node %i" % i, str(i), "--test", str(scenario_number)))

    def terminate_processes(self):
        for node_proc in self.procs:
            node_proc.proc.terminate()

    def terminate_single_process(self, i):
        node_name = 'node ' + str(i)
        for node_proc in self.procs:
            if node_proc.name == node_name:
                node_proc.proc.terminate()
                print("====================== stderr =======================")
                node_proc.shutdown()

    def extract_committed_blocks_single_process(self, i):
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
