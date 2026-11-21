"""Resource and category operations. Student reads are limited to published rows."""
import re,sqlite3
from urllib.parse import urlparse
from .db import rows
from .common import Reply,Problem,text,timestamp,identifier,day_string
from .auth import require
SELECT="""SELECT r.*,c.name AS category_name,c.icon AS category_icon,c.color AS category_color
          FROM resources r JOIN categories c ON c.id=r.category_id"""
FIELDS=["category_id","name","summary","description","location","hours","email","phone","url","tags","next_steps","status","source_checked_on"]
def categories(db):
    return rows(db,"SELECT * FROM categories ORDER BY position,name")
def resources(db,include_archived=False,category="",query=""):
    conditions=[]; args=[]
    if not include_archived: conditions.append("r.status='published'")
    if category: conditions.append("r.category_id=?"); args.append(category)
    result=rows(db,SELECT+(" WHERE "+" AND ".join(conditions) if conditions else "")+" ORDER BY c.position,r.name",args)
    if not include_archived:
        for r in result: r["updated_by"]=""
    if query and not include_archived:
        from .classifier import directory_search
        by_id={r["id"]:r for r in result}
        return [by_id[i] for i in directory_search(query,result)]
    if query:
        terms=query.lower().split()
        result=[r for r in result if all(w in " ".join(r[k] for k in ("name","summary","description","category_name","tags")).lower() for w in terms)]
    return result

def exists_category(db,cid):
    if not db.execute("SELECT id FROM categories WHERE id=?",(cid,)).fetchone():
        raise Problem(422,"Choose an existing category.")

def published(db,rid):
    if not db.execute("SELECT id FROM resources WHERE id=? AND status='published'",(rid,)).fetchone():
        raise Problem(404,"That resource is unavailable.")

def change_resource(db,a,body,rid=None):
    require(a,admin=True)
    sizes=[(1,80),(3,140),(10,280),(10,2500),(2,240),(2,240),(0,254),(0,60),(1,600),(0,300),(0,1800),(1,20),(0,10)]
    r={k:text(body,k,*n) for k,n in zip(FIELDS,sizes)}
    if r["status"] not in ("published","archived"): raise Problem(422,"Choose a valid publication status.")
    try:
        u=urlparse(r["url"])
        if u.scheme!="https" or not u.hostname or u.username is not None or u.password is not None or any(c.isspace() for c in r["url"]): raise ValueError
    except ValueError: raise Problem(422,"Use an HTTPS website address.")
    if r["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",r["email"]): raise Problem(422,"Check the contact email.")
    day_string(r["source_checked_on"],False); exists_category(db,r["category_id"])
    now=timestamp(); values=[r[x] for x in FIELDS]
    if rid:
        if type(body.get("version"))!=int or body["version"]<1: raise Problem(422,"Include the existing resource version.")
        args=values+[now,a["id"],rid,body["version"]]
        cur=db.execute("UPDATE resources SET "+",".join(k+"=?" for k in FIELDS)+",updated_at=?,updated_by=?,version=version+1 WHERE id=? AND version=?",args)
        if not cur.rowcount: raise Problem(409 if db.execute("SELECT 1 FROM resources WHERE id=?",(rid,)).fetchone() else 404,"The resource changed or was removed. Refresh the directory.")
        status=200
    else:
        rid=identifier(); names=FIELDS+["id","created_at","updated_at","updated_by","version"];args=values+[rid,now,now,a["id"],1]
        db.execute("INSERT INTO resources("+",".join(names)+") VALUES("+",".join("?" for _ in names)+")",args);status=201
    return Reply({"resource":dict(db.execute(SELECT+" WHERE r.id=?",(rid,)).fetchone())},status)

def change_category(db,a,b):
    require(a,True);action=text(b,"action",1,10)
    if action not in ("create","rename","remove"): raise Problem(422,"Unknown category action.")
    cid=identifier() if action=="create" else text(b,"id",1,80)
    db.execute("BEGIN IMMEDIATE")
    if action!="create" and not db.execute("SELECT 1 FROM categories WHERE id=?",(cid,)).fetchone(): raise Problem(404,"That category no longer exists.")
    if action=="remove":
        if db.execute("SELECT 1 FROM resources WHERE category_id=? UNION ALL SELECT 1 FROM notices WHERE category_id=? LIMIT 1",(cid,cid)).fetchone(): raise Problem(409,"Move this category’s resources and notices before removing it.")
        db.execute("DELETE FROM categories WHERE id=?",(cid,))
    else:
        name=text(b,"name",2,64)
        if db.execute("SELECT 1 FROM categories WHERE name=? COLLATE NOCASE AND id<>?",(name,cid)).fetchone(): raise Problem(409,"A category with that name already exists.")
        if action=="create": db.execute("INSERT INTO categories SELECT ?,?,'compass','#28578A',COALESCE(MAX(position),0)+1 FROM categories",(cid,name))
        else: db.execute("UPDATE categories SET name=? WHERE id=?",(name,cid))
    return Reply({"categories":categories(db)},201 if action=="create" else 200)
