from mininet.net import Mininet
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.node import UserSwitch
from mininet.node import RemoteController
from mininet.node import OVSKernelSwitch

import time

class SliceableSwitch(UserSwitch):
    def __init__(self, name, **kwargs):
        UserSwitch.__init__(self, name, '', **kwargs)

class MyTopo(Topo):
    def __init__( self ):
        "Create custom topo."
        # Initialize topology
        Topo.__init__( self )
        # Add hosts and switches
        host01 = self.addHost('h1')
        host02 = self.addHost('h2')
        switch01 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='1')
        switch02 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='2')
        switch03 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='3')
        switch04 = self.addSwitch('s4', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='4')
        # Add links
        self.addLink(host01, switch01)
        self.addLink(host02, switch02)
        self.addLink(switch01, switch02)
        self.addLink(switch01, switch03)

def run(net):
    s1 = net.getNodeByName('s1')
    # s1.cmdPrint('dpctl unix:/tmp/s1 queue-mod 1 1 80')
    # s1.cmdPrint('dpctl unix:/tmp/s1 queue-mod 1 2 120')
    # s1.cmdPrint('dpctl unix:/tmp/s1 queue-mod 1 3 800')

def genericTest(topo):
    net = Mininet(topo=topo, switch=SliceableSwitch,
        controller=RemoteController)
    net.start()
    run(net)

    #time.sleep(7)

    #net.addSwitch('s4', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='4')


    # > $ sudo mn -v output
    # > mininet> py net.addHost('h3')
    # > <Host h3:  pid=3405>
    # > mininet> py net.addLink(s1, net.get('h3'))
    # > <mininet.link.Link object at 0x1737090>
    # > mininet> py s1.attach('s1-eth3')
    # > mininet> py net.get('h3').cmd('ifconfig h3-eth0 10.3')
    # > mininet> h1 ping -c1 10.3

    CLI(net)
    net.stop()

def main():
    topo = MyTopo()
    genericTest(topo)

if __name__ == '__main__':
    main()
