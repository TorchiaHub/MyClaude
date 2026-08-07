import os
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


def get_home_path() -> Path:
    return Path.home()


def get_control_plane_home() -> Path:
    return Path.home() / ".claude-control-plane"


def get_backend_port() -> int:
    """The port this backend is actually listening on, matching start.sh's
    `PORT="${PORT:-8000}"` convention — used to build the SessionStart hook
    command so it targets the right port even when the app was launched
    with a non-default PORT."""
    return int(os.environ.get("PORT", 8000))


def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = connect(default_db_path())
    try:
        yield conn
    finally:
        conn.close()
