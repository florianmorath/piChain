
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
        print("====================== stdout =======================")
        stdout.write(self.proc.stdout.read())
        print("====================== stderr =======================")
        stdout.write(self.proc.stderr.read())
        return self.proc.returncode


class TestMultiNode(TestCase):

    def setUp(self):
        self.procs = []

        # delete level db on disk
        path = os.path.dirname(os.getcwd()) + '/DB/'
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(e)
                raise

    def tearDown(self):
        if any(proc.shutdown() for proc in self.procs):
            raise Exception("Subprocess failed!")

        # delete level db on disk
        path = os.path.dirname(os.getcwd()) + '/DB/'
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(e)
                raise

    def test_scenario2(self):
        for i in range(len(peers)):
            self.procs.append(NodeProcess("node %i" % i, str(i), "--test", str(2)))

        time.sleep(10)
        for node_proc in self.procs:
            node_proc.proc.terminate()

        for node_proc in self.procs:
            if node_proc.name == 'node 0':
                node0_stdout = node_proc.proc.stdout.read()
            elif node_proc.name == 'node 1':
                node1_stdout = node_proc.proc.stdout.read()
            elif node_proc.name == 'node 2':
                node2_stdout = node_proc.proc.stdout.read()

        assert node0_stdout == node1_stdout
        assert node1_stdout == node2_stdout
