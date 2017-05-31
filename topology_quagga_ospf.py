from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug
from mininet.node import Host, RemoteController
from mininet.node import Controller, OVSController
from mininet.node import OVSSwitch

QUAGGA_DIR = '/usr/lib/quagga'
# Must exist and be owned by quagga user (quagga:quagga by default on Ubuntu)
QUAGGA_RUN_DIR = '/var/run/quagga'
# To avoid permission denied problems
# Folder bust be owned by quagga:quaggavty
# Files must be owned by quagga:quagga
# Files must be executable
CONFIG_DIR = '/etc/quagga/configs'

class InbandController( RemoteController ):
    def __init__(self, *args, **kwargs):
        RemoteController.__init__(self, *args, **kwargs)

    def checkListening( self ):
        "Overridden to do nothing."
        return

class OSPFHost(Host):
    def __init__(self, name, ip, route, *args, **kwargs):
        Host.__init__(self, name, ip=ip, *args, **kwargs)

        self.route = route

    def config(self, **kwargs):
        Host.config(self, **kwargs)

        debug("configuring route %s" % self.route)
        self.cmd('ip route add default via %s' % self.route)

class OSPFSwitch(OVSSwitch):
    def __init__(self, name, *args, **kwargs):
        OVSSwitch.__init__(self, name, *args, **kwargs)

    def start(self, a):
        return OVSSwitch.start(self, [cmap[self.name]])

class OSPFRouter(Host):
    def __init__(self, name, quaggaConfFile, zebraConfFile, intfDict, *args, **kwargs):
        Host.__init__(self, name, *args, **kwargs)

        self.quaggaConfFile = quaggaConfFile
        self.zebraConfFile = zebraConfFile
        self.intfDict = intfDict

    def config(self, **kwargs):
        Host.config(self, **kwargs)
        self.cmd('sysctl net.ipv4.ip_forward=1')

        for intf, attrs in self.intfDict.items():
            self.cmd('ip addr flush dev %s' % intf)
            if 'mac' in attrs:
                self.cmd('ip link set %s down' % intf)
                self.cmd('ip link set %s address %s' % (intf, attrs['mac']))
                self.cmd('ip link set %s up' % intf)
            for addr in attrs['ipAddrs']:
                self.cmd('ip addr add %s dev %s' % (addr, intf))

        self.cmd('/usr/lib/quagga/zebra -d -f %s -z %s/zebra%s.api -i %s/zebra%s.pid' % (self.zebraConfFile, QUAGGA_RUN_DIR, self.name, QUAGGA_RUN_DIR, self.name))
        self.cmd('/usr/lib/quagga/ospfd -d -f %s -z %s/zebra%s.api -i %s/ospfd%s.pid' % (self.quaggaConfFile, QUAGGA_RUN_DIR, self.name, QUAGGA_RUN_DIR, self.name))

    def terminate(self):
        self.cmd("ps ax | egrep 'ospfd%s.pid|zebra%s.pid' | awk '{print$1}' | xargs kill" % (self.name, self.name))
        Host.terminate(self)

