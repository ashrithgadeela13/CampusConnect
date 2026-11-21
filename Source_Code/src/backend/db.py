"""Initialize a fresh SQLite database; never overwrite edited catalog rows on restart."""
from pathlib import Path
from threading import Lock
import json, os, secrets, sqlite3
from .common import timestamp

ROOT=Path(__file__).resolve().parents[1]
_ready=set()
_lock=Lock()

def database_path():
    return Path(os.environ.get("CAMPUSCONNECT_DATA_DIR",str(ROOT/"instance"))).expanduser().resolve()/"campusconnect.sqlite3"

def rows(db, sql, args=()):
    return [dict(r) for r in db.execute(sql,args)]

def connect():
    path=database_path()
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=12)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    with _lock:
        if path not in _ready:
            try:
                initialize(db)
            except BaseException:
                db.close()
                raise
            _ready.add(path)
    return db

def initialize(db):
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(name TEXT PRIMARY KEY)")
    db.commit()
    for path in sorted((ROOT/"migrations").glob("*.sql")):
        # The write lock also serializes startup in separate WSGI worker processes.
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM schema_migrations WHERE name=?",(path.name,)).fetchone():
            db.commit(); continue
        source=path.read_text(encoding="utf-8").replace("--> statement-breakpoint","\n")
        buf=""
        for char in source:
            buf+=char
            if char==";" and sqlite3.complete_statement(buf):
                db.execute(buf); buf=""
        if buf.strip():
            db.execute(buf)
        db.execute("INSERT INTO schema_migrations VALUES(?)",(path.name,)); db.commit()
    db.execute("BEGIN IMMEDIATE")
    if not db.execute("SELECT 1 FROM app_settings WHERE key='standalone_catalog_v1'").fetchone():
        catalog=json.loads((ROOT/"data-source/catalog.json").read_text(encoding="utf-8"))
        for c in catalog["categories"]:
            db.execute("INSERT OR IGNORE INTO categories(id,name,icon,color,position) VALUES(:id,:name,:icon,:color,:position)",c)
        now=timestamp()
        for r in catalog["resources"]:
            db.execute("""INSERT OR IGNORE INTO resources(id,category_id,name,summary,description,location,hours,email,phone,url,tags,next_steps,status,source_checked_on,version,created_at,updated_at,updated_by)
              VALUES(:id,:category_id,:name,:summary,:description,:location,:hours,:email,:phone,:url,:tags,:next_steps,'published',:source_checked_on,1,:now,:now,'Initial directory')""",{**r,"now":now})
        db.execute("""INSERT OR IGNORE INTO notices(id,title,body,status,expires_on,updated_at,version)
          VALUES('welcome-directory','Welcome to CampusConnect',?,'published','',?,1)""",("Choose Find help to ask a question or follow the guided steps. Each resource links to its official UTA page. A CampusConnect account lets you save an office for later.",now))
        db.execute("INSERT OR IGNORE INTO app_settings VALUES('standalone_catalog_v1',?)",(now,))
    db.execute("INSERT OR IGNORE INTO app_settings(key,value) VALUES('throttle_salt',?)",(secrets.token_hex(32),))
    db.commit()
