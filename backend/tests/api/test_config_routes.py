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


def test_get_project_config_includes_own_permissions_distinct_from_effective(
    tmp_path: Path,
) -> None:
    settings_json = tmp_path / "settings.json"
    write_json(settings_json, {"permissions": {"allow": ["Bash(git *)"]}})

    project_dir = tmp_path / "my-project"
    (project_dir / ".claude").mkdir(parents=True)
    write_json(
        project_dir / ".claude" / "settings.json",
        {"permissions": {"allow": ["Edit(src/**)"]}},
    )

    app.dependency_overrides[get_global_settings_path] = lambda: settings_json

    response = client.get("/config/project", params={"path": str(project_dir)})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["own_permissions"]["allow"] == ["Edit(src/**)"]
    assert body["effective_permissions"]["allow"] == ["Bash(git *)", "Edit(src/**)"]


def test_put_global_permissions_writes_settings_file_and_preserves_other_keys(
    tmp_path: Path,
) -> None:
    settings_json = tmp_path / "settings.json"
    write_json(
        settings_json,
        {
            "permissions": {"allow": ["Bash(git *)"], "defaultMode": "acceptEdits"},
            "model": "sonnet",
        },
    )
    app.dependency_overrides[get_global_settings_path] = lambda: settings_json

    response = client.put(
        "/config/global/permissions",
        json={"allow": ["Edit(*)"], "ask": ["Bash(rm *)"], "deny": []},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["effective_permissions"]["allow"] == ["Edit(*)"]
    assert body["effective_permissions"]["ask"] == ["Bash(rm *)"]

    persisted = json.loads(settings_json.read_text())
    assert persisted["permissions"]["allow"] == ["Edit(*)"]
    assert persisted["permissions"]["defaultMode"] == "acceptEdits"
    assert persisted["model"] == "sonnet"


def test_put_project_permissions_writes_project_settings_file(tmp_path: Path) -> None:
    project_dir = tmp_path / "my-project"
    (project_dir / ".claude").mkdir(parents=True)
    write_json(
        project_dir / ".claude" / "settings.json",
        {"permissions": {"allow": ["Edit(src/**)"]}, "model": "opus"},
    )

    response = client.put(
        "/config/project/permissions",
        params={"path": str(project_dir)},
        json={"allow": ["Bash(git *)"], "ask": [], "deny": ["Bash(rm *)"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["own_permissions"]["allow"] == ["Bash(git *)"]
    assert body["own_permissions"]["deny"] == ["Bash(rm *)"]

    persisted = json.loads((project_dir / ".claude" / "settings.json").read_text())
    assert persisted["permissions"]["allow"] == ["Bash(git *)"]
    assert persisted["model"] == "opus"


def test_put_project_permissions_creates_settings_file_when_missing(tmp_path: Path) -> None:
    project_dir = tmp_path / "fresh-project"

    response = client.put(
        "/config/project/permissions",
        params={"path": str(project_dir)},
        json={"allow": ["Edit(*)"], "ask": [], "deny": []},
    )

    assert response.status_code == 200
    persisted = json.loads((project_dir / ".claude" / "settings.json").read_text())
    assert persisted["permissions"]["allow"] == ["Edit(*)"]
