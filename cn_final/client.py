#!/usr/bin/env python3
import argparse, json, socket, time

def parse_server_reply(data):
    obj=json.loads(data.decode("utf-8"))
    if not isinstance(obj,dict) or "t2" not in obj or "t3" not in obj:
        raise ValueError("server reply must contain t2 and t3")
    return float(obj["t2"]),float(obj["t3"])

def synchronize_once(host,port,timeout,client_id,clock_skew_ms=0.0):
    skew=clock_skew_ms/1000.0
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        s.settimeout(timeout); t1=time.time()+skew
        s.sendto(json.dumps({"type":"TIME_REQUEST","client_id":client_id,"t1":t1}).encode(),(host,port))
        start=time.perf_counter(); data,addr=s.recvfrom(4096); elapsed=time.perf_counter()-start
        t4=time.time()+skew
    t2,t3=parse_server_reply(data)
    offset=((t2-t1)+(t3-t4))/2.0
    delay=max(0.0,elapsed-max(0.0,t3-t2))
    return addr,delay*1000.0,offset*1000.0

def main():
    p=argparse.ArgumentParser(); p.add_argument("--host",default="127.0.0.1"); p.add_argument("--port",type=int,default=5005)
    p.add_argument("--timeout",type=float,default=2); p.add_argument("--interval",type=float,default=1)
    p.add_argument("--count",type=int,default=1); p.add_argument("--client-id",default="client-1")
    p.add_argument("--clock-skew-ms",type=float,default=0)
    a=p.parse_args()
    if not 1<=a.port<=65535 or a.timeout<=0 or a.interval<0 or a.count<0:p.error("invalid argument")
    n=0
    try:
        while a.count==0 or n<a.count:
            n+=1
            try:
                addr,rtt,offset=synchronize_once(a.host,a.port,a.timeout,a.client_id,a.clock_skew_ms)
                expected=-a.clock_skew_ms
                print(f"sample={n} peer={addr[0]} RTT={rtt:.3f} ms offset={offset:+.3f} ms expected={expected:+.3f} ms sync_error={abs(offset-expected):.3f} ms")
            except (OSError,ValueError) as e:print(f"sample={n} failed: {e}")
            if a.count==0 or n<a.count:time.sleep(a.interval)
    except KeyboardInterrupt:print("\nClient stopped.")
if __name__=="__main__":main()
