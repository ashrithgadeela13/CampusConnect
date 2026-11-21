"""Run against the real HTTP application and a disposable SQLite database."""
import http.cookiejar,json,os,pathlib,re,socket,subprocess,sys,tempfile,unittest,urllib.error,urllib.request
from contextlib import closing
from urllib.parse import urlsplit
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend import auth
from backend.db import connect
from backend.classifier import classify
from backend import directory
PW="Example-only-passphrase-28"

class Website(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.old_data=os.environ.get("CAMPUSCONNECT_DATA_DIR")
        cls.old_origin=os.environ.pop("CAMPUSCONNECT_ORIGIN",None)
        os.environ["CAMPUSCONNECT_DATA_DIR"]=cls.temp.name
        with closing(connect()) as db:auth.create(db,"demo-admin",PW,"Test Admin","admin");db.commit()
        cls.launch()
    @classmethod
    def launch(cls):
        cls.server=subprocess.Popen([sys.executable,"-u","start.py","--no-browser","--port","0"],cwd=ROOT,env=os.environ.copy(),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        line=cls.server.stdout.readline().strip()
        if "http://" not in line:raise RuntimeError("Local server did not start: "+line)
        cls.base=line.split("http://",1)[1].rstrip("/");cls.base="http://"+cls.base
    @classmethod
    def stop(cls):
        cls.server.terminate();cls.server.wait(timeout=7);cls.server.stdout.close()
    @classmethod
    def tearDownClass(cls):
        cls.stop();cls.temp.cleanup()
        if cls.old_data is None:os.environ.pop("CAMPUSCONNECT_DATA_DIR",None)
        else:os.environ["CAMPUSCONNECT_DATA_DIR"]=cls.old_data
        if cls.old_origin:os.environ["CAMPUSCONNECT_ORIGIN"]=cls.old_origin
    def client(self):
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def send(self,client,path,body=None,method=None,**headers):
        verb=method or ("GET" if body is None else "POST")
        hdr={"Origin":self.base,"Content-Type":"application/json",**headers}
        req=urllib.request.Request(self.base+path,data=None if body is None else json.dumps(body).encode(),headers=hdr,method=verb)
        try:
            result=client.open(req,timeout=7)
        except urllib.error.HTTPError as e:result=e
        with result as r:
            raw=r.read();value=json.loads(raw) if "application/json" in r.headers.get("Content-Type","") else raw.decode(errors="replace")
            return r.status,value,r.headers
    def admin(self):
        c=self.client();self.assertEqual(self.send(c,"/api/auth/login",{"username":"demo-admin","password":PW})[0],200);return c
    def student(self,username):
        c=self.client();self.assertEqual(self.send(c,"/api/auth/register",{"username":username,"name":"Test Student","password":PW})[0],200);return c
    def test_guide_feedback_and_admin_dashboard(self):
        guest=self.client()
        student=self.student("student-feedback")
        admin=self.admin()
        guide="/api/guide"
        feedback=guide+"/feedback"
        dashboard="/api/admin/unanswered"
        self.assertEqual(self.send(guest,dashboard)[0],401)
        self.assertEqual(self.send(student,dashboard)[0],403)
        self.assertEqual(self.send(student,dashboard,{"id":"unused","reviewed":True})[0],403)

        question="I lost my student ID."
        result=self.send(guest,guide,{"question":question})[1]
        receipt=result["feedbackReceipt"]
        self.assertEqual(self.send(guest,feedback,{"receipt":receipt+"x","solved":False})[0],422)
        vote={"receipt":receipt,"solved":False,"reason":"Wrong office"}
        self.assertEqual(self.send(guest,feedback,vote)[0],200)
        self.assertEqual(self.send(guest,feedback,vote)[0],200)
        rows=self.send(admin,dashboard)[1]["items"]
        matches=[row for row in rows if row["question"]==question]
        self.assertEqual(len(matches),1)
        match=matches[0]
        self.assertEqual(match["reason"],"Wrong office")
        self.assertIn("Mav Card Office",match["offices"])
        self.assertEqual(self.send(admin,dashboard,{"id":match["id"],"reviewed":True})[0],200)
        reviewed=next(row for row in self.send(admin,dashboard)[1]["items"] if row["id"]==match["id"])
        self.assertIsNotNone(reviewed["reviewed_at"])

        unmatched="Give me a recipe for blueberry muffins."
        result=self.send(guest,guide,{"question":unmatched})[1]
        self.assertEqual(result["state"],"none")
        self.assertTrue(any(row["question"]==unmatched for row in self.send(admin,dashboard)[1]["items"]))
        self.assertEqual(self.send(guest,feedback,{"receipt":result["feedbackReceipt"],"solved":True})[0],200)
        report=self.send(admin,dashboard)[1]
        self.assertFalse(any(row["question"]==unmatched for row in report["items"]))
        self.assertGreaterEqual(report["counts"]["yes"],1)
        self.assertGreaterEqual(report["counts"]["noMatch"],1)

    def test_idle_connection_does_not_block_a_second_window(self):
        url=urlsplit(self.base)
        with socket.create_connection((url.hostname,url.port),timeout=4) as idle:
            # Leave a request incomplete, as if one window opened a connection early.
            idle.sendall(b"GET /api/health HTTP/1.0\r\n")
            with urllib.request.urlopen(self.base+"/api/bootstrap",timeout=4) as other:
                self.assertEqual(len(json.load(other)["resources"]),30)
            idle.sendall(b"\r\n")
            with idle.makefile("rb") as reply:
                self.assertIn(b"200 OK",reply.readline())

    def test_guest_directory_assets_and_filters(self):
        c=self.client();code,b,_=self.send(c,"/api/bootstrap");self.assertEqual((code,len(b["resources"]),len(b["categories"]),b["account"]),(200,30,11,None))
        self.assertEqual(self.send(c,"/api/resources?q=3D&category=library")[1]["resources"][0]["id"],"fablab")
        for url in ("/","/register","/login","/logout"):
            status,body,h=self.send(c,url);self.assertEqual(status,200);self.assertIn("CampusConnect",body)
        bundle=re.search(r'<script[^>]*src="([^"]+)"',body).group(1);status,js,_=self.send(c,bundle);self.assertEqual(status,200);self.assertNotIn("signin-with-chatgpt",js)
        self.assertEqual(self.send(c,"/instance/campusconnect.sqlite3")[0],404)
    def test_native_auth_sessions_and_forgery(self):
        c=self.client()
        self.assertEqual(self.send(c,"/api/auth/register",{"username":"attacker","name":"test","password":PW,"role":"admin"})[0],422)
        self.assertEqual(self.send(c,"/api/auth/register",{"username":"attacker","name":"test","password":PW},Origin="https://other.test")[0],403)
        status,_,h=self.send(c,"/api/auth/register",{"username":"student-auth","name":"Student","password":PW})
        self.assertEqual(status,200);cookie=h.get("Set-Cookie");self.assertIn("HttpOnly",cookie);self.assertIn("SameSite=Lax",cookie)
        a=self.send(c,"/api/bootstrap")[1]["account"];self.assertEqual((a["name"],a["role"]),("Student","student"))
        self.assertEqual(self.send(self.client(),"/api/bootstrap",**{"oai-authenticated-user-id":"pretend-admin","X-Forwarded-User":"demo-admin"})[1]["account"],None)
        self.assertEqual(self.send(self.client(),"/api/auth/register",{"username":"STUDENT-AUTH","name":"Other","password":PW})[0],409)
        self.assertEqual(self.send(c,"/api/auth/logout",{})[0],200)
        self.assertEqual(self.send(self.client(),"/api/personal",Cookie=cookie.split(";")[0])[0],401)
        self.assertEqual(self.send(c,"/api/auth/login",{"username":"student-auth","password":"incorrect-value"})[0],401)
        self.assertEqual(self.send(c,"/api/auth/login",{"username":"STUDENT-AUTH","password":PW})[0],200)
        with closing(connect()) as db:
            row=db.execute("SELECT salt,verifier FROM credentials WHERE username='student-auth'").fetchone()
            self.assertEqual((len(row[0]),len(row[1])),(16,32));self.assertNotEqual(row[1],PW.encode())
            self.assertEqual(db.execute("SELECT max(length(digest)) FROM sessions").fetchone()[0],32)
    def test_bookmarks_are_private_and_persist_after_server_restart(self):
        a=self.student("student-favorites");b=self.student("student-other")
        self.assertEqual(self.send(a,"/api/personal",{"action":"save","id":"mav-card","saved":True})[0],200)
        self.send(a,"/api/activity",{"kind":"view","id":"mav-card"})
        self.send(a,"/api/activity",{"kind":"view","id":"mav-card"})
        self.assertEqual(self.send(b,"/api/personal")[1],{"saved":[],"recent":[]})
        self.assertEqual(self.send(b,"/api/personal",{"action":"clearRecent","userId":"another"})[0],422)
        type(self).stop();type(self).launch()
        self.assertEqual(self.send(a,"/api/personal")[1],{"saved":["mav-card"],"recent":["mav-card"]})
        self.assertEqual(self.send(a,"/api/personal",{"action":"clearRecent"})[1]["recent"],[])
        self.assertEqual(self.send(a,"/api/personal",{"action":"save","id":"mav-card","saved":False})[1]["saved"],[])
    def test_resources_categories_notices_and_roles(self):
        guest=self.client();s=self.student("student-management");a=self.admin()
        for route in ("/api/categories","/api/notices","/api/resources"):
            self.assertEqual(self.send(s,route,{})[0],403)
        self.assertEqual(self.send(s,"/api/analytics")[0],403)
        self.assertEqual(self.send(s,"/api/account/mode",{"mode":"admin"})[0],403)
        original=self.send(a,"/api/resources?status=all")[1]["resources"][0]
        status,d,_=self.send(a,"/api/categories",{"action":"create","name":"Acceptance test"});self.assertEqual(status,201)
        cid=next(c["id"] for c in d["categories"] if c["name"]=="Acceptance test")
        self.assertEqual(self.send(a,"/api/categories",{"action":"create","name":"ACCEPTANCE TEST"})[0],409)
        self.assertEqual(self.send(a,"/api/categories",{"action":"rename","id":cid,"name":"New title"})[0],200)
        self.assertEqual(self.send(a,"/api/resources",{**original,"url":"javascript:alert(1)"})[0],422)
        status,d,_=self.send(a,"/api/resources",{**original,"name":"Acceptance resource","category_id":cid});self.assertEqual(status,201)
        r=d["resource"];rid=r["id"]; self.assertEqual(self.send(a,"/api/categories",{"action":"remove","id":cid})[0],409)
        self.send(s,"/api/personal",{"action":"save","id":rid,"saved":True})
        status,d,_=self.send(a,"/api/resources/"+rid,{**r,"status":"archived"},method="PATCH");self.assertEqual(status,200)
        self.assertNotIn(rid,self.send(s,"/api/personal")[1]["saved"])
        self.assertEqual(self.send(a,"/api/resources/"+rid,r,method="PATCH")[0],409)
        self.assertEqual(self.send(a,"/api/resources/"+rid,{**d["resource"],"category_id":"academics","status":"published"},method="PATCH")[0],200)
        self.assertEqual(self.send(a,"/api/categories",{"action":"remove","id":cid})[0],200)
        note={"title":"Acceptance notice","body":"An isolated testing notice.","category_id":None,"status":"draft","expires_on":""}
        status,d,_=self.send(a,"/api/notices",note);self.assertEqual(status,201)
        current=next(n for n in d["notices"] if n["title"]==note["title"])
        def ids():return [n["id"] for n in self.send(guest,"/api/notices")[1]["notices"]]
        self.assertNotIn(current["id"],ids())
        def edit(status,expires=""):
            nonlocal current
            code,d,_=self.send(a,"/api/notices",{**note,"id":current["id"],"version":current["version"],"status":status,"expires_on":expires});self.assertEqual(code,200)
            current=next(n for n in d["notices"] if n["title"]==note["title"])
        edit("published");self.assertIn(current["id"],ids());edit("published","2000-01-01");self.assertNotIn(current["id"],ids());edit("archived");self.assertNotIn(current["id"],ids())
        self.assertEqual(self.send(a,"/api/account/mode",{"mode":"student"})[1]["account"]["effectiveRole"],"student")
        self.assertEqual(self.send(a,"/api/notices?manage=1")[0],403)
        self.assertEqual(self.send(a,"/api/account/mode",{"mode":"admin"})[1]["account"]["effectiveRole"],"admin")
    def test_guide_metrics_and_privacy(self):
        c=self.client();a=self.admin();pre=self.send(a,"/api/analytics")[1]["metrics"]
        q="I lost my student ID."
        self.assertIn("mav-card",self.send(c,"/api/guide",{"question":q})[1]["resourceIds"])
        self.assertEqual(self.send(c,"/api/guide",{"question":"What is the capital of Finland?"})[1]["state"],"none")
        self.send(c,"/api/activity",{"kind":"view","id":"mav-card"});self.send(c,"/api/activity",{"kind":"search","found":False});self.send(c,"/api/activity",{"kind":"guided","id":"library"})
        self.assertEqual(self.send(c,"/api/activity",{"kind":"search","found":False,"query":q})[0],422)
        d=self.send(a,"/api/analytics?days=7")[1];self.assertEqual(len(d["daily"]),7)
        self.assertEqual(len(self.send(a,"/api/analytics?days=30")[1]["daily"]),30)
        for metric,change in {"views":1,"guides":3,"unmatched":1,"empty":1,"searches":1}.items():self.assertEqual(d["metrics"][metric]-pre[metric],change)
        self.assertNotIn(q,json.dumps(d))
        with closing(connect()) as db:self.assertEqual([r[1] for r in db.execute("pragma table_info(usage_daily)")],["day","kind","bucket","total"])
    def test_home_and_guide_share_service_search(self):
        c=self.client();q="I want to drop a course and do it next semester"
        code,data,_=self.send(c,"/api/search",{"query":q,"category":""})
        self.assertEqual(code,200);self.assertEqual(data["resourceIds"][0],"academic-advising")
        self.assertEqual(self.send(c,"/api/guide",{"question":q})[1]["resourceIds"][0],data["resourceIds"][0])
        scoped=self.send(c,"/api/search",{"query":"printer","category":"library"})[1]["resourceIds"]
        self.assertIn("fablab",scoped);self.assertNotIn("it-service-desk",scoped)
        self.assertEqual(self.send(c,"/api/search",{"query":" ","category":""})[0],422)
        self.assertEqual(self.send(c,"/api/search",{"query":q,"status":"all"})[0],422)

    def test_legacy_client_topic_hint(self):
        client=self.client()
        positive={"question":"My financial aid didn't come through.","topic":{"category":"money","score":.97}}
        status,body=self.send(client,"/api/guide",positive)[:2]
        self.assertEqual(status,200);self.assertEqual(body["resourceIds"][0],"financial-aid")
        # The older topic hint cannot create a match for an unrelated question.
        out={"question":"What is the capital of Finland?","topic":{"category":"money","score":1}}
        self.assertEqual(self.send(client,"/api/guide",out)[1]["state"],"none")
        for bad in ({"category":"money","score":2},{"category":"money","score":True},"money"):
            self.assertEqual(self.send(client,"/api/guide",{"question":"Financial aid","topic":bad})[0],422)
        # Clients can ask the new local server directly.
        self.assertIn("mav-card",self.send(client,"/api/guide",{"question":"I lost my student ID."})[1]["resourceIds"])

    def test_classifier_holdout(self):
        with closing(connect()) as db:cats=directory.categories(db);resources=directory.resources(db)
        held=json.loads((ROOT/"ai/heldout.json").read_text());probes=json.loads((ROOT/"ai/unsupported.json").read_text())
        found=[(expected,[x["id"] for x in classify(q,cats,resources)["categories"]]) for q,expected in held]
        top1=sum(bool(p) and p[0]==e for e,p in found);top3=sum(e in p for e,p in found)
        rejected=sum(classify(q,cats,resources)["state"]=="none" for q in probes);print(f"Classifier: first {top1}/{len(found)}, top three {top3}/{len(found)}, unsupported rejected {rejected}/{len(probes)}",flush=True)
        self.assertGreaterEqual(top3/len(held),.80);self.assertEqual(rejected,len(probes))
    def test_rate_limit_and_guest_admin_boundary(self):
        c=self.client()
        for _ in range(12):self.assertEqual(self.send(c,"/api/auth/login",{"username":"absent-user","password":"wrong"})[0],401)
        self.assertEqual(self.send(c,"/api/auth/login",{"username":"absent-user","password":"wrong"})[0],429)
        self.assertEqual(self.send(c,"/api/resources?status=all")[0],401)
        self.assertEqual(self.send(c,"/api/notices?manage=1")[0],401)
        self.assertEqual(self.send(c,"/api/health")[1],{"status":"ok"})
if __name__=="__main__":unittest.main(verbosity=2)
