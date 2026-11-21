#!/usr/bin/env python3
import argparse,csv,statistics,time
from client import synchronize_once
def main():
    p=argparse.ArgumentParser(description="Measure RTT and absolute clock synchronization error")
    p.add_argument("--host",required=True);p.add_argument("--port",type=int,default=5005);p.add_argument("--count",type=int,default=30)
    p.add_argument("--interval",type=float,default=.2);p.add_argument("--timeout",type=float,default=2)
    p.add_argument("--clock-skew-ms",type=float,default=20);p.add_argument("--client-id",default="benchmark-client")
    p.add_argument("--csv",default="results.csv");a=p.parse_args()
    if a.count<1 or a.interval<0 or a.timeout<=0:p.error("invalid count/interval/timeout")
    rows=[];fail=0;expected=-a.clock_skew_ms
    for i in range(1,a.count+1):
        try:
            _,rtt,offset=synchronize_once(a.host,a.port,a.timeout,a.client_id,a.clock_skew_ms)
            err=abs(offset-expected)
            rows.append({"sample":i,"rtt_ms":f"{rtt:.6f}","estimated_offset_ms":f"{offset:.6f}","expected_offset_ms":f"{expected:.6f}","absolute_sync_error_ms":f"{err:.6f}"})
            print(f"{i:02d}: RTT={rtt:.3f} ms | offset={offset:+.3f} ms | sync error={err:.3f} ms")
        except (OSError,ValueError) as e:fail+=1;print(f"{i:02d}: FAILED: {e}")
        if i<a.count:time.sleep(a.interval)
    with open(a.csv,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["sample","rtt_ms","estimated_offset_ms","expected_offset_ms","absolute_sync_error_ms"]);w.writeheader();w.writerows(rows)
    print("\n=== PERFORMANCE SUMMARY ===");print(f"Successful samples: {len(rows)}/{a.count}; failed: {fail}")
    if rows:
        r=[float(x["rtt_ms"]) for x in rows];e=[float(x["absolute_sync_error_ms"]) for x in rows]
        print(f"Average RTT: {statistics.mean(r):.3f} ms | Average sync error: {statistics.mean(e):.3f} ms | Maximum error: {max(e):.3f} ms")
    print(f"CSV saved: {a.csv}")
if __name__=="__main__":main()
