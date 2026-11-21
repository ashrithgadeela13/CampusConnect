CREATE TABLE IF NOT EXISTS credentials (
  user_id TEXT PRIMARY KEY REFERENCES app_users(id),
  username TEXT NOT NULL UNIQUE COLLATE NOCASE,
  salt BLOB NOT NULL,
  verifier BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  digest BLOB PRIMARY KEY, user_id TEXT NOT NULL REFERENCES app_users(id), expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions(expires_at);
CREATE TABLE IF NOT EXISTS auth_limits (
  bucket TEXT PRIMARY KEY, window INTEGER NOT NULL, attempts INTEGER NOT NULL
);
