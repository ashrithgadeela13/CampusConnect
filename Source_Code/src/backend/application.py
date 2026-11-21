"""WSGI entry point shared by desktop demo and independent hosting."""
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs,urlparse
import json, mimetypes, os, sqlite3, sys
from . import auth,directory,guide_feedback,services
from .classifier import classify,directory_search
from .common import Problem,Reply,only,text
from .db import ROOT,connect
PUBLIC=(ROOT/"public").resolve()
SAFE=[("X-Content-Type-Options","nosniff"),("Referrer-Policy","strict-origin-when-cross-origin"),("X-Frame-Options","DENY"),
      ("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'")]
def origin_for(env):
    public=os.environ.get("CAMPUSCONNECT_ORIGIN","").rstrip("/")
    if public:return public
    scheme=env.get("wsgi.url_scheme","http")
    return scheme+"://"+env.get("HTTP_HOST","localhost")

def read_body(env):
    if env.get("HTTP_ORIGIN")!=origin_for(env):raise Problem(403,"This request could not be verified. Reload and try again.")
    host=urlparse(origin_for(env))
    if host.scheme!="https" and host.hostname not in ("localhost","127.0.0.1","::1"):raise Problem(403,"Sign in and make changes over HTTPS.")
    if env.get("CONTENT_TYPE","").split(";")[0].lower()!="application/json":raise Problem(415,"Send a JSON request.")
    try:size=int(env.get("CONTENT_LENGTH") or 0)
    except ValueError:raise Problem(400,"Invalid request length.")
    if not 0<size<=32768:raise Problem(413,"The request is missing or too large.")
    try:d=json.loads(env["wsgi.input"].read(size))
    except (ValueError,UnicodeError,RecursionError):raise Problem(400,"Invalid JSON.")
    if not isinstance(d,dict):raise Problem(422,"Send a JSON object.")
    return d

def dispatch(db,e,method,path,q,b):
    a=auth.account(db,e)
    if path.startswith("/api/auth/") and method=="POST":return auth.process(db,e,path[10:],b,origin_for(e).startswith("https://"))
    if path=="/api/health" and method=="GET":
        db.execute("SELECT COUNT(*) FROM usage_daily").fetchone();return {"status":"ok"}
    if path=="/api/bootstrap" and method=="GET":
        return {"account":a,"categories":directory.categories(db),"resources":directory.resources(db,bool(a and a["effectiveRole"]=="admin"))}
    if path=="/api/account/mode" and method=="POST":
        auth.require(a);only(b,["mode"])
        if a["role"]!="admin":raise Problem(403,"Only administrators can use student preview.")
        if b.get("mode") not in ("student","admin"):raise Problem(422,"Choose a valid mode.")
        db.execute("UPDATE app_users SET student_preview=? WHERE id=?",(int(b["mode"]=="student"),a["id"]));return {"account":auth.account(db,e)}
    if path=="/api/resources":
        if method=="GET":
            all_=q.get("status")=="all"
            if all_:auth.require(a,True)
            return {"resources":directory.resources(db,all_,q.get("category",""),q.get("q","")[:200])}
        if method=="POST":return directory.change_resource(db,a,b)
    if path.startswith("/api/resources/") and method=="PATCH":
        return directory.change_resource(db,a,b,path[15:])
    if path=="/api/categories":
        if method=="GET":return {"categories":directory.categories(db)}
        if method=="POST":return directory.change_category(db,a,b)
    if path=="/api/personal":
        if method=="GET":return services.personal(db,a)
        if method=="POST":return services.edit_personal(db,a,b)
    if path=="/api/notices":
        if method=="GET":
            manage=q.get("manage")=="1"
            if manage:auth.require(a,True)
            return {"notices":services.notices(db,manage)}
        if method=="POST":return services.edit_notice(db,a,b)
    if path=="/api/search" and method=="POST":
        only(b,["query","category"])
        question=text(b,"query",1,200); cat=text(b,"category",0,80)
        return {"resourceIds":directory_search(question,directory.resources(db,category=cat))}
    if path=="/api/guide" and method=="POST":
        only(b,["question","topic"])
        hint=b.get("topic")
        if hint is not None:
            if not isinstance(hint,dict):raise Problem(422,"Invalid topic suggestion.")
            only(hint,["category","score"])
            text(hint,"category",1,80);score=hint.get("score")
            if type(score) not in (int,float) or not 0<=score<=1:raise Problem(422,"Invalid topic score.")
        question=text(b,"question",3,500)
        resources=directory.resources(db)
        result=classify(question,directory.categories(db),resources,neural_hint=hint)
        guide_feedback.attach_receipt(db,question,result,resources)
        services.count(db,"guide",result["categories"][0]["id"] if result["categories"] else "no_match");return result
    if path=="/api/guide/feedback" and method=="POST":
        return guide_feedback.submit(db,b)
    if path=="/api/admin/unanswered":
        if method=="GET":return guide_feedback.dashboard(db,a,q.get("page","0"))
        if method=="POST":return guide_feedback.review(db,a,b)
    if path=="/api/activity" and method=="POST":return services.activity(db,a,b)
    if path=="/api/analytics" and method=="GET":return services.analytics(db,a,q.get("days","7"))
    raise Problem(404,"Endpoint not found.")

def application(env,start_response):
    path=env.get("PATH_INFO","/");method=env.get("REQUEST_METHOD","GET").upper()
    if path in ("/","/login","/logout","/register","/favicon.svg") or path.startswith("/assets/"):
        if method not in ("GET","HEAD"):return send(start_response,405,b"Method not allowed","text/plain")
        file=(PUBLIC/(path.lstrip("/") if path=="/favicon.svg" or path.startswith("/assets/") else "index.html")).resolve()
        if not file.is_relative_to(PUBLIC) or not file.is_file():return send(start_response,404,b"Not found","text/plain")
        content_type={".js":"text/javascript; charset=utf-8",".css":"text/css; charset=utf-8",".svg":"image/svg+xml",".html":"text/html; charset=utf-8"}.get(file.suffix,"application/octet-stream")
        return send(start_response,200,file.read_bytes(),content_type,[("Cache-Control","public, max-age=31536000, immutable" if path.startswith("/assets/") else "no-cache")],method=="HEAD")
    db=None
    try:
        if not path.startswith("/api/"):raise Problem(404,"Page not found.")
        body=read_body(env) if method not in ("GET","HEAD") else {}
        query={k:v[-1] for k,v in parse_qs(env.get("QUERY_STRING","")).items()}
        db=connect()
        value=dispatch(db,env,method,path,query,body)
        db.commit();result=value if isinstance(value,Reply) else Reply(value)
    except Problem as exc:
        if db:db.rollback()
        result=Reply({"error":exc.message},exc.status)
    except Exception as exc:
        if db:db.rollback()
        # Do not log bodies, passwords or search terms.
        print("CampusConnect request failed:",type(exc).__name__, file=sys.stderr)
        result=Reply({"error":"Could not complete the request."},500)
    finally:
        if db:db.close()
    return send(start_response,result.status,json.dumps(result.content,ensure_ascii=False).encode(),"application/json; charset=utf-8",[("Cache-Control","no-store"),*result.headers])

def send(start,status,data,mime,headers=(),head=False):
    start(f"{status} {HTTPStatus(status).phrase}",[("Content-Type",mime),("Content-Length",str(len(data))),*SAFE,*headers])
    return [b"" if head else data]
