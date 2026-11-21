#!/usr/bin/env python3
import argparse,json,socket,time
def request(host,port,msg,timeout):
    with socket.create_connection((host,port),timeout=timeout) as s:
        s.settimeout(timeout); s.sendall((json.dumps(msg)+"\n").encode())
        line=s.makefile("r",encoding="utf-8").readline()
        if not line:raise ConnectionError("server closed without response")
        return json.loads(line)
def main():
    p=argparse.ArgumentParser();p.add_argument("--host",default="127.0.0.1");p.add_argument("--port",type=int,default=5005)
    p.add_argument("--timeout",type=float,default=2);p.add_argument("--client-id",default="tcp-client-1");p.add_argument("--status",action="store_true")
    a=p.parse_args();msg={"type":"STATUS"} if a.status else {"type":"TIME_REQUEST","client_id":a.client_id,"t1":time.time()}
    try:print(json.dumps(request(a.host,a.port,msg,a.timeout),indent=2))
    except (OSError,ValueError) as e:raise SystemExit(f"TCP request failed: {e}")
if __name__=="__main__":main()
