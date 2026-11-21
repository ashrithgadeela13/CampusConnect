CREATE TABLE guide_feedback (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('match', 'clarify', 'none')),
    offices TEXT NOT NULL,
    solved INTEGER CHECK (solved IN (0, 1)),
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    reviewed_at TEXT
);
CREATE INDEX guide_feedback_created ON guide_feedback(created_at DESC, id DESC);
