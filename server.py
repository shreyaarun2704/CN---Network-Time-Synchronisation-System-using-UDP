#!/usr/bin/env python3
import argparse, json, socket, threading, time

def response_for(request, t2=None):
    t2 = time.time() if t2 is None else t2
    t3 = time.time()
    return {"ok": True, "client_id": str(request.get("client_id","unknown")), "t2":t2, "t3":t3, "server_time":t3}

def udp_loop(host, port, stop):
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind((host,port)); s.settimeout(1)
        print(f"[UDP] listening on {host}:{port}",flush=True)
        while not stop.is_set():
            try: data,addr=s.recvfrom(4096)
            except socket.timeout: continue
            except OSError: break
            t2=time.time()
            try:
                req=json.loads(data.decode())
                if not isinstance(req,dict) or req.get("type")!="TIME_REQUEST": raise ValueError()
            except (ValueError,UnicodeDecodeError):
                s.sendto(b'{"ok":false,"error":"invalid request"}',addr); continue
            s.sendto(json.dumps(response_for(req,t2)).encode(),addr)

def handle_tcp(conn,addr):
    with conn:
        conn.settimeout(30); stream=conn.makefile("r",encoding="utf-8")
        for line in stream:
            try:
                req=json.loads(line)
                if not isinstance(req,dict): raise ValueError()
                if req.get("type")=="STATUS":
                    reply={"ok":True,"status":"running","protocols":["TCP","UDP"],"server_time":time.time()}
                elif req.get("type")=="TIME_REQUEST": reply=response_for(req)
                else: reply={"ok":False,"error":"type must be TIME_REQUEST or STATUS"}
            except (ValueError,json.JSONDecodeError): reply={"ok":False,"error":"invalid JSON"}
            try: conn.sendall((json.dumps(reply)+"\n").encode())
            except OSError: break
    print(f"[TCP] disconnected {addr}",flush=True)

def tcp_loop(host,port,stop):
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind((host,port)); s.listen(32); s.settimeout(1)
        print(f"[TCP] listening on {host}:{port}",flush=True)
        while not stop.is_set():
            try: conn,addr=s.accept()
            except socket.timeout: continue
            except OSError: break
            threading.Thread(target=handle_tcp,args=(conn,addr),daemon=True).start()

def main():
    p=argparse.ArgumentParser(); p.add_argument("--host",default="0.0.0.0"); p.add_argument("--port",type=int,default=5005)
    a=p.parse_args()
    if not 1<=a.port<=65535: p.error("invalid port")
    stop=threading.Event()
    threads=[threading.Thread(target=f,args=(a.host,a.port,stop),daemon=True) for f in (udp_loop,tcp_loop)]
    try:
        for t in threads:t.start()
        print("Server ready. Ctrl+C to stop.",flush=True)
        while any(t.is_alive() for t in threads):time.sleep(.2)
    except KeyboardInterrupt:
        stop.set()
        for t in threads:t.join(timeout=2)
if __name__=="__main__":main()
