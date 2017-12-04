
from twisted.trial.unittest import TestCase
from subprocess import PIPE, Popen
from sys import stdout
from piChain.config import peers

import signal
import time
import shutil
import os


class NodeProcess:
    def __init__(self, name, *args):
        self.name = name
        self.proc = Popen(["pichain"] + list(args), stdout=PIPE, stderr=PIPE, universal_newlines=True)

    def shutdown(self):
        self.proc.send_signal(signal.SIGINT)
        self.proc.wait(1)
        print("Node process %s terminated with code %i." % (self.name, self.proc.returncode))
        # print("====================== stdout =======================")
        # stdout.write(self.proc.stdout.read())
        print("====================== stderr =======================")
        stdout.write(self.proc.stderr.read())
        return self.proc.returncode


class TestMultiNode(TestCase):

    def setUp(self):
        self.procs = []

        # delete level db on disk
        base_path = os.path.expanduser('~/.pichain/DB')
        if os.path.exists(base_path):
            try:
                shutil.rmtree(base_path)
            except Exception as e:
                print(e)
                raise

    def tearDown(self):
        if any(proc.shutdown() for proc in self.procs):
            raise Exception("Subprocess failed!")

        # delete level db on disk
        base_path = os.path.expanduser('~/.pichain/DB')
        if os.path.exists(base_path):
            try:
                shutil.rmtree(base_path)
            except Exception as e:
                print(e)
                raise

    def start_processes_with_test_scenario(self, scenario_number):
        for i in range(len(peers)):
            self.procs.append(NodeProcess("node %i" % i, str(i), "--test", str(scenario_number)))

    def terminate_processes(self):
        for node_proc in self.procs:
            node_proc.proc.terminate()

    def extract_committed_blocks(self):
        for node_proc in self.procs:
            if node_proc.name == 'node 0':
                node0_lines = node_proc.proc.stdout.readlines()
            elif node_proc.name == 'node 1':
                node1_lines = node_proc.proc.stdout.readlines()
            elif node_proc.name == 'node 2':
                node2_lines = node_proc.proc.stdout.readlines()

        node0_blocks = []
        node1_blocks = []
        node2_blocks = []

        for line in node0_lines:
            if 'block =' in line:
                node0_blocks.append(line)

        for line in node1_lines:
            if 'block =' in line:
                node1_blocks.append(line)

        for line in node2_lines:
            if 'block =' in line:
                node2_blocks.append(line)

        return node0_blocks, node1_blocks, node2_blocks

    def test_scenario1(self):
        self.start_processes_with_test_scenario(1)
        time.sleep(1)
        self.terminate_processes()

        node0_blocks, node1_blocks, node2_blocks = self.extract_committed_blocks()

        assert len(node0_blocks) == 1
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario2(self):
        self.start_processes_with_test_scenario(2)
        time.sleep(1)
        self.terminate_processes()

        node0_blocks, node1_blocks, node2_blocks = self.extract_committed_blocks()

        assert len(node0_blocks) == 1
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario3(self):
        self.start_processes_with_test_scenario(3)
        time.sleep(1)
        self.terminate_processes()

        node0_blocks, node1_blocks, node2_blocks = self.extract_committed_blocks()

        assert len(node0_blocks) == 1
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario4(self):
        self.start_processes_with_test_scenario(4)
        time.sleep(2)
        self.terminate_processes()

        node0_blocks, node1_blocks, node2_blocks = self.extract_committed_blocks()

        assert len(node0_blocks) == 2
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario5(self):
        self.start_processes_with_test_scenario(4)
        time.sleep(2)
        self.terminate_processes()

        node0_blocks, node1_blocks, node2_blocks = self.extract_committed_blocks()

        assert len(node0_blocks) == 2
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks
