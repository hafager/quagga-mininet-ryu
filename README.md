# master


## Network
The file `topology_quagga_ospf.py` creates a network with 3 routers(`r1`, `r2`, `r3`) running OSPF between themselves.
Each router is connected to one switch (`s1`, `s2`, `s3`) with a separate subnet (`10.0.x.0/24`).
They are all interconnected through one switch `s4` on the subnet `10.1.100.0/24`. `s4` is connected to a separate controller to decouple it from the networks outside of the OSPF networks, and runs a simple switch.
Additionally `h1` is connected to `s3` for testing purposes.
```
The network:
s1--r1---------s4------r2--s2
               |
               |
               r3
               |
               s3
               |
               h1
```


The network can be started by running:
```
sudo python topology_quagga_ospf.py
```
## Controllers
The network will then listen for controllers on 
- 6653 (`s1`, `s2`, `s3`)
- 6654 (`s4`)

Then start a simple switch for the OSPF network (`s4`)
```
ryu-manager --ofp-tcp-listen-port 6654 simple_switch.py
```
And the controller for the other switches:
```
ryu-manager --ofp-tcp-listen-port 6653 simple_switch.py
```
