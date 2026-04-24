#!/usr/bin/env python3
"""
QoS Priority Controller - Mininet Topology (POX version)
4 hosts connected to 1 OpenFlow switch controlled by POX.
  h1 = Video streaming  (TCP port 5001) - highest priority
  h2 = VoIP            (TCP port 5004) - high priority
  h3 = HTTP/Web        (TCP port 80)   - medium priority
  h4 = FTP/Bulk        (TCP port 21)   - low priority
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink


class QoSTopology(Topo):
    def build(self):
        s1 = self.addSwitch('s1')

        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')

        self.addLink(h1, s1, bw=10, delay='5ms',  loss=0, max_queue_size=1000)
        self.addLink(h2, s1, bw=10, delay='5ms',  loss=0, max_queue_size=1000)
        self.addLink(h3, s1, bw=10, delay='10ms', loss=0, max_queue_size=1000)
        self.addLink(h4, s1, bw=10, delay='20ms', loss=0, max_queue_size=1000)


def run():
    topo = QoSTopology()
    net = Mininet(
        topo=topo,
        controller=RemoteController('c0', ip='127.0.0.1', port=6633),
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=False
    )
    net.start()

    print("\n*** QoS Topology started (POX controller) ***")
    print("h1=Video(5001)  h2=VoIP(5004)  h3=HTTP(80)  h4=FTP(21)")
    print("Controller: POX at 127.0.0.1:6633\n")

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
