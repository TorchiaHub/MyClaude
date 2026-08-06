import json
from pathlib import Path

from app.db.connection import connect
from app.project_discovery import (
    discover_touched_projects,
    list_projects,
    list_registered_projects,
    register_project,
)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_discover_touched_projects_returns_sorted_paths(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(
        claude_json,
        {"projects": {"/home/matt/b-project": {}, "/home/matt/a-project": {}}},
    )

    result = discover_touched_projects(claude_json)

    assert result == ["/home/matt/a-project", "/home/matt/b-project"]


def test_discover_touched_projects_returns_empty_list_when_no_projects_key(
    tmp_path: Path,
) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {})

    result = discover_touched_projects(claude_json)

    assert result == []


def test_register_project_persists_and_lists(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")

    register_project(conn, Path("/home/matt/manual-project"))

    assert list_registered_projects(conn) == ["/home/matt/manual-project"]


def test_register_project_is_idempotent(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")

    register_project(conn, Path("/home/matt/manual-project"))
    register_project(conn, Path("/home/matt/manual-project"))

    assert list_registered_projects(conn) == ["/home/matt/manual-project"]


def test_list_projects_merges_auto_and_manual_without_duplicates(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {"/home/matt/auto-project": {}}})
    conn = connect(tmp_path / "index.sqlite")
    register_project(conn, Path("/home/matt/auto-project"))
    register_project(conn, Path("/home/matt/manual-project"))

    result = list_projects(claude_json, conn)

    assert len(result) == 2
    by_path = {entry.path: entry.source for entry in result}
    assert by_path["/home/matt/auto-project"] == "auto"
    assert by_path["/home/matt/manual-project"] == "manual"
