import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS library_item_tags (
    item_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (item_id, tag)
);

CREATE TABLE IF NOT EXISTS library_bookmarks (
    item_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS registered_projects (
    path TEXT PRIMARY KEY,
    registered_at INTEGER NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def default_db_path() -> Path:
    return Path.home() / ".claude-control-plane" / "index.sqlite"
