import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.json_store import read_json

Source = Literal["auto", "manual"]


@dataclass(frozen=True)
class ProjectEntry:
    path: str
    source: Source


def discover_touched_projects(claude_json_path: Path) -> list[str]:
    projects = read_json(claude_json_path).get("projects", {})
    return sorted(projects.keys())


def register_project(conn: sqlite3.Connection, path: Path) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO registered_projects (path, registered_at) VALUES (?, ?)",
        (str(path), int(time.time())),
    )
    conn.commit()


def list_registered_projects(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT path FROM registered_projects ORDER BY registered_at").fetchall()
    return [row["path"] for row in rows]


def list_projects(claude_json_path: Path, conn: sqlite3.Connection) -> list[ProjectEntry]:
    auto_paths = discover_touched_projects(claude_json_path)
    manual_paths = list_registered_projects(conn)

    auto_set = set(auto_paths)
    entries = [ProjectEntry(path=path, source="auto") for path in auto_paths]
    entries += [
        ProjectEntry(path=path, source="manual") for path in manual_paths if path not in auto_set
    ]
    return entries
