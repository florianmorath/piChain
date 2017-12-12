"""Integration test: Test basic behavior of paxos nodes in a connected network and no node crashes occuring.

note: currently the tests only work locally i.e all nodes must have IP address 127.0.0.1
"""

from tests.util import MultiNodeTest

import time


class MultiNodeTestBasic(MultiNodeTest):

    def test_scenario1(self):
        self.start_processes_with_test_scenario(1)
        time.sleep(3)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 1
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario2(self):
        self.start_processes_with_test_scenario(2)
        time.sleep(3)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 1
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario3(self):
        self.start_processes_with_test_scenario(3)
        time.sleep(3)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 1
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario4(self):
        self.start_processes_with_test_scenario(4)
        time.sleep(4)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 2
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario5(self):
        self.start_processes_with_test_scenario(5)
        time.sleep(4)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 3
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario6(self):
        self.start_processes_with_test_scenario(6)
        time.sleep(3)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 1
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario7(self):
        self.start_processes_with_test_scenario(7)
        time.sleep(3)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 1
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario8(self):
        self.start_processes_with_test_scenario(8)
        time.sleep(3)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 1
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario9(self):
        self.start_processes_with_test_scenario(9)
        time.sleep(4)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 2
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario10(self):
        self.start_processes_with_test_scenario(10)
        time.sleep(3)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 1
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario11(self):
        self.start_processes_with_test_scenario(11)
        time.sleep(8)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 3
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks

    def test_scenario12(self):
        self.start_processes_with_test_scenario(12)
        time.sleep(8)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)

        assert len(node0_blocks) == 3
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks
