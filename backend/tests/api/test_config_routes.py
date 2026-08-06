import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_claude_json_path, get_global_settings_path
from app.main import app

client = TestClient(app)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_get_global_config_returns_claude_json_and_settings(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    settings_json = tmp_path / "settings.json"
    write_json(claude_json, {"mcpServers": {"ollama": {"command": "ollama"}}})
    write_json(settings_json, {"permissions": {"allow": ["Bash(git *)"]}})

    app.dependency_overrides[get_claude_json_path] = lambda: claude_json
    app.dependency_overrides[get_global_settings_path] = lambda: settings_json

    response = client.get("/config/global")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["claude_json"]["mcpServers"]["ollama"]["command"] == "ollama"
    assert body["settings"]["permissions"]["allow"] == ["Bash(git *)"]
    assert body["effective_permissions"]["allow"] == ["Bash(git *)"]


def test_get_project_config_computes_effective_permissions(tmp_path: Path) -> None:
    settings_json = tmp_path / "settings.json"
    write_json(settings_json, {"permissions": {"allow": ["Bash(git *)"]}})

    project_dir = tmp_path / "my-project"
    (project_dir / ".claude").mkdir(parents=True)
    write_json(
        project_dir / ".claude" / "settings.json",
        {"permissions": {"allow": ["Edit(src/**)"]}},
    )
    write_json(
        project_dir / ".claude" / "settings.local.json",
        {"permissions": {"allow": ["Bash(npm test)"]}},
    )
    write_json(project_dir / ".mcp.json", {"mcpServers": {"db": {"command": "dbhub"}}})

    app.dependency_overrides[get_global_settings_path] = lambda: settings_json

    response = client.get("/config/project", params={"path": str(project_dir)})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["mcp_servers"]["db"]["command"] == "dbhub"
    assert body["effective_permissions"]["allow"] == ["Bash(npm test)"]


def test_get_project_config_handles_missing_project_files(tmp_path: Path) -> None:
    settings_json = tmp_path / "settings.json"
    write_json(settings_json, {})
    app.dependency_overrides[get_global_settings_path] = lambda: settings_json

    response = client.get("/config/project", params={"path": str(tmp_path / "empty-project")})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["mcp_servers"] == {}
    assert body["effective_permissions"] == {"allow": [], "ask": [], "deny": []}
