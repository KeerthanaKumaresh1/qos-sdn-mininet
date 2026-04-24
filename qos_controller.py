"""
Simple QoS Priority Controller using POX + OpenFlow 1.0

Traffic priority mapping:
  TCP port 5001 (Video)  -> priority 300  (Highest)
  TCP port 5004 (VoIP)   -> priority 200
  TCP port 80   (HTTP)   -> priority 100
  TCP port 21   (FTP)    -> priority 50   (Lowest)
  All other traffic      -> priority 1    (Default/flood)

Save this file in: ~/pox/ext/qos_controller.py
Run with: python3 pox.py qos_controller
"""

from pox.core import core
from pox.lib.revent import *
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.tcp import tcp

log = core.getLogger()

QOS_RULES = [
    (5001, 300, 'VIDEO'),
    (5004, 200, 'VOIP'),
    (80,   100, 'HTTP'),
    (21,    50, 'FTP'),
]


class QoSController(EventMixin):
    """
    QoS Priority Controller for POX.
    Installs priority flow rules on switch connect,
    then does MAC learning on packet_in events.
    """

    def __init__(self):
        self.mac_table = {}
        self.listenTo(core.openflow)
        log.info("=== QoS Priority Controller (POX) started ===")

    def _handle_ConnectionUp(self, event):
        """Called when a switch connects to the controller."""
        connection = event.connection
        dpid = dpid_to_str(event.dpid)
        self.mac_table[event.dpid] = {}

        log.info("Switch connected: %s", dpid)

        self._install_table_miss(connection)
        self._install_qos_rules(connection)

        log.info("All QoS rules installed on switch %s", dpid)

    def _install_table_miss(self, connection):
        """
        Table-miss rule: send unknown packets to controller.
        Priority 0 = lowest, catches everything not matched above.
        """
        msg = of.ofp_flow_mod()
        msg.priority = 0
        msg.match = of.ofp_match()
        msg.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
        connection.send(msg)
        log.info("Table-miss rule installed")

    def _install_qos_rules(self, connection):
        """
        Install QoS flow rules for each traffic type.
        Matches on TCP destination port and assigns priority.
        """
        for port, priority, label in QOS_RULES:
            for direction in ['dst', 'src']:
                msg = of.ofp_flow_mod()
                msg.priority = priority
                msg.idle_timeout = 30
                msg.hard_timeout = 120

                msg.match = of.ofp_match()
                msg.match.dl_type = 0x0800
                msg.match.nw_proto = 6

                if direction == 'dst':
                    msg.match.tp_dst = port
                else:
                    msg.match.tp_src = port

                msg.actions.append(
                    of.ofp_action_output(port=of.OFPP_FLOOD)
                )
                connection.send(msg)

            log.info("QoS rule: %-8s | TCP port %-5d | priority %d",
                     label, port, priority)

    def _handle_PacketIn(self, event):
        """
        Handle packets not matched by flow rules.
        Learns MAC addresses and installs unicast forwarding rules.
        """
        packet_data = event.parsed
        if not packet_data.parsed:
            return

        dpid = event.dpid
        in_port = event.port
        connection = event.connection

        src_mac = str(packet_data.src)
        dst_mac = str(packet_data.dst)

        self.mac_table.setdefault(dpid, {})
        self.mac_table[dpid][src_mac] = in_port

        traffic_type = "OTHER"
        ip_pkt = packet_data.find('ipv4')
        if ip_pkt:
            tcp_pkt = packet_data.find('tcp')
            if tcp_pkt:
                for port, priority, label in QOS_RULES:
                    if tcp_pkt.dstport == port or tcp_pkt.srcport == port:
                        traffic_type = label
                        break

        log.debug("PacketIn | dpid=%s | src=%s dst=%s port=%d type=%s",
                  dpid_to_str(dpid), src_mac, dst_mac, in_port, traffic_type)

        if dst_mac in self.mac_table.get(dpid, {}):
            out_port = self.mac_table[dpid][dst_mac]

            msg = of.ofp_flow_mod()
            msg.priority = 1
            msg.idle_timeout = 20
            msg.hard_timeout = 60
            msg.match = of.ofp_match()
            msg.match.in_port = in_port
            msg.match.dl_dst = packet_data.dst
            msg.actions.append(of.ofp_action_output(port=out_port))
            connection.send(msg)

            msg_out = of.ofp_packet_out()
            msg_out.data = event.ofp
            msg_out.actions.append(of.ofp_action_output(port=out_port))
            connection.send(msg_out)
        else:
            msg_out = of.ofp_packet_out()
            msg_out.data = event.ofp
            msg_out.in_port = in_port
            msg_out.actions.append(
                of.ofp_action_output(port=of.OFPP_FLOOD)
            )
            connection.send(msg_out)

    def _handle_FlowRemoved(self, event):
        """Log when a flow rule expires."""
        log.info("Flow removed: priority=%d packets=%d bytes=%d",
                 event.ofp.priority,
                 event.ofp.packet_count,
                 event.ofp.byte_count)


def launch():
    """
    Entry point — POX calls this when the module is loaded.
    Run with: python3 pox.py qos_controller
    """
    core.registerNew(QoSController)
