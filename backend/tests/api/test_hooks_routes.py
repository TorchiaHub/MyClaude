import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_backend_port, get_db_connection, get_global_settings_path
from app.db.connection import connect
from app.main import app
from tests.api.db_override import db_override

client = TestClient(app)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_post_session_start_records_session(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.post(
        "/hooks/session-start",
        json={
            "session_id": "sess-1",
            "cwd": "/home/matt/my-project",
            "hook_event_name": "SessionStart",
            "transcript_path": "/irrelevant.jsonl",
        },
    )

    app.dependency_overrides.clear()

    row = conn.execute(
        "SELECT cwd FROM session_started WHERE session_id = ?", ("sess-1",)
    ).fetchone()
    conn.close()

    assert response.status_code == 204
    assert row["cwd"] == "/home/matt/my-project"


def test_post_session_start_requires_session_id_and_cwd(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.post("/hooks/session-start", json={"hook_event_name": "SessionStart"})

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 422


def test_get_hook_status_false_when_not_installed(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})
    app.dependency_overrides[get_global_settings_path] = lambda: settings_path

    response = client.get("/hooks/session-start/status")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"installed": False}


def test_post_install_writes_hook_using_backend_port(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})
    app.dependency_overrides[get_global_settings_path] = lambda: settings_path
    app.dependency_overrides[get_backend_port] = lambda: 9999

    response = client.post("/hooks/session-start/install")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"installed": True}
    data = json.loads(settings_path.read_text())
    assert "9999" in data["hooks"]["SessionStart"][0]["hooks"][0]["command"]


def test_post_install_is_idempotent(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})
    app.dependency_overrides[get_global_settings_path] = lambda: settings_path

    client.post("/hooks/session-start/install")
    response = client.post("/hooks/session-start/install")

    app.dependency_overrides.clear()

    assert response.json() == {"installed": False}


def test_delete_uninstall_removes_hook(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})
    app.dependency_overrides[get_global_settings_path] = lambda: settings_path
    client.post("/hooks/session-start/install")

    response = client.delete("/hooks/session-start/install")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"uninstalled": True}
    data = json.loads(settings_path.read_text())
    assert data["hooks"]["SessionStart"] == []
