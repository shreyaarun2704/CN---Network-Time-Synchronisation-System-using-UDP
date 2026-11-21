#!/usr/bin/env python3
import argparse,subprocess
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController,OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel,info

class ClockSyncTopo(Topo):
    def build(self,bw=10,delay="5ms",jitter="0ms"):
        s=self.addSwitch("s1",protocols="OpenFlow13")
        h1=self.addHost("h1",ip="10.0.0.1/24");h2=self.addHost("h2",ip="10.0.0.2/24");h3=self.addHost("h3",ip="10.0.0.3/24")
        opts={"bw":bw,"delay":delay,"jitter":jitter,"use_htb":True}
        self.addLink(h1,s,**opts);self.addLink(h2,s,**opts);self.addLink(h3,s,**opts)

def configure_qos():
    cmds=[
      "ovs-vsctl --if-exists clear Port s1-eth1 qos",
      "ovs-vsctl --if-exists clear Port s1-eth2 qos",
      "ovs-vsctl -- --id=@q0 create Queue other-config:min-rate=1000000 other-config:max-rate=10000000 -- --id=@q1 create Queue other-config:min-rate=8000000 other-config:max-rate=10000000 -- --id=@qos create QoS type=linux-htb other-config:max-rate=10000000 queues:0=@q0 queues:1=@q1 -- set Port s1-eth1 qos=@qos -- set Port s1-eth2 qos=@qos"
    ]
    for cmd in cmds:subprocess.run(cmd,shell=True,check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument("--bw-mbps",type=float,default=10);p.add_argument("--delay-ms",type=float,default=5)
    p.add_argument("--jitter-ms",type=float,default=0);p.add_argument("--controller-ip",default="127.0.0.1")
    p.add_argument("--controller-port",type=int,default=6653);p.add_argument("--no-qos",action="store_true");a=p.parse_args()
    if a.bw_mbps<=0 or a.delay_ms<0 or a.jitter_ms<0:p.error("invalid link settings")
    topo=ClockSyncTopo(bw=a.bw_mbps,delay=f"{a.delay_ms}ms",jitter=f"{a.jitter_ms}ms")
    net=Mininet(topo=topo,controller=None,switch=OVSSwitch,link=TCLink,autoSetMacs=True)
    net.addController("c0",controller=RemoteController,ip=a.controller_ip,port=a.controller_port)
    try:
        net.start()
        if not a.no_qos:
            configure_qos()
            info("*** QoS: queue 1 sync UDP min 8 Mbps; queue 0 other traffic min 1 Mbps\n")
        info("*** h1=server 10.0.0.1 | h2=sync client 10.0.0.2 | h3=load generator 10.0.0.3\n")
        info(f"*** Link: {a.bw_mbps} Mbps, delay {a.delay_ms} ms, jitter {a.jitter_ms} ms\n")
        info("*** Start: h1 python3 server.py --host 10.0.0.1 --port 5005\n")
        CLI(net)
    finally:net.stop()
if __name__=="__main__":setLogLevel("info");main()
