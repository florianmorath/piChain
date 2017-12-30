"""This file stores the for each node an ip address, port and uuid."""


"""
note:
use the following setup for integration tests (basic and crashes)
"""
# peers = {
#     '0': {'ip': '127.0.0.1', 'port': 7982},
#     '1': {'ip': '127.0.0.1', 'port': 7981},
#     '2': {'ip': '127.0.0.1', 'port': 7980}
# }

"""
note:
use the following setup for integration tests (partition)
"""
peers = {
    '0': {'ip': '127.0.0.1', 'port': 6982},
    '1': {'ip': '127.0.0.1', 'port': 6981},
    '2': {'ip': '127.0.0.1', 'port': 6980},
    '3': {'ip': '127.0.0.1', 'port': 6984},
    '4': {'ip': '127.0.0.1', 'port': 6985}
}
