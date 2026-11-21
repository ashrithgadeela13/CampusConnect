"""Administrator provisioning is a terminal-only operation, never public registration."""
import argparse,getpass
from backend import auth
from backend.common import Problem
from backend.db import connect
def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["create-admin","reset-password"])
    cmd=p.parse_args()
    db=connect()
    try:
        name=input("CampusConnect username: ").strip().lower()
        label=input("Display name: ").strip() if cmd.action=="create-admin" else None
        print("Password entry is hidden: type your password and press Enter, even though no characters appear.")
        password=getpass.getpass("New password (at least 12 characters): ")
        if getpass.getpass("Type it again: ")!=password:raise Problem(422,"Passwords didn't match.")
        auth.validate_password(password)
        if cmd.action=="create-admin":auth.create(db,name,password,label,role="admin")
        else:
            import secrets
            row=db.execute("SELECT user_id FROM credentials WHERE username=?",(name,)).fetchone()
            if not row:raise Problem(404,"No such CampusConnect username.")
            salt=secrets.token_bytes(16);digest=auth.derive(password,salt)
            db.execute("UPDATE credentials SET salt=?,verifier=? WHERE user_id=?",(salt,digest,row[0]))
            db.execute("DELETE FROM sessions WHERE user_id=?",(row[0],))
        db.commit(); print("Done. Sign in to CampusConnect with this username and password.")
    except Problem as e:
        db.rollback();raise SystemExit(e.message)
    finally:db.close()
if __name__=="__main__":main()
