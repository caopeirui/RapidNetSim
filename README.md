RapinNetSim is a fast and scalable event-driven network simulator.

# Prerequisites
Python3 has been installed and teminal can use command `python3`.

Add the project root path into PYTHONPATH environment variables. Eg:
```bash
vim ~/.bashrc

# add
export PYTHONPATH=$PYTHONPATH:"【Your path】/RapidNetSim"

# let it take effect
source ~/.bashrc
```


# Get Started

## Simple Test
```
cd 16kGPU_many_exp/onebigtask/hw_oxc_allreduce_nopeer
sh start.sh
```

# Generate Doxygen Document
```sh
cd doc
sh make_and_open_doc.sh
```

# Feature
Simulate real time through global static simulator and event base class.

Task generator generate numerous jobs.

Global topology including link capacity.

Jobs can share links.

Update link occupancy at every task event.

Network refresh after every event is done.

Different routing schemes are supported.

Initial configuration templating.

If NIC_src and NIC_dst belong to the same server, do not accupy links bandwidth.

Large-scale verification.

Multi-stage controller.

Ring adn Butterfly strategy.

Multiple tasks can be excuted in turn.

A NIC can be used by next task only when all flows of last task on it have been done.

The real start time of every task is determined by TaskStartEvent and TASK_WAITING_LIST.

Reconfiguration after every task is done.

Automatic Logger.

Measurement event measure link sharing.

Collision weight mechanism.

Support single GPU occupation.
