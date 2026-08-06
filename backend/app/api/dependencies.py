import sqlite3
from collections.abc import Generator
from pathlib import Path

from app.db.connection import connect, default_db_path


def get_claude_json_path() -> Path:
    return Path.home() / ".claude.json"


def get_global_settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def get_claude_home_path() -> Path:
    return Path.home() / ".claude"


def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = connect(default_db_path())
    try:
        yield conn
    finally:
        conn.close()
