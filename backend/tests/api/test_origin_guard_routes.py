from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_claude_json_path, get_db_connection
from app.api.system import get_shutdown_handler
from app.db.connection import connect
from app.json_store import write_json
from app.main import app
from tests.api.db_override import db_override

client = TestClient(app)


def test_post_projects_succeeds_with_no_origin_header(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.post("/projects", json={"path": str(tmp_path / "proj")})

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 201


def test_post_projects_succeeds_with_matching_origin_header(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.post(
        "/projects",
        json={"path": str(tmp_path / "proj")},
        headers={"origin": str(client.base_url)},
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 201


def test_post_projects_rejected_with_mismatched_origin_header(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.post(
        "/projects",
        json={"path": str(tmp_path / "proj")},
        headers={"origin": "http://evil.example.com"},
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 403


def test_post_system_shutdown_rejected_with_mismatched_origin_header() -> None:
    calls: list[bool] = []
    app.dependency_overrides[get_shutdown_handler] = lambda: (lambda: calls.append(True))

    response = client.post("/system/shutdown", headers={"origin": "http://evil.example.com"})

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert calls == []


def test_post_system_shutdown_succeeds_with_no_origin_header() -> None:
    calls: list[bool] = []
    app.dependency_overrides[get_shutdown_handler] = lambda: (lambda: calls.append(True))

    response = client.post("/system/shutdown")

    app.dependency_overrides.clear()

    assert response.status_code == 202


def test_delete_mcp_server_rejected_with_mismatched_origin_header(tmp_path: Path) -> None:
    claude_json_path = tmp_path / "claude.json"
    write_json(claude_json_path, {"mcpServers": {"ollama": {"command": "ollama"}}})
    app.dependency_overrides[get_claude_json_path] = lambda: claude_json_path

    response = client.request(
        "DELETE",
        "/mcp/servers/ollama",
        json={"scope": "global"},
        headers={"origin": "http://evil.example.com"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert '"ollama"' in claude_json_path.read_text()


def test_get_projects_not_affected_by_mismatched_origin_header(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.get("/projects", headers={"origin": "http://evil.example.com"})

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
