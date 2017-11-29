
from twisted.trial.unittest import TestCase
from subprocess import PIPE, Popen
from sys import stdout
from piChain.config import peers

import signal
import logging
logging.disable(logging.CRITICAL)


class NodeProcess:
    def __init__(self, name, *args):
        self.name = name
        self.proc = Popen(["pichain"] + list(args), stdout=PIPE, stderr=PIPE, universal_newlines=True)
        self.err_output = ""

    def wait_for_start(self):
        while "Connection setup finished" not in self.err_output:
            self.err_output += self.proc.stderr.read(10)

    def shutdown(self):
        self.proc.send_signal(signal.SIGINT)
        self.proc.wait(0.1)
        print("Node process %s terminated with code %i."
              % (self.name, self.proc.returncode))
        print("====================== stdout =======================")
        stdout.write(self.proc.stdout.read())
        print("====================== stderr =======================")
        stdout.write(self.err_output)
        stdout.write(self.proc.stderr.read())
        return self.proc.returncode


class TestMultiNode(TestCase):

    def setUp(self):
        self.procs = []

        for i in range(len(peers)):
            self.procs.append(NodeProcess("node %i" % i,
                                          str(i),           # node id
                                          "--test", str(0)  # test scenario number
                                          )
                              )

        # Wait for the nodes to startup
        # for proc in self.procs:
        #     proc.wait_for_start()

    def tearDown(self):
        # TODO: delete everything in leveldb -> rmtree

        if any(proc.shutdown() for proc in self.procs):
            raise Exception("Subprocess failed!")

    def test_scenarios(self):
        pass
