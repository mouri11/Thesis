# Resource-Constrained Cluster for Intensive Computations
This is intended to contain the source code implementing and solving the above-mentioned scenario. The project is originally intended to be implemented using ARM devices like Raspberry Pi. Currently, the project contains a sandbox implementation in Mininet, and an ongoing closer-to-real-life implementation on AWS EC2.

For the AWS setup, LXD and runc are the intended tools to be used to implement live migration, to mitigate failure of nodes and reduce downtime. A journal laying out the progress and timeline of the project can be found [here](https://docs.google.com/document/d/1nu5DaCyusmTI1MsJf_ltdt4ChMOaHcWaL71IBXUBuzY/edit).
