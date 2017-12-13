"""Integration test: Test partition of paxos nodes.

note: currently the tests only work locally and with ACCUMULATION_TIME = 0.1 because of timing reasons.
"""

from tests.util import MultiNodeTest

import time


class MultiNodeTestPartition(MultiNodeTest):

    def test_scenario30_partition(self):
        self.start_processes_with_test_scenario(30)
        time.sleep(8)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)
        node3_blocks = self.extract_committed_blocks_single_process(3)
        node4_blocks = self.extract_committed_blocks_single_process(4)

        assert len(node0_blocks) > 0
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks
        assert node3_blocks == node1_blocks
        assert node4_blocks == node1_blocks

    def test_scenario31_partition(self):
        self.start_processes_with_test_scenario(31)
        time.sleep(8)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)
        node3_blocks = self.extract_committed_blocks_single_process(3)
        node4_blocks = self.extract_committed_blocks_single_process(4)

        assert len(node0_blocks) > 0
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks
        assert node3_blocks == node1_blocks
        assert node4_blocks == node1_blocks

    def test_scenario32_partition(self):
        self.start_processes_with_test_scenario(32)
        time.sleep(15)
        self.terminate_processes()

        node0_blocks = self.extract_committed_blocks_single_process(0)
        node1_blocks = self.extract_committed_blocks_single_process(1)
        node2_blocks = self.extract_committed_blocks_single_process(2)
        node3_blocks = self.extract_committed_blocks_single_process(3)
        node4_blocks = self.extract_committed_blocks_single_process(4)

        assert len(node0_blocks) > 0
        assert node0_blocks == node1_blocks
        assert node2_blocks == node1_blocks
        assert node3_blocks == node1_blocks
        assert node4_blocks == node1_blocks
