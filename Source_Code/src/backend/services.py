"""Private user lists, notices, and aggregate-only directory analytics."""
from collections import Counter
from datetime import date,timedelta
from . import directory
from .auth import require
from .common import Reply,Problem,text,only,today,timestamp,identifier,day_string
from .db import rows

def personal(db,a):
    uid=require(a)["id"]
    def ids(table,field):
        return [r[0] for r in db.execute(f"SELECT t.resource_id FROM {table} t JOIN resources r ON r.id=t.resource_id WHERE user_id=? AND r.status='published' ORDER BY t.{field} DESC,t.rowid DESC",(uid,))]
    return {"saved":ids("bookmarks","saved_at"),"recent":ids("recent_views","viewed_at")[:20]}

def edit_personal(db,a,b):
    uid=require(a)["id"]
    if b.get("action")=="clearRecent":
        only(b,["action"]);db.execute("DELETE FROM recent_views WHERE user_id=?",(uid,))
    elif b.get("action")=="save":
        only(b,["action","id","saved"]); rid=text(b,"id",1,100)
        if type(b.get("saved"))!=bool: raise Problem(422,"Choose whether to save this resource.")
        if b["saved"]:
            directory.published(db,rid);db.execute("INSERT OR IGNORE INTO bookmarks VALUES(?,?,?)",(uid,rid,timestamp()))
        else: db.execute("DELETE FROM bookmarks WHERE user_id=? AND resource_id=?",(uid,rid))
    else: raise Problem(422,"Unknown personal-list action.")
    return personal(db,a)

def count(db,kind,bucket):
    db.execute("INSERT INTO usage_daily(day,kind,bucket,total) VALUES(?,?,?,1) ON CONFLICT(day,kind,bucket) DO UPDATE SET total=total+1",(today(),kind,bucket))

def activity(db,a,b):
    kind=b.get("kind")
    if kind=="view":
        only(b,["kind","id"]);rid=text(b,"id",1,100);directory.published(db,rid);count(db,"view",rid)
        if a:
            uid=a["id"]
            db.execute("INSERT INTO recent_views(user_id,resource_id,viewed_at) VALUES(?,?,?) ON CONFLICT(user_id,resource_id) DO UPDATE SET viewed_at=excluded.viewed_at",(uid,rid,timestamp()))
            db.execute("DELETE FROM recent_views WHERE user_id=? AND resource_id NOT IN (SELECT resource_id FROM recent_views WHERE user_id=? ORDER BY viewed_at DESC,rowid DESC LIMIT 20)",(uid,uid))
    elif kind=="search":
        only(b,["kind","found"])
        if type(b.get("found"))!=bool: raise Problem(422,"Invalid search outcome.")
        count(db,"search","results" if b["found"] else "empty")
    elif kind=="guided":
        only(b,["kind","id"]); cid=text(b,"id",1,80);directory.exists_category(db,cid);count(db,"guide",cid)
    else: raise Problem(422,"Unknown activity.")
    return {"ok":True}

def notices(db,manage=False):
    sql="SELECT n.*,c.name AS category_name FROM notices n LEFT JOIN categories c ON c.id=n.category_id"
    query="" if manage else " WHERE n.status='published' AND (n.expires_on='' OR n.expires_on>=?)"
    return rows(db,sql+query+" ORDER BY n.updated_at DESC,n.id",() if manage else (today(),))

def edit_notice(db,a,b):
    require(a,True);only(b,["id","version","title","body","status","category_id","expires_on"])
    title=text(b,"title",3,110);msg=text(b,"body",5,2000);status=text(b,"status",1,12);expiry=day_string(text(b,"expires_on",0,10))
    if status not in ("draft","published","archived"): raise Problem(422,"Choose a notice status.")
    cid=b.get("category_id") or None
    if cid: directory.exists_category(db,text(b,"category_id",1,80))
    if b.get("id"):
        if type(b.get("version"))!=int or b["version"]<1: raise Problem(422,"Include a valid notice version.")
        cur=db.execute("UPDATE notices SET title=?,body=?,status=?,category_id=?,expires_on=?,updated_at=?,version=version+1 WHERE id=? AND version=?",(title,msg,status,cid,expiry,timestamp(),text(b,"id",1,100),b["version"]))
        if not cur.rowcount: raise Problem(409,"This notice changed. Refresh to load the latest version.")
        code=200
    else:
        db.execute("INSERT INTO notices(id,title,body,status,category_id,expires_on,updated_at,version) VALUES(?,?,?,?,?,?,?,1)",(identifier(),title,msg,status,cid,expiry,timestamp()));code=201
    return Reply({"notices":notices(db,True)},code)

def analytics(db,a,period):
    require(a,True)
    if period not in ("7","30"): raise Problem(422,"Choose 7 or 30 days.")
    days=int(period);end=date.fromisoformat(today());dates=[(end-timedelta(days=i)).isoformat() for i in reversed(range(days))]
    daily={day:{"day":day,"views":0,"searches":0,"guides":0} for day in dates}
    metrics=dict(views=0,searches=0,empty=0,guides=0,unmatched=0);services=Counter();needs=Counter()
    for r in db.execute("""SELECT u.*,r.name AS service,c.name AS category FROM usage_daily u
          LEFT JOIN resources r ON u.kind='view' AND u.bucket=r.id LEFT JOIN categories c ON u.kind='guide' AND u.bucket=c.id
          WHERE u.day BETWEEN ? AND ?""",(dates[0],dates[-1])):
        k={"view":"views","search":"searches","guide":"guides"}[r["kind"]];n=r["total"];metrics[k]+=n;daily[r["day"]][k]+=n
        if k=="views":services[r["service"] or "Removed resource"]+=n
        elif k=="searches" and r["bucket"]=="empty":metrics["empty"]+=n
        elif k=="guides":
            if r["bucket"]=="no_match":metrics["unmatched"]+=n
            else:needs[r["category"] or "Removed category"]+=n
    def top(counts):return [{"label":k,"total":n} for k,n in sorted(counts.items(),key=lambda item:(-item[1],item[0]))[:5]]
    return {"period":days,"metrics":metrics,"daily":list(daily.values()),"services":top(services),"needs":top(needs)}
