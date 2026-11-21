from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER,MAIN_DISPATCHER,set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet,ethernet,ether_types,ipv4,udp

class ClockSyncLearningSwitch(app_manager.RyuApp):
    OFP_VERSIONS=[ofproto_v1_3.OFP_VERSION]
    SYNC_PORT=5005
    SYNC_QUEUE=1
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.mac_to_port={}
    def add_flow(self,dp,priority,match,actions,idle_timeout=0):
        p,o=dp.ofproto_parser,dp.ofproto
        inst=[p.OFPInstructionActions(o.OFPIT_APPLY_ACTIONS,actions)]
        dp.send_msg(p.OFPFlowMod(datapath=dp,priority=priority,match=match,instructions=inst,idle_timeout=idle_timeout))
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures,CONFIG_DISPATCHER)
    def switch_features(self,ev):
        dp=ev.msg.datapath;o,p=dp.ofproto,dp.ofproto_parser
        self.add_flow(dp,0,p.OFPMatch(),[p.OFPActionOutput(o.OFPP_CONTROLLER,o.OFPCML_NO_BUFFER)])
        self.logger.info("OpenFlow 1.3 switch connected: %s",dp.id)
    @set_ev_cls(ofp_event.EventOFPPacketIn,MAIN_DISPATCHER)
    def packet_in(self,ev):
        msg,dp=ev.msg,ev.msg.datapath;o,p=dp.ofproto,dp.ofproto_parser
        in_port=msg.match["in_port"];pkt=packet.Packet(msg.data);eth=pkt.get_protocol(ethernet.ethernet)
        if eth is None or eth.ethertype==ether_types.ETH_TYPE_LLDP:return
        self.mac_to_port.setdefault(dp.id,{})[eth.src]=in_port
        out=self.mac_to_port[dp.id].get(eth.dst,o.OFPP_FLOOD)
        ip=pkt.get_protocol(ipv4.ipv4);u=pkt.get_protocol(udp.udp)
        sync=ip is not None and u is not None and (u.src_port==self.SYNC_PORT or u.dst_port==self.SYNC_PORT)
        if out==o.OFPP_FLOOD:
            actions=[p.OFPActionOutput(o.OFPP_FLOOD)]
        else:
            fields={"in_port":in_port,"eth_src":eth.src,"eth_dst":eth.dst}
            actions=[]
            if sync:
                fields.update({"eth_type":0x0800,"ip_proto":17,"ipv4_src":ip.src,"ipv4_dst":ip.dst})
                if u.dst_port==self.SYNC_PORT:fields["udp_dst"]=self.SYNC_PORT
                else:fields["udp_src"]=self.SYNC_PORT
                actions.append(p.OFPActionSetQueue(self.SYNC_QUEUE));priority=100
                self.logger.info("SYNC UDP prioritized with queue %s",self.SYNC_QUEUE)
            else:priority=10
            actions.append(p.OFPActionOutput(out))
            self.add_flow(dp,priority,p.OFPMatch(**fields),actions,idle_timeout=60)
        data=None if msg.buffer_id!=o.OFP_NO_BUFFER else msg.data
        dp.send_msg(p.OFPPacketOut(datapath=dp,buffer_id=msg.buffer_id,in_port=in_port,actions=actions,data=data))