class OSPFTopo( Topo ):
    "SDN-IP tutorial topology"

    def build( self ):
        s1 = self.addSwitch('s1', dpid='00000000000000a1', cls=OSPFSwitch, protocols='OpenFlow13', inband=True, inNamespace=True)
        s2 = self.addSwitch('s2', dpid='00000000000000a2', cls=OSPFSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', dpid='00000000000000a3', cls=OSPFSwitch, protocols='OpenFlow13')
        s4 = self.addSwitch('s4', dpid='00000000000000a4', cls=OSPFSwitch, protocols='OpenFlow13')

        zebraConf = '%s/zebra.conf' % CONFIG_DIR

        # Router 1
        r1name = 'r1'
        r1eth0 = { 'mac' : '00:00:00:00:01:01',
                 'ipAddrs' : ['10.0.1.254/24'] }
        r1eth1 = { 'mac' : '00:00:00:00:01:02',
                 'ipAddrs' : ['10.1.100.1/24'] }
        r1intfs = { 'r1-eth0' : r1eth0,
                  'r1-eth1' : r1eth1}
        r1quaggaConf = '%s/quagga1.conf' % (CONFIG_DIR)
        r1 = self.addHost(r1name, cls=OSPFRouter, quaggaConfFile=r1quaggaConf, zebraConfFile=zebraConf, intfDict=r1intfs)

        # Router 2
        r2name = 'r2'
        r2eth0 = { 'mac' : '00:00:00:00:02:01',
                 'ipAddrs' : ['10.0.2.254/24'] }
        r2eth1 = { 'mac' : '00:00:00:00:02:02',
                 'ipAddrs' : ['10.1.100.2/24'] }
        r2intfs = { 'r2-eth0' : r2eth0,
                  'r2-eth1' : r2eth1}
        r2quaggaConf = '%s/quagga2.conf' % (CONFIG_DIR)
        r2 = self.addHost(r2name, cls=OSPFRouter, quaggaConfFile=r2quaggaConf, zebraConfFile=zebraConf, intfDict=r2intfs)

        # Router 3
        r3name = 'r3'
        r3eth0 = { 'mac' : '00:00:00:00:03:01',
                 'ipAddrs' : ['10.0.3.254/24'] }
        r3eth1 = { 'mac' : '00:00:00:00:03:02',
                 'ipAddrs' : ['10.1.100.3/24'] }
        r3intfs = { 'r3-eth0' : r3eth0,
                  'r3-eth1' : r3eth1}
        r3quaggaConf = '%s/quagga3.conf' % (CONFIG_DIR)
        r3 = self.addHost(r3name, cls=OSPFRouter, quaggaConfFile=r3quaggaConf, zebraConfFile=zebraConf, intfDict=r3intfs)

        # Add links to their separate networks
        self.addLink(r1, s1)
        self.addLink(r2, s2)
        self.addLink(r3, s3)

        # Add links to connect the OSPF network
        self.addLink(r1, s4)
        self.addLink(r2, s4)
        self.addLink(r3, s4)

        # Add hosts to each platform
        h1 = self.addHost('h1', cls=OSPFHost, ip='10.0.1.1', route='10.0.1.254')
        h2 = self.addHost('h2', cls=OSPFHost, ip='10.0.2.1', route='10.0.2.254')
        h3 = self.addHost('h3', cls=OSPFHost, ip='10.0.3.1', route='10.0.3.254')
        self.addLink(h1, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)

        # Add hosts for controllers for each platform
        h4 = self.addHost('h4', ip='10.0.1.2')
        h5 = self.addHost('h5', ip='10.0.2.2')
        h6 = self.addHost('h6', ip='10.0.3.2')
        self.addLink(h4, s1)
        self.addLink(h4, s2)
        self.addLink(h4, s3)

topos = { 'ospf' : OSPFTopo }

# One controller for taking care of the OSPF network and one for the switches outside of the OSPF network
# c1 running inside the OSPF network. Runs a simple switch.
c1 = InbandController(name='c1', ip='10.0.1.2', port=6653)
c2 = InbandController(name='c2', ip='127.0.0.1', port=6654)
c3 = InbandController(name='c3', ip='127.0.0.1', port=6655)
c4 = InbandController(name='c4', ip='127.0.0.1', port=6656)
# ryu-manager --ofp-tcp-listen-port 6656 simple_switch.py

cmap = {'s1': c1, 's2': c2, 's3': c3, 's4': c4}

if __name__ == '__main__':
    setLogLevel('debug')
    topo = OSPFTopo()

    net = Mininet(topo=topo, controller=None)

    for controller in cmap:
        net.addController(cmap[controller])

    net.start()
    net.getNodeByName('s1').cmd('ifconfig s1 inet 10.0.1.10')

    CLI(net)

    net.stop()

    info("done\n")
