

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug
from mininet.node import Host, RemoteController
from mininet.node import OVSKernelSwitch

QUAGGA_DIR = '/usr/lib/quagga'
# Must exist and be owned by quagga user (quagga:quagga by default on Ubuntu)
QUAGGA_RUN_DIR = '/var/run/quagga'
# To avoid permission denied problems
CONFIG_DIR = '/etc/quagga/configs_ospf'

class SdnIpHost(Host):
    def __init__(self, name, ip, route, *args, **kwargs):
        Host.__init__(self, name, ip=ip, *args, **kwargs)

        self.route = route

    def config(self, **kwargs):
        Host.config(self, **kwargs)

        debug("configuring route %s" % self.route)

        self.cmd('ip route add default via %s' % self.route)



class OSPFHost(Host):
    def __init__(self, name, ip, route, *args, **kwargs):
        Host.__init__(self, name, ip=ip, *args, **kwargs)

        self.route = route

    def config(self, **kwargs):
        Host.config(self, **kwargs)

        debug("configuring route %s" % self.route)

        self.cmd('ip route add default via %s' % self.route)

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


class SdnIpTopo( Topo ):
    "SDN-IP tutorial topology"

    def build( self ):
        s1 = self.addSwitch('s1', dpid='00000000000000a1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', dpid='00000000000000a2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', dpid='00000000000000a3', cls=OVSKernelSwitch, protocols='OpenFlow13')

        zebraConf = '%s/zebra.conf' % CONFIG_DIR

        # ------------ Network 1 -----------------
        r1name = 'r1'
        r1eth0 = { 'mac' : '00:00:00:00:01:01',
                 'ipAddrs' : ['10.0.1.254/24'] }
        r1eth1 = { 'mac' : '00:00:00:00:01:02',
                 'ipAddrs' : ['10.1.101.1/24'] }
        r1eth2 = { 'mac' : '00:00:00:00:01:03',
                 'ipAddrs' : ['10.1.103.2/24'] }
        r1intfs = { 'r1-eth0' : r1eth0,
                  'r1-eth1' : r1eth1,
                  'r1-eth2' : r1eth2 }
        r1quaggaConf = '%s/quagga1.conf' % (CONFIG_DIR)

        r1 = self.addHost(r1name, cls=OSPFRouter, quaggaConfFile=r1quaggaConf, zebraConfFile=zebraConf, intfDict=r1intfs)
        #h1 = self.addHost('h1', cls=OSPFHost, ip='192.168.1.1/24', route='192.168.1.254')

        r2name = 'r2'
        r2eth0 = { 'mac' : '00:00:00:00:02:01',
                 'ipAddrs' : ['10.0.2.254/24'] }
        r2eth1 = { 'mac' : '00:00:00:00:02:02',
                 'ipAddrs' : ['10.1.101.2/24'] }
        r2eth2 = { 'mac' : '00:00:00:00:02:03',
                 'ipAddrs' : ['10.1.102.2/24'] }
        r2intfs = { 'r2-eth0' : r2eth0,
                  'r2-eth1' : r2eth1,
                  'r2-eth2' : r2eth2 }
        r2quaggaConf = '%s/quagga2.conf' % (CONFIG_DIR)

        r2 = self.addHost(r2name, cls=OSPFRouter, quaggaConfFile=r2quaggaConf, zebraConfFile=zebraConf, intfDict=r2intfs)
        #h1 = self.addHost('h1', cls=OSPFHost, ip='192.168.1.1/24', route='192.168.1.254')

        r3name = 'r3'
        r3eth0 = { 'mac' : '00:00:00:00:03:01',
                 'ipAddrs' : ['10.0.3.254/24'] }
        r3eth1 = { 'mac' : '00:00:00:00:03:02',
                 'ipAddrs' : ['10.1.103.1/24'] }
        r3eth2 = { 'mac' : '00:00:00:00:03:03',
                 'ipAddrs' : ['10.1.102.1/24'] }
        r3intfs = { 'r3-eth0' : r3eth0,
                  'r3-eth1' : r3eth1,
                  'r3-eth2' : r3eth2 }
        r3quaggaConf = '%s/quagga3.conf' % (CONFIG_DIR)

        r3 = self.addHost(r3name, cls=OSPFRouter, quaggaConfFile=r3quaggaConf, zebraConfFile=zebraConf, intfDict=r3intfs)
        #h1 = self.addHost('h1', cls=OSPFHost, ip='192.168.1.1/24', route='192.168.1.254')


        self.addLink(r1, s1)
        self.addLink(r2, s2)
        self.addLink(r3, s3)

        self.addLink(r1, r2)
        self.addLink(r1, r3)
        self.addLink(r2, r3)

        # ------------ Network 2 -------------
        # Router 4
        r4name = 'r4'
        r4eth0 = { 'mac' : '00:00:00:00:04:01',
                 'ipAddrs' : ['10.0.1.253/24'] }
        r4eth1 = { 'mac' : '00:00:00:00:04:02',
                 'ipAddrs' : ['10.2.101.1/24'] }
        r4eth2 = { 'mac' : '00:00:00:00:04:03',
                 'ipAddrs' : ['10.2.103.2/24'] }
        r4intfs = {
            'r4-eth0': r4eth0,
            'r4-eth1': r4eth1,
            'r4-eth2': r4eth2
        }
        r4quaggaConf = '%s/quagga4.conf' % (CONFIG_DIR)
        r4 = self.addHost(r4name, cls=OSPFRouter, quaggaConfFile=r4quaggaConf, zebraConfFile=zebraConf, intfDict=r4intfs)

        # Router 5
        r5name = 'r5'
        r5eth0 = { 'mac' : '00:00:00:00:05:01',
                 'ipAddrs' : ['10.0.2.253/24'] }
        r5eth1 = { 'mac' : '00:00:00:00:05:02',
                 'ipAddrs' : ['10.2.101.2/24'] }
        r5eth2 = { 'mac' : '00:00:00:00:05:03',
                 'ipAddrs' : ['10.2.102.2/24'] }
        r5intfs = {
            'r5-eth0': r5eth0,
            'r5-eth1': r5eth1,
            'r5-eth2': r5eth2
        }
        r5quaggaConf = '%s/quagga5.conf' % (CONFIG_DIR)
        r5 = self.addHost(r5name, cls=OSPFRouter, quaggaConfFile=r5quaggaConf, zebraConfFile=zebraConf, intfDict=r5intfs)

        # Router 6
        r6name = 'r6'
        r6eth0 = { 'mac' : '00:00:00:00:06:01',
                 'ipAddrs' : ['10.0.3.253/24'] }
        r6eth1 = { 'mac' : '00:00:00:00:06:02',
                 'ipAddrs' : ['10.2.103.1/24'] }
        r6eth2 = { 'mac' : '00:00:00:00:06:03',
                 'ipAddrs' : ['10.2.102.1/24'] }
        r6intfs = {
            'r6-eth0': r6eth0,
            'r6-eth1': r6eth1,
            'r6-eth2': r6eth2
        }
        r6quaggaConf = '%s/quagga6.conf' % (CONFIG_DIR)
        r6 = self.addHost(r6name, cls=OSPFRouter, quaggaConfFile=r6quaggaConf, zebraConfFile=zebraConf, intfDict=r6intfs)

        self.addLink(r4, s1)
        self.addLink(r5, s2)
        self.addLink(r6, s3)

        self.addLink(r4, r5)
        #self.addLink(r4, r6)
        self.addLink(r5, r6)

        h1 = self.addHost('h1', cls=OSPFHost, ip='10.0.1.1', route='10.0.1.254')
        self.addLink(h1, s1)


topos = { 'sdnip' : SdnIpTopo }

if __name__ == '__main__':
    setLogLevel('debug')
    topo = SdnIpTopo()

    net = Mininet(topo=topo, controller=RemoteController)

    net.start()

    CLI(net)

    net.stop()

    info("done\n")
