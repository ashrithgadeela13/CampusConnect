"""Shared validation and response types used by the HTTP handlers."""
from dataclasses import dataclass, field
from datetime import datetime, date, timezone
import uuid

class Problem(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message

@dataclass
class Reply:
    content: object
    status: int = 200
    headers: list = field(default_factory=list)

def text(obj, key, low=0, high=500):
    value = obj.get(key, "")
    if not isinstance(value, str) or not low <= len(value.strip()) <= high:
        raise Problem(422, f"Check {key.replace('_', ' ')} ({low}–{high} characters).")
    return value.strip()

def only(obj, keys):
    if set(obj) - set(keys):
        raise Problem(422, "Unexpected fields in this request.")

def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")

def today():
    return datetime.now(timezone.utc).date().isoformat()

def day_string(value, allow_future=True):
    if not value:
        return ""
    try:
        if len(value)!=10 or date.fromisoformat(value).isoformat()!=value or (not allow_future and value>today()):
            raise ValueError
    except (ValueError,TypeError):
        raise Problem(422, "Enter a valid date.")
    return value

def identifier():
    return str(uuid.uuid4())
