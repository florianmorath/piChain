"""This module computes the limit of the RPS rate for different cluster sizes and then plots the results.
Note: The test is based on local running nodes."""

import os
import shutil
import logging
import signal
import time
from sys import stdout
from subprocess import PIPE, Popen

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


cluster_size = 3
cluster_size_max = 7

RPS_MAX = []

logging.basicConfig(level=logging.DEBUG)


class NodeProcess:
    """
    Args:
        name (str): name of the node e.g node 1.
        args (str): positional arguments used as arguments to the main.py script.

    Attributes:
        proc (POpen): instance of POpen class representing a process.
    """
    def __init__(self, name, path, *args):
        self.name = name
        self.proc = Popen(["python", path] + list(args), stdout=PIPE, stderr=PIPE, universal_newlines=True)

    def shutdown(self):
        self.proc.send_signal(signal.SIGKILL)
        self.proc.wait(0.5)
        print('')
        print("==========")
        print("Node process %s terminated with code %i." % (self.name, self.proc.returncode))
        stdout.write(self.proc.stderr.read())
        return self.proc.returncode


def compute_rps_limit(c_size):
    global cluster_size

    # delete .pichain folder
    base_path = os.path.expanduser('~/.pichain')
    if os.path.exists(base_path):
        try:
            shutil.rmtree(base_path)
        except Exception as e:
            print(e)
            raise

    # start distributed_db processes
    db_procs = []
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/examples/distributed_db.py'
    for i in range(c_size):
        db_procs.append(NodeProcess("db node %i" % i, path, str(i), str(c_size)))
        time.sleep(0.1)

    time.sleep(1)

    # start automated performance test process
    path = os.path.dirname(os.path.abspath(__file__)) + '/pichain_performance_automated.py'
    performance_proc = NodeProcess("performance node", path)

    # sleep_time = 10000/step_size*running_time_per_RPS*try_count_per_RPS
    time.sleep(500)

    # terminate processes
    for node_proc in db_procs:
        node_proc.proc.terminate()
    performance_proc.proc.terminate()

    # extract outputs
    node_lines = performance_proc.proc.stdout.readlines()
    print("====================== stdout =======================")
    print('')
    print("==========")
    for line in node_lines:
        if 'piChain' in line:
            rps = [int(s) for s in line.split(' ') if s.isdigit()]
            RPS_MAX.append(rps[0])
        print(line)

    print("====================== stderr =======================")
    performance_proc.shutdown()
    for node_proc in db_procs:
        node_proc.shutdown()

    # start next round
    cluster_size += 1
    if cluster_size > cluster_size_max:
        return
    compute_rps_limit(cluster_size)


def main():
    global RPS_MAX
    compute_rps_limit(cluster_size)
    print(RPS_MAX)

    # make a plot
    cluster_list = [x for x in range(3, cluster_size_max + 1)]
    plt.ylabel('RPS')
    plt.xlabel('Cluster size')
    axes = plt.gca()
    axes.set_ylim([0, max(RPS_MAX)+1000])
    axes.xaxis.set_major_locator(MaxNLocator(integer=True))

    red_dot, = plt.plot(cluster_list, RPS_MAX, 'ro-')
    plt.legend([red_dot], ['200 bytes write request'])
    plt.show()


if __name__ == "__main__":
    main()
