"""Launch the loopback presentation server. Public hosting uses backend.application directly."""
import argparse,os,sys,threading,webbrowser
from socketserver import ThreadingMixIn
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer
from backend.application import application
from backend.db import connect

class LocalServer(ThreadingMixIn, WSGIServer):
    # Browsers may open a spare connection before sending a request on it.
    daemon_threads = True
    request_queue_size = 16

def local_application(environ, start_response):
    environ["wsgi.multithread"] = True
    return application(environ, start_response)

class Quiet(WSGIRequestHandler):
    timeout = 30
    def log_message(self,fmt,*args):
        pass  # never write search strings to an access log

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--port",type=int)
    p.add_argument("--no-browser",action="store_true")
    args=p.parse_args()
    db=connect()
    count=db.execute("SELECT COUNT(*) FROM resources WHERE status='published'").fetchone()[0]
    db.close()
    for port in ([args.port] if args.port is not None else range(8000,8010)):
        try:
            httpd=make_server("127.0.0.1",port,local_application,server_class=LocalServer,handler_class=Quiet)
            break
        except OSError:
            if args.port is not None:raise
    else:raise SystemExit("Ports 8000–8009 are busy. Run python start.py --port 8080.")
    link=f"http://127.0.0.1:{httpd.server_port}/"
    print(f"CampusConnect is ready: {link}\n{count} published resources. Keep this window open while using CampusConnect. Press Ctrl+C to stop.",flush=True)
    if not args.no_browser:
        threading.Timer(.35,lambda:webbrowser.open(link)).start()
    with httpd:
        try:httpd.serve_forever()
        except KeyboardInterrupt:pass
if __name__=="__main__":main()
