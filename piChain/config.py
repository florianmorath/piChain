""" Configuration module. """


#
# Paxos Logic (Timing - Fine tuning)
#

# time the quick node accumulates transactions befor creating a block.
# dependences: the higher the RPS rate, the higher this value should be.
# default = 0.1 seconds
ACCUMULATION_TIME = 0.1

# max allowed time a node has to commit a block.
# dependences: the higher RPS rate and txn sizes, the higher this value should be.
# note: the expected round trip times needed will be automatically added to this value, so this value should but a limit
# on the local processing time only.
# default = 2 seconds
MAX_COMMIT_TIME = 2
