# Mininet emulation for paper

This folder contains the emulation of the cluster discussed in the paper, intended to be originally implemented using Raspberry Pi 3/4 Model B/B+.

## Implementation

Multiple hosts are created, out of which one is chosen as the master node. There are less number of standby than active nodes. Active nodes are those to be running some form of computation, here just a simple increment. Standby nodes monitor the active nodes, and report any failure to the master node. Timeout is used to detect if any active node is down. A server runs on the master node, that detects any failure,
reassigns one of the corresponding standby nodes as the new active node, and manages the overall cluster. Most functions are implemented using the Mininet Python (v.2x) API and Python threads. Subprocesses do not share resources like lists and dicts, and hence the use of threads. However, Mininet is not thread safe.

## Issues

Often, assertion errors are thrown when using .cmd(). .popen() is a solution, but not fast enough, which is why the master will not read the correct failed active node. A queue must be implemented on the server side to regulate the rate at which requests are fed to the master node. Some functionalities can be modularized into further functions.

Regular updates on the status of the project can be found [here](https://docs.google.com/document/d/1nu5DaCyusmTI1MsJf_ltdt4ChMOaHcWaL71IBXUBuzY/edit?usp=sharing).