"""This module defines the representation of all objects that need to be sent over the network and thus need to be
serialized and unserialized."""

import cbor


class PaxosMessage:
    """ A paxos message used to commit a block.

    Args:
        msg_type (str): TRY, TRY_OK, PROPOSE, PROPOSE_ACK or COMMIT.
        request_seq (int): each message contains a request sequence number s.t outdated messaged can be detected.

    Attributes:
        new_block (int): block_id of new block (block a quick node wants to commit).
        prop_block (int): block_id of proposed block.
        supp_block (int): block_id of support block (supporting the proposed block).
        com_block (int): block_id of compromise block.
        last_committed_block (int): block_id of last committed block (for faster recovery in case of partition).
    """
    def __init__(self, msg_type, request_seq):
        self.msg_type = msg_type
        self.request_seq = request_seq

        # content variables: are assigned depending on message type
        self.new_block = None
        self.prop_block = None
        self.supp_block = None
        self.com_block = None
        self.last_committed_block = None

    def serialize(self):
        """
        Returns (bytes): bytes representing the object.
        """
        obj_list = [self.last_committed_block, self.com_block, self.supp_block, self.prop_block, self.new_block,
                    self.request_seq, self.msg_type]
        obj_bytes = cbor.dumps(obj_list)
        return b'PAM' + obj_bytes

    @staticmethod
    def unserialize(msg):
        """
        Args:
            msg (bytes): PaxosMessage represented in bytes.

        Returns:
             PaxosMessage: original PaxosMessage instance.
        """
        obj_list = cbor.loads(msg[3:])
        obj = PaxosMessage.__new__(PaxosMessage)
        setattr(obj, 'msg_type', obj_list.pop())
        setattr(obj, 'request_seq', obj_list.pop())
        setattr(obj, 'new_block', obj_list.pop())
        setattr(obj, 'prop_block', obj_list.pop())
        setattr(obj, 'supp_block', obj_list.pop())
        setattr(obj, 'com_block', obj_list.pop())
        setattr(obj, 'last_committed_block', obj_list.pop())
        return obj


class RequestBlockMessage:
    """"Is sent if a node is missing a block.

    Args:
        block_id (int): block id of missing block.
    """
    def __init__(self, block_id):
        self.block_id = block_id

    def serialize(self):
        """
        Returns (bytes): bytes representing the object.
        """
        return b'RQB' + cbor.dumps(self.block_id)

    @staticmethod
    def unserialize(msg):
        """
        Args:
            msg (bytes): RequestBlockMessage represented in bytes.

        Returns:
             RequestBlockMessage: original RequestBlockMessage instance.
        """
        block_id = cbor.loads(msg[3:])
        obj = RequestBlockMessage.__new__(RequestBlockMessage)
        setattr(obj, 'block_id', block_id)
        return obj


class RespondBlockMessage:
    """Is sent as a response to a `RequestBlockMessage`.

    Args:
        blocks (list): list containing the missing blocks.
    """
    def __init__(self, blocks):
        self.blocks = blocks  # the last 5 blocks starting from block the node misses

    def serialize(self):
        """
        Returns (bytes): bytes representing the object.
        """
        blocks = []
        for b in self.blocks:
            blocks.append(b.serialize())
        return b'RSB' + cbor.dumps(blocks)

    @staticmethod
    def unserialize(msg):
        """
        Args:
            msg (bytes): RespondBlockMessage represented in bytes.

        Returns:
             RespondBlockMessage: original RespondBlockMessage instance.
        """
        obj_list = cbor.loads(msg[3:])
        blocks = []
        for b in obj_list:
            blocks.append(Block.unserialize(b))
        obj = RespondBlockMessage.__new__(RespondBlockMessage)
        setattr(obj, 'blocks', blocks)
        return obj


class AckCommitMessage:
    """Is broadcast once a node commits a block to perform genesis block change once all nodes committed a block.

    Args:
        block_id (int): block id of committed block.
    """
    def __init__(self, block_id):
        self.block_id = block_id

    def serialize(self):
        """
        Returns (bytes): bytes representing the object.
        """
        return b'ACM' + cbor.dumps(self.block_id)

    @staticmethod
    def unserialize(msg):
        """
        Args:
            msg (bytes): AckCommitMessage represented in bytes.

        Returns:
             AckCommitMessage: original AckCommitMessage instance.
        """
        block_id = cbor.loads(msg[3:])
        obj = AckCommitMessage.__new__(AckCommitMessage)
        setattr(obj, 'block_id', block_id)
        return obj


