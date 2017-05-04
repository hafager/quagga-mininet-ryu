from ryu.lib import pcaplib
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ospf

# iterate pcaplib.Reader that yields (timestamp, packet_data)
# in the PCAP file
frame_count = 0
for ts, buf in pcaplib.Reader(open('master/OSPF_LSA_types.cap', 'rb')):
    frame_count += 1
    pkt = packet.Packet(buf)
    #print("%d, %f, %s" % (frame_count, ts, pkt))


    eth = pkt.get_protocol(ethernet.ethernet)
    ip = pkt.get_protocol(ipv4.ipv4)
    ospfpkt = pkt.get_protocol(ospf.ospf)
    for i in pkt.protocols:
        #if 'OSPF' in i:
        try:
            if "OSPF" in i.protocol_name:
                print i
        except:
            pass


    #print dir(ospfpkt)
    #print ospfpkt.protocol_name
