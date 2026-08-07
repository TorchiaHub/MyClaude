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

CREATE TABLE IF NOT EXISTS packages (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('global', 'project')),
    project_path TEXT,
    content_path TEXT NOT NULL,
    folder TEXT,
    updated_at INTEGER NOT NULL
);

-- log, non stato corrente: necessario per il confronto storico per finestra temporale (Fase 4)
CREATE TABLE IF NOT EXISTS activation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id TEXT REFERENCES packages(id),
    project_path TEXT,
    action TEXT NOT NULL CHECK (action IN ('activate', 'deactivate')),
    occurred_at INTEGER NOT NULL
);

-- manifest di ciò che activation_engine ha scritto, per rimozione sicura
CREATE TABLE IF NOT EXISTS written_files (
    package_id TEXT REFERENCES packages(id),
    project_path TEXT,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    PRIMARY KEY (package_id, project_path, file_path)
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
