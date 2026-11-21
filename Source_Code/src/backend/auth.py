"""Independent CampusConnect credentials and revocable, server-side sessions."""
import hashlib, hmac, re, secrets, sqlite3, time
from http.cookies import SimpleCookie,CookieError
from .common import Problem, Reply, timestamp, text, identifier, only
COOKIE="cc_session"
TTL=7*24*3600
NAME=re.compile(r"[a-z0-9][a-z0-9_.-]{2,39}\Z")
DUMMY_SALT=b"CC-missing-user!"

def normalized(value):
    return value.strip().lower() if isinstance(value,str) else ""

def derive(password,salt):
    return hashlib.scrypt(password.encode("utf-8"),salt=salt,n=32768,r=8,p=3,maxmem=64*1024*1024,dklen=32)

def validate_password(password):
    if not isinstance(password,str) or not 12<=len(password)<=128:
        raise Problem(422,"Choose a password between 12 and 128 characters.")

def create(db,username,password,name,role="student"):
    username=normalized(username)
    if not NAME.fullmatch(username):
        raise Problem(422,"Usernames start with a letter or number and use 3–40 letters, numbers, dots, underscores or hyphens.")
    validate_password(password)
    if not isinstance(name,str) or not 1<=len(name.strip())<=60:
        raise Problem(422,"Use a display name of 1–60 characters.")
    if db.execute("SELECT 1 FROM credentials WHERE username=?",(username,)).fetchone():
        raise Problem(409,"That username is already taken.")
    salt=secrets.token_bytes(16)
    verifier=derive(password,salt)
    uid=identifier()
    db.execute("INSERT INTO app_users(id,email,name,role,student_preview,created_at) VALUES(?,'',?,?,0,?)",(uid,name.strip(),role,timestamp()))
    try:
        db.execute("INSERT INTO credentials VALUES(?,?,?,?)",(uid,username,salt,verifier))
    except sqlite3.IntegrityError:
        raise Problem(409,"That username is already taken.")
    return uid

def session_digest(env):
    c=SimpleCookie()
    try: c.load(env.get("HTTP_COOKIE",""))
    except CookieError: return None
    v=c.get(COOKIE)
    if not v or not re.fullmatch(r"[A-Za-z0-9_-]{43}",v.value): return None
    return hashlib.sha256(v.value.encode()).digest()

def account(db,env):
    digest=session_digest(env)
    if not digest: return None
    row=db.execute("""SELECT u.id,u.name,u.role,u.student_preview,c.username FROM sessions s
        JOIN app_users u ON u.id=s.user_id JOIN credentials c ON c.user_id=u.id WHERE s.digest=? AND s.expires_at>?""",(digest,int(time.time()))).fetchone()
    if not row: return None
    a=dict(row)
    a["email"]="@"+a["username"]  # display label in the account menu; no email collected
    a["effectiveRole"]="admin" if a["role"]=="admin" and not a["student_preview"] else "student"
    return a

def require(a,admin=False):
    if not a: raise Problem(401,"Sign in to continue.")
    if admin and a["effectiveRole"]!="admin": raise Problem(403,"Administrator access is required.")
    return a

def cookie_header(value,age,secure):
    return ("Set-Cookie",f"{COOKIE}={value}; Path=/; Max-Age={age}; HttpOnly; SameSite=Lax"+("; Secure" if secure else ""))

def new_session(db,uid,env,secure):
    old=session_digest(env)
    if old: db.execute("DELETE FROM sessions WHERE digest=?",(old,))
    token=secrets.token_urlsafe(32)
    now=int(time.time())
    db.execute("DELETE FROM sessions WHERE expires_at<=?",(now,))
    db.execute("INSERT INTO sessions VALUES(?,?,?)",(hashlib.sha256(token.encode()).digest(),uid,now+TTL))
    return Reply({"ok":True},200,[cookie_header(token,TTL,secure)])

def throttle(db,env,username,action):
    # A short-lived keyed bucket, never joined with directory analytics.
    salt=bytes.fromhex(db.execute("SELECT value FROM app_settings WHERE key='throttle_salt'").fetchone()[0])
    now=int(time.time())//600
    db.execute("DELETE FROM auth_limits WHERE window<?",(now-1,))
    for key,limit in [("ip:"+env.get("REMOTE_ADDR","local"),80),("user:"+username,12)]:
        bucket=hmac.new(salt,(action+":"+key).encode(),hashlib.sha256).hexdigest()
        db.execute("""INSERT INTO auth_limits VALUES(?,?,1) ON CONFLICT(bucket) DO UPDATE SET
            attempts=CASE WHEN window=excluded.window THEN attempts+1 ELSE 1 END, window=excluded.window""",(bucket,now))
        n=db.execute("SELECT attempts FROM auth_limits WHERE bucket=?",(bucket,)).fetchone()[0]
        if n>limit:
            db.commit()
            raise Problem(429,"Too many attempts. Try again in 10 minutes.")
    db.commit()  # failed credentials must still count

def process(db,env,action,b,secure):
    if action=="logout":
        only(b,[]); d=session_digest(env)
        if d: db.execute("DELETE FROM sessions WHERE digest=?",(d,))
        return Reply({"ok":True},200,[cookie_header("",0,secure)])
    if action not in ("register","login"): raise Problem(404,"Unknown account action.")
    only(b,["username","password","name"] if action=="register" else ["username","password"])
    username=normalized(text(b,"username",3,40)); password=b.get("password")
    if not isinstance(password,str) or not 1<=len(password)<=128: raise Problem(422,"Check your password.")
    throttle(db,env,username,action)
    if action=="register":
        uid=create(db,username,password,text(b,"name",1,60))
    else:
        c=db.execute("SELECT user_id,salt,verifier FROM credentials WHERE username=?",(username,)).fetchone()
        verifier=derive(password,c["salt"] if c else DUMMY_SALT)
        if not c or not hmac.compare_digest(verifier,c["verifier"]): raise Problem(401,"Incorrect username or password.")
        uid=c["user_id"]
    return new_session(db,uid,env,secure)
