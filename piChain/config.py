""" Configuration module. Can be used to fine-tune the timeouts. """


#
# Paxos Logic (Timing - Fine tuning)
#


ACCUMULATION_TIME = 0.1
"""float: Time the quick node accumulates transactions befor creating a block.

dependences: the higher the RPS rate, the higher this value should be.
default = 0.1 seconds
"""


MAX_COMMIT_TIME = 2
"""float: Max allowed time a node has to commit a block.

dependences: the higher RPS rate and txn sizes, the higher this value should be.
Note: the expected round trip times needed will be automatically added to this value, so this value should put a limit
on the local processing time only.
default = 2 seconds
"""

#
# Paxos Logic (Data sizes)
#


MAX_TXN_COUNT = 7500
"""int: Max number of transactions allowed in a block.

dependences: depends on transaction size.
default = 7500 transactions (this is based on transactions that are of size = 200 bytes)
"""

RECOVERY_BLOCKS_COUNT = 5
"""int: Number of blocks send to a node if he is missing a block s.t he can recover after a crash or a partition. 

dependences: depends on number of transactions send per second and how long crashed nodes are down. 
default = 5
"""

#
# Logging and Debug
#


TESTING = False
"""bool: If set to true will log all debug messages.

Note: set it to False during a performance test.
"""
