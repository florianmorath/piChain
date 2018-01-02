""" Configuration module. """


#
# Paxos Logic (Timing)
#

# time the quick node accumulates transactions befor creating a block (0.1 is the default)
# the higher the RPS rate the higher this value should be
ACCUMULATION_TIME = 0.1