class Block:
    """A block containing transactions.

    Args:
        creator_id (int): id of the node that created the block.
        parent_block_id (:obj:`int`, optional): id of parent block.
        txs (list): list of Transaction instances.
        counter (int): used to define unqiue sequence number.

    Attributes:
        block_id (int): used to uniquely identify a block.
        SEQ (int): sequence number used to create unique block id.
        creator_state (int): 0,1 or 2 translates to QUICK, MEDIUM or SLOW.
        depth (int): Total number of transactions the block and all ist ancestor blocks contain.
    """
    def __init__(self, creator_id, parent_block_id, txs, counter):
        self.creator_id = creator_id
        self.SEQ = counter
        self.block_id = self.creator_id | (self.SEQ << 16)
        self.creator_state = None
        self.parent_block_id = parent_block_id
        self.depth = None
        self.txs = txs

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
        return hash(self.block_id)

    def serialize(self):
        """
        Returns (bytes): bytes representing the object.
        """
        txs = []
        for txn in self.txs:
            txs.append(txn.serialize())
        obj_list = [txs, self.depth, self.parent_block_id, self.creator_state, self.block_id, self.SEQ, self.creator_id]
        obj_bytes = cbor.dumps(obj_list)
        return b'BLK' + obj_bytes

    @staticmethod
    def unserialize(msg):
        """
        Args:
            msg (bytes): Block represented in bytes.

        Returns:
             Block: original Block instance.
        """
        obj_list = cbor.loads(msg[3:])

        obj = Block.__new__(Block)
        setattr(obj, 'creator_id', obj_list.pop())
        setattr(obj, 'SEQ', obj_list.pop())
        setattr(obj, 'block_id', obj_list.pop())
        setattr(obj, 'creator_state', obj_list.pop())
        setattr(obj, 'parent_block_id', obj_list.pop())
        setattr(obj, 'depth', obj_list.pop())
        txs = []
        for txn in obj_list.pop():
            txs.append(Transaction.unserialize(txn))
        setattr(obj, 'txs', txs)
        return obj


class Transaction:
    """ A Transaction contains a content field wich can store an arbitrary string. This can for example be a database-
    operation.

    Args:
        creator_id (int): id of the node that created the transaction.
        content (str): the command to be stored/executed/committed.
        counter (int): used to define unqiue sequence number.

    Attributes:
        SEQ (int): used to define unique transaction id.
        txn_id (int): used to uniquely identify a transaction.
    """
    def __init__(self, creator_id, content, counter):
        self.creator_id = creator_id
        self.SEQ = counter
        self.txn_id = self.creator_id | (self.SEQ << 16)
        self.content = content  # a string which can represent a command for example

    def __eq__(self, other):
        return self.txn_id == other.txn_id

    def __hash__(self):
        return hash(self.txn_id)

    def serialize(self):
        """
        Returns (bytes): bytes representing the object.
        """
        obj_list = [self.content, self.txn_id, self.SEQ, self.creator_id]
        obj_bytes = cbor.dumps(obj_list)
        return b'TXN' + obj_bytes

    @staticmethod
    def unserialize(msg):
        """
        Args:
            msg (bytes): Transaction represented in bytes.

        Returns:
             Transaction: original Transaction instance.
        """
        obj_list = cbor.loads(msg[3:])
        obj = Transaction.__new__(Transaction)
        setattr(obj, 'creator_id', obj_list.pop())
        setattr(obj, 'SEQ', obj_list.pop())
        setattr(obj, 'txn_id', obj_list.pop())
        setattr(obj, 'content', obj_list.pop())
        return obj


class PingMessage:
    """Is sent to estimate RTT.

    Args:
        time (float): timestamp marking the start.
    """
    def __init__(self, time):
        self.time = time

    def serialize(self):
        """
        Returns (bytes): bytes representing the object.
        """
        return b'PIN' + cbor.dumps(self.time)

    @staticmethod
    def unserialize(msg):
        """
        Args:
            msg (bytes): PingMessage represented in bytes.

        Returns:
             PingMessage: original PingMessage instance.
        """
        time = cbor.loads(msg[3:])
        obj = PingMessage.__new__(PingMessage)
        setattr(obj, 'time', time)
        return obj


class PongMessage:
    """Is sent to estimate RTT.

    Args:
        time (float): timestamp that was received in the PingMessage.
    """
    def __init__(self, time):
        self.time = time

    def serialize(self):
        """
        Returns (bytes): bytes representing the object.
        """
        return b'PON' + cbor.dumps(self.time)

    @staticmethod
    def unserialize(msg):
        """
        Args:
            msg (bytes): PongMessage represented in bytes.

        Returns:
             PongMessage: original PongMessage instance.
        """
        time = cbor.loads(msg[3:])
        obj = PongMessage.__new__(PongMessage)
        setattr(obj, 'time', time)
        return obj
