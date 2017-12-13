"""This module contains all classes that need to be serialized."""

import json
import jsonpickle


class PaxosMessage:
    def __init__(self, msg_type, request_seq):
        self.msg_type = msg_type  # TRY, TRY_OK, PROPOSE, PROPOSE_ACK, COMMIT
        self.request_seq = request_seq

        # content variables: are assigned depending on message type
        self.new_block = None
        self.prop_block = None
        self.supp_block = None
        self.com_block = None
        self.last_committed_block = None

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'PAM', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        pam = jsonpickle.decode(msg['obj_str'])
        return pam


class RequestBlockMessage:
    """"Is sent if a node is missing a block."""
    def __init__(self, block_id):
        self.block_id = block_id  # id of block which is missing

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'RQB', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        rqb = jsonpickle.decode(msg['obj_str'])
        return rqb


class RespondBlockMessage:
    """Is sent as a response to a `RequestBlockMessage`."""
    def __init__(self, blocks):
        self.blocks = blocks  # the last 5 blocks starting from block the node misses

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'RSB', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        rsb = jsonpickle.decode(msg['obj_str'])
        return rsb

# TODO: add AckCommitMessage


class Block:

    def __init__(self, creator_id, parent_block_id, txs, counter):
        self.creator_id = creator_id
        self.SEQ = counter
        self.block_id = int(str(self.creator_id) + str(self.SEQ))  # (creator_id || SEQ)
        self.creator_state = None
        self.parent_block_id = parent_block_id  # parent block id
        self.txs = txs  # list of transactions of type Transaction
        self.depth = None

    def __lt__(self, other):
        """Compare two blocks by depth` and `creator_id`."""
        if self.depth < other.depth:
            return True

        if self.depth > other.depth:
            return False

        return self.creator_id < other.creator_id

    def __eq__(self, other):
        return self.block_id == other.block_id

    def __hash__(self):
        return 0

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'BLK', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        blk = jsonpickle.decode(msg['obj_str'])
        return blk


class Transaction:
    def __init__(self, creator_id, content, counter):
        self.creator_id = creator_id
        self.SEQ = counter
        self.txn_id = int(str(self.creator_id) + str(self.SEQ))
        self.content = content  # a string which can represent a command for example

    def __eq__(self, other):
        return self.txn_id == other.txn_id

    def __hash__(self):
        return 0

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'TXN', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        txn = jsonpickle.decode(msg['obj_str'])
        return txn


class PingMessage:
    """"Is sent to estimate RTT."""
    def __init__(self, time):
        self.time = time    # timestamp

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'PIN', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        ping = jsonpickle.decode(msg['obj_str'])
        return ping


class PongMessage:
    """"Is sent to estimate RTT."""
    def __init__(self, time):
        self.time = time    # timestamp (the one received in PingMessage)

    def serialize(self):
        obj_str = jsonpickle.encode(self)
        s = json.dumps({'msg_type': 'PON', 'obj_str': obj_str})
        return s.encode()

    @staticmethod
    def unserialize(msg):
        pong = jsonpickle.decode(msg['obj_str'])
        return pong
