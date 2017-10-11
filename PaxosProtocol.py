"""
    This module implements the logic of the paxos algorithm.
"""


class Block:
    def __init__(self, creator_id, seq, parent, txs):
        self.creator_id = creator_id
        self.SEQ = seq
        self.parent = parent
        self.txs = txs

        if parent:
            self.depth = parent.depth + len(txs)
        else:
            self.depth = 0


class Node:
    def __init__(self):
        self.state = 0
