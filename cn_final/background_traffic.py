#!/usr/bin/env python3
import argparse,socket,time
def main():
    p=argparse.ArgumentParser(description="Paced UDP background traffic generator")
    p.add_argument("--host",default="10.0.0.1");p.add_argument("--port",type=int,default=6000)
    p.add_argument("--rate-mbps",type=float,default=9);p.add_argument("--duration",type=float,default=30);a=p.parse_args()
    if a.rate_mbps<=0 or a.duration<=0:p.error("rate and duration must be positive")
    payload=b"BACKGROUND-LOAD"+bytes(1385);interval=len(payload)*8/(a.rate_mbps*1e6)
    end=time.monotonic()+a.duration;sent=0
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        while time.monotonic()<end:
            t=time.monotonic();s.sendto(payload,(a.host,a.port));sent+=1
            wait=interval-(time.monotonic()-t)
            if wait>0:time.sleep(wait)
    print(f"Sent {sent} datagrams; offered rate approximately {sent*len(payload)*8/a.duration/1e6:.2f} Mbps")
if __name__=="__main__":main()
