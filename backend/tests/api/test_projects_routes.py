import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_claude_json_path, get_db_connection
from app.db.connection import connect
from app.main import app
from tests.api.db_override import db_override

client = TestClient(app)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_get_projects_returns_auto_discovered_entries(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {"/home/matt/auto-project": {}}})
    conn = connect(tmp_path / "index.sqlite")

    app.dependency_overrides[get_claude_json_path] = lambda: claude_json
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.get("/projects")

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
    body = response.json()
    assert body == [{"path": "/home/matt/auto-project", "source": "auto"}]


def test_post_projects_registers_manual_project(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {})
    conn = connect(tmp_path / "index.sqlite")

    app.dependency_overrides[get_claude_json_path] = lambda: claude_json
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.post("/projects", json={"path": "/home/matt/manual-project"})

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 201
    assert response.json() == {"path": "/home/matt/manual-project", "source": "manual"}
