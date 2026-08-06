import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_claude_json_path
from app.main import app

client = TestClient(app)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_get_servers_returns_global_and_project_scope(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"mcpServers": {"ollama": {"command": "ollama"}}})
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    write_json(project_dir / ".mcp.json", {"mcpServers": {"db": {"command": "dbhub"}}})

    app.dependency_overrides[get_claude_json_path] = lambda: claude_json

    response = client.get("/mcp/servers", params={"project_path": str(project_dir)})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    names = {entry["name"] for entry in response.json()}
    assert names == {"ollama", "db"}


def test_get_servers_without_project_path_returns_only_global(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"mcpServers": {"ollama": {"command": "ollama"}}})

    app.dependency_overrides[get_claude_json_path] = lambda: claude_json

    response = client.get("/mcp/servers")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert [entry["name"] for entry in response.json()] == ["ollama"]


def test_post_server_adds_entry_to_global_scope(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {})
    app.dependency_overrides[get_claude_json_path] = lambda: claude_json

    response = client.post(
        "/mcp/servers",
        json={"name": "ollama", "scope": "global", "config": {"command": "ollama"}},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    saved = json.loads(claude_json.read_text())
    assert saved["mcpServers"]["ollama"]["command"] == "ollama"


def test_post_server_adds_entry_to_project_scope(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    response = client.post(
        "/mcp/servers",
        json={
            "name": "db",
            "scope": "project",
            "project_path": str(project_dir),
            "config": {"command": "dbhub"},
        },
    )

    assert response.status_code == 201
    saved = json.loads((project_dir / ".mcp.json").read_text())
    assert saved["mcpServers"]["db"]["command"] == "dbhub"


def test_post_server_project_scope_without_project_path_is_a_bad_request() -> None:
    response = client.post(
        "/mcp/servers",
        json={"name": "db", "scope": "project", "config": {"command": "dbhub"}},
    )

    assert response.status_code == 400


def test_delete_server_removes_entry(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"mcpServers": {"ollama": {"command": "ollama"}}})
    app.dependency_overrides[get_claude_json_path] = lambda: claude_json

    response = client.request("DELETE", "/mcp/servers/ollama", json={"scope": "global"})

    app.dependency_overrides.clear()

    assert response.status_code == 204
    assert json.loads(claude_json.read_text())["mcpServers"] == {}


def test_delete_server_returns_404_when_not_found(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"mcpServers": {}})
    app.dependency_overrides[get_claude_json_path] = lambda: claude_json

    response = client.request("DELETE", "/mcp/servers/ghost", json={"scope": "global"})

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_post_server_test_returns_reachable_true_for_known_command(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"mcpServers": {"ollama": {"command": "python3"}}})
    app.dependency_overrides[get_claude_json_path] = lambda: claude_json

    response = client.post("/mcp/servers/ollama/test", json={"scope": "global"})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["reachable"] is True


def test_post_server_test_returns_404_when_server_not_found(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"mcpServers": {}})
    app.dependency_overrides[get_claude_json_path] = lambda: claude_json

    response = client.post("/mcp/servers/ghost/test", json={"scope": "global"})

    app.dependency_overrides.clear()

    assert response.status_code == 404
