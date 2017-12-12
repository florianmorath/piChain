"""This file stores the for each node an ip address, port and uuid."""


"""
note:
use the following setup for integration tests (basic and crashes)
"""
peers = {
    '0': {'ip': '127.0.0.1', 'port': 5982, 'uuid': 'a60c0bc6-b85a-47ad-abaa-a59e35822de2'},
    '1': {'ip': '127.0.0.1', 'port': 5981, 'uuid': 'b5564ec6-fd1d-481a-b68b-9b49a0ddd38b'},
    '2': {'ip': '127.0.0.1', 'port': 5980, 'uuid': 'c1469026-d386-41ee-adc5-9fd7d0bf453e'}
}

"""
note:
use the following setup for integration tests (partition)
"""
# peers = {
#     '0': {'ip': '127.0.0.1', 'port': 6982, 'uuid': 'a60c0bc6-b85a-47ad-abaa-a59e35822de2'},
#     '1': {'ip': '127.0.0.1', 'port': 6981, 'uuid': 'b5564ec6-fd1d-481a-b68b-9b49a0ddd38b'},
#     '2': {'ip': '127.0.0.1', 'port': 6980, 'uuid': 'c1469026-d386-41ee-adc5-9fd7d0bf453e'},
#     '3': {'ip': '127.0.0.1', 'port': 6984, 'uuid': 'd1469026-d386-41ee-adc5-9fd7d0bf453e'},
#     '4': {'ip': '127.0.0.1', 'port': 6985, 'uuid': 'e1469026-d386-41ee-adc5-9fd7d0bf453e'}
# }
