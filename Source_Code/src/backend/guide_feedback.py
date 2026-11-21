"""Collect guide outcomes and let administrators review unresolved questions."""
import base64
import binascii
import hashlib
import hmac
import json
import time

from . import auth
from .common import Problem, identifier, only, text, timestamp
from .db import rows

REASONS = {"Wrong office", "Instructions unclear", "Couldn't find my service", "Other"}


def signature(db, payload):
    key = db.execute("SELECT value FROM app_settings WHERE key='throttle_salt'").fetchone()[0]
    return hmac.new(key.encode(), b"guide-feedback:" + payload, hashlib.sha256).hexdigest()


def attach_receipt(db, question, result, resources):
    names = {resource["id"]: resource["name"] for resource in resources}
    offices = [names[resource_id] for resource_id in result["resourceIds"] if resource_id in names]
    receipt = [identifier(), question, result["state"], offices, int(time.time())]
    if result["state"] == "none":
        db.execute(
            "INSERT INTO guide_feedback(id, question, outcome, offices, created_at) VALUES(?,?,?,?,?)",
            (receipt[0], question, result["state"], "[]", timestamp()),
        )
    payload = base64.urlsafe_b64encode(json.dumps(receipt).encode())
    result["feedbackReceipt"] = payload.decode() + "." + signature(db, payload)


def submit(db, body):
    only(body, ["receipt", "solved", "reason"])
    solved = body.get("solved")
    reason = text(body, "reason", 0, 50)
    if type(solved) is not bool or (reason and (solved or reason not in REASONS)):
        raise Problem(422, "Choose Yes or No and an optional reason.")
    try:
        encoded, provided = text(body, "receipt", 1, 14000).split(".")
        payload = encoded.encode("ascii")
        if not hmac.compare_digest(signature(db, payload), provided):
            raise ValueError
        entry, question, outcome, offices, issued = json.loads(base64.urlsafe_b64decode(payload))
        if time.time() - issued > 86400:
            raise ValueError
    except (ValueError, TypeError, binascii.Error):
        raise Problem(422, "Run Find help again before sending feedback.") from None
    db.execute(
        """INSERT INTO guide_feedback(id, question, outcome, offices, solved, reason, created_at)
           VALUES(?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET solved=excluded.solved, reason=excluded.reason,
               question=excluded.question, offices=excluded.offices
           WHERE guide_feedback.solved IS NULL""",
        (entry, "" if solved else question, outcome, json.dumps([] if solved else offices),
         int(solved), reason, timestamp()),
    )
    return {"ok": True}


def dashboard(db, account, page):
    auth.require(account, True)
    try:
        offset = max(0, min(int(page), 1000000)) * 25
    except ValueError:
        raise Problem(422, "Choose a valid page.") from None
    counts = dict(db.execute(
        """SELECT
             COUNT(CASE WHEN solved=1 THEN 1 END) AS yes,
             COUNT(CASE WHEN solved=0 THEN 1 END) AS no,
             COUNT(CASE WHEN outcome='none' THEN 1 END) AS noMatch
           FROM guide_feedback"""
    ).fetchone())
    items = rows(db, """SELECT id, question, outcome, offices, solved, reason, created_at, reviewed_at
                        FROM guide_feedback
                        WHERE solved=0 OR (outcome='none' AND solved IS NULL)
                        ORDER BY reviewed_at IS NOT NULL, created_at DESC, id DESC
                        LIMIT 26 OFFSET ?""", (offset,))
    for item in items:
        item["offices"] = json.loads(item["offices"])
    return {"counts": counts, "items": items[:25], "hasMore": len(items) > 25}


def review(db, account, body):
    auth.require(account, True)
    only(body, ["id", "reviewed"])
    entry = text(body, "id", 36, 36)
    reviewed = body.get("reviewed")
    if type(reviewed) is not bool:
        raise Problem(422, "Choose a review status.")
    updated = db.execute(
        """UPDATE guide_feedback SET reviewed_at=? WHERE id=?
           AND (solved=0 OR (outcome='none' AND solved IS NULL))""",
        (timestamp() if reviewed else None, entry),
    )
    if not updated.rowcount:
        raise Problem(404, "Question not found.")
    return {"ok": True}
