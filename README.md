# piChain

piChain is a library which implements a fault-tolerant distributed state machine that inherits features of Paxos, providing strong consistency, and of a blockchain, providing eventual consistency and simplicity. For example the library can be used to keep replicas of a distributed data storage consistent in case of failures.

## Requirements

Python 3.6, pip

## Installation

It is recommended to install piChain inside a virtual environment.

Setup a virtual environment:
```
virtualenv --python=python3 <venv-name>
source <venv-name>/bin/activate
```
Install piChain:
```
git clone https://github.com/florianmorath/piChain.git
cd piChain
pip install -r requirements.txt
python setup.py install 
```
Note: before running `pip install -r requirements.txt` you need to have a leveldb instance installed. The installation process depends on the OS. For macOS do the following:
```
brew install leveldb
CFLAGS='-mmacosx-version-min=10.7 -stdlib=libc++' pip install --no-use-wheel plyvel
```

## Usage

First, one needs to setup the Node instances (each node represents a peer in the network):
A Node constructor takes two arguments, a node index and a peers dictionary. The peers dictionary contains an (ip,port) pair for each node. With the `node_index` argument one can select which node from the peers dictionary is running "locally". 
The `tx_committed` field of a Node instance is a callable that is called once a transaction has been committed. By calling `start_server()` on the Node instance the local node will try to connect to its peers. 
Note: `start_server()` starts the twisted main loop. 
```python
from piChain import Node

def tx_committed(commands):
    """
    Args:
        commands (list of str): List of committed Transaction commands.
    """
    for command in commands:
        print('command committed: %s' % command)

def main():
    node_index = 0
    peers = {
        '0': {'ip': '127.0.0.1', 'port': 7982},
        '1': {'ip': '127.0.0.1', 'port': 7981},
        '2': {'ip': '127.0.0.1', 'port': 7980}
    }
    node = Node(node_index, peers)
    node.tx_committed = tx_committed
    node.start_server()
```

Transactions can be committed by calling `make_txn('command')` on a Node instance:
```python
node.make_txn('command')
```

## Performance
This plot shows the benchmark results of how many Requests Per Second (RPS) piChain can handle for different cluster sizes. 
<p align="center">
  <img src="/docs/images/plot_average_pichain.png">
</p>


## More information
- There is a distributed database implementation in the examples folder to demonstrate an application of the piChain package. 
- The API documentation can be build as follows: (requires installation of the piChain package)
```
pip install sphinx
pip install sphinxcontrib-napoleon
cd docs
make html
```

## Publications
- [piChain: When a Blockchain meets Paxos](https://www.tik.ee.ethz.ch/file/14b0ed803c27d585cc06ecd91164c48a/piChain.pdf)
- [Implementation of piChain](https://pub.tik.ee.ethz.ch/students/2017-HS/BA-2017-36.pdf)
