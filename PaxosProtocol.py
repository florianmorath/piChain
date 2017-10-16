"""
    This module implements the logic of the paxos algorithm.
"""

QUICK = 0
MEDIUM = 1
SLOW = 2


class Block:
    def __init__(self, creator_id, seq, parent, txs):
        self.creator_id = creator_id
        self.SEQ = seq
        self.parent = parent  # pointer to a parent block
        self.txs = txs  # list of transactions of type Transaction

        if parent:
            self.depth = parent.depth + len(txs)
        else:
            self.depth = 0

    def __lt__(self, other):
        """Compare two blocks by depth and creator ID."""
        if self.depth < other.depth:
            return True

        if self.depth > other.depth:
            return False

        return self.creator_id < other.creator_id


class Transaction:
    def __init__(self, creator_od, seq, content):
        self.creator_id = creator_od
        self.SEQ = seq
        self.content = content


class Message:
    def __init__(self, message_type):
        self.message_type = message_type  # try, ok, propose, ack, commit


class Node:
    def __init__(self):
        self.state = QUICK

    def receive_message(self, message):
        ''' receive a message of type Message. Return answer of type Message. '''

    def receive_transaction(self, txn):
        ''' react on a received txn depending on '''

    def receive_block(self, block):
        ''' react on a received block '''



