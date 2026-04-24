# Simple QoS Priority Controller — SDN Mininet + POX Project

## Problem Statement
Implement an SDN-based QoS solution using Mininet and POX controller (OpenFlow 1.0)
that prioritizes network traffic by type to minimize latency for real-time flows.

## Traffic Priority Mapping
| Traffic Type | TCP Port | OpenFlow Priority |
|---|---|---|
| Video Streaming | 5001 | 300 (Highest) |
| VoIP | 5004 | 200 |
| HTTP/Web | 80 | 100 |
| FTP/Bulk | 21 | 50 (Lowest) |
| Other | - | 1 (Default) |

## Setup & Execution

### Prerequisites
- Ubuntu 20.04 or 22.04 VM
- Mininet, Open vSwitch, Python3, Git

### Installation
```bash
sudo apt update && sudo apt install mininet openvswitch-switch git python3 iperf -y
cd ~
git clone https://github.com/noxrepo/pox.git
cp qos_controller.py ~/pox/ext/
```

### Running the project
Terminal 1 — Start POX controller:
```bash
cd ~/pox
python3 pox.py log.level --DEBUG qos_controller
```

Terminal 2 — Start Mininet:
```bash
sudo python3 qos_topology.py
```

### Test commands
```
pingall                                      # connectivity test
h1 ping -c 5 h4                             # latency test
h3 iperf -s -p 5001 &                       # start video server
h1 iperf -c 10.0.0.3 -p 5001 -t 10 -i 1   # video throughput
h3 iperf -s -p 21 &                         # start FTP server
h4 iperf -c 10.0.0.3 -p 21 -t 10 -i 1     # FTP throughput
sh ovs-ofctl dump-flows s1                  # show flow rules
exit && sudo mn -c                          # cleanup
```

## Expected Output
- pingall: 0% packet loss (12/12 received)
- Flow table shows priority=300 (video), 200 (voip), 100 (http), 50 (ftp)
- Video (port 5001, priority 300) achieves better throughput than FTP (port 21)

## Test Scenarios
1. **Connectivity test**: pingall confirms all 4 hosts reachable through QoS switch
2. **QoS throughput comparison**: simultaneous iperf video vs FTP shows priority effect

## References
- https://mininet.org/overview/
- https://github.com/noxrepo/pox
- https://opennetworking.org/technical-communities/areas/specification/open-datapath/

