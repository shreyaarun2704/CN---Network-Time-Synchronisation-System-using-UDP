# Network Time Synchronization over TCP/UDP + SDN — Demo 2

## Architecture
- h1 (10.0.0.1): reference time server; UDP and TCP port 5005.
- h2 (10.0.0.2): UDP synchronization client and TCP client.
- h3 (10.0.0.3): background UDP load generator, destination port 6000.
- s1: OpenFlow 1.3 Open vSwitch controlled by Ryu on TCP port 6653.

All hosts connect through s1. UDP clock requests/responses use four timestamps t1–t4. TCP provides time/status JSON-line requests. The controller learns MAC-to-port mappings and classifies UDP source/destination port 5005.

## Demo 1 functionality retained
UDP four-timestamp clock offset and RTT; TCP time/status requests; concurrent TCP handling; Mininet/OpenFlow learning switch; repeated client samples.

## Demo 2 implementation
1. **Prioritization:** Ryu installs priority-100 OpenFlow rules for UDP port 5005 and applies `OFPActionSetQueue(1)`. Other flows use the normal queue. OVS HTB QoS reserves 8 Mbps minimum for queue 1 and 1 Mbps minimum for queue 0 on switch egress ports s1-eth1 and s1-eth2. This is bandwidth-reservation QoS, not strict-priority scheduling.
2. **Controlled delay:** Mininet TCLink sets bandwidth, one-way delay and jitter. Defaults: 10 Mbps, 5 ms, 0 ms jitter.
3. **Synchronization error:** `measure.py` injects a known clock skew into application timestamps only (never changes OS clock). Expected server-minus-client offset is `-clock_skew_ms`; absolute error = `abs(estimated_offset - expected_offset)`. It records RTT, estimated offset, expected offset and error in CSV.
4. **Congestion:** h3 sends paced background UDP datagrams to h1, competing for the same switch egress toward h1. Compare QoS enabled/disabled and congestion/no congestion.

## Requirements
Linux VM, Python 3, Mininet, Open vSwitch with OpenFlow 1.3 and linux-htb QoS, Ryu (`ryu-manager`), root privileges. Socket apps use Python standard library.

## Run the final demo
Terminal 1:
```bash
ryu-manager sdn_controller.py
```
Terminal 2:
```bash
sudo python3 topology.py --bw-mbps 10 --delay-ms 5 --jitter-ms 0
```
At Mininet CLI:
```text
pingall
h1 python3 server.py --host 10.0.0.1 --port 5005 &
h2 python3 measure.py --host 10.0.0.1 --count 30 --interval 0.2 --clock-skew-ms 20 --csv baseline.csv
```
Congestion run (while measurement is running, use separate Mininet xterms/CLI commands):
```text
h3 python3 background_traffic.py --host 10.0.0.1 --rate-mbps 9 --duration 40 &
h2 python3 measure.py --host 10.0.0.1 --count 30 --interval 0.2 --clock-skew-ms 20 --csv congestion_qos.csv
```
For no-QoS comparison, exit Mininet and restart:
```bash
sudo python3 topology.py --bw-mbps 10 --delay-ms 5 --jitter-ms 0 --no-qos
```
Repeat the same congestion measurement and save as `congestion_no_qos.csv`.

TCP checks:
```text
h2 python3 tcp_client.py --host 10.0.0.1 --port 5005
h2 python3 tcp_client.py --host 10.0.0.1 --port 5005 --status
```
Verify OpenFlow and QoS from Linux shell:
```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
sudo ovs-vsctl list Port s1-eth1
sudo ovs-vsctl list Port s1-eth2
sudo ovs-vsctl list Queue
```
Look for UDP port 5005 rules with higher priority and queue 1 actions; verify QoS is attached to both switch egress ports.

## Local socket tests (without Mininet)
```bash
python3 server.py --host 127.0.0.1 --port 5005
python3 client.py --host 127.0.0.1 --port 5005 --count 5
python3 measure.py --host 127.0.0.1 --count 20 --clock-skew-ms 20 --csv local.csv
python3 tcp_client.py --host 127.0.0.1 --port 5005 --status
python3 -m unittest -v
```

## Performance table — fill with measured values
| Condition | Average RTT (ms) | Average absolute sync error (ms) | Maximum error (ms) | Successful samples |
|---|---:|---:|---:|---:|
| No congestion, QoS enabled | 13.006 | 0.317 | 1.110 | 30/30 |
| Congestion, QoS enabled | 12.841 | 0.279 | 0.865 | 30/30 |
| Congestion, QoS disabled | 23.960 | 0.463 | 1.796 | 30/30 |

Do not invent result values. Report the measurements from your own VM and discuss whether QoS helped.

## D2 rubric mapping
| Rubric component | Project evidence |
|---|---|
| Complete Application Functionality (4) | UDP synchronization, TCP requests/status, repeated samples, concurrent TCP handlers |
| Dynamic SDN Functionality (6) | MAC learning plus dynamic UDP/5005 classification and queue selection |
| Challenging Scenario / Robustness (4) | Configurable delay/jitter and h3-generated congestion |
| Performance Evaluation & Comparison (5) | CSV RTT/error metrics and QoS/no-QoS comparison |
| Documentation, Final Demo & Viva (6) | Architecture, setup, commands, verification, result table |

## Limitations to disclose
- Clock skew is simulated in application timestamps; system time is not changed.
- Error is calculated against known injected skew, not GPS/NTP hardware ground truth.
- QoS behavior depends on OVS/kernel linux-htb support and the actual bottleneck; verify queues and flows before claiming prioritization.
- This is an educational single-switch controller, not production-grade SDN.
