import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_claude_home_path, get_global_settings_path
from app.main import app
from app.telemetry_reader.project_paths import encode_project_path

client = TestClient(app)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_get_memory_returns_project_memory(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    project_path = "/home/matt/proj"
    memory_dir = claude_home / "projects" / encode_project_path(project_path) / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("# Memory Index\n")
    (memory_dir / "topic.md").write_text("---\nname: t\ndescription: d\n---\ncontent\n")

    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.get("/memory", params={"project_path": project_path})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert "Memory Index" in body["index_content"]
    assert body["topics"][0]["name"] == "t"


def test_get_memory_returns_404_when_no_memory(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.get("/memory", params={"project_path": "/nope"})

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_get_rules_returns_scanned_rules(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    rules_dir = claude_home / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "docs.md").write_text('---\npaths:\n  - "**/*.md"\n---\nBody.\n')

    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.get("/rules")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body[0]["name"] == "docs"
    assert body[0]["paths"] == ["**/*.md"]


def test_get_checkpoints_returns_timeline(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    project_path = "/home/matt/proj"
    session_id = "sess-1"
    project_dir = claude_home / "projects" / encode_project_path(project_path)
    project_dir.mkdir(parents=True)
    record = {
        "type": "file-history-snapshot",
        "messageId": "msg-1",
        "snapshot": {
            "messageId": "msg-1",
            "trackedFileBackups": {},
            "timestamp": "2026-08-06T13:09:07.006Z",
        },
        "isSnapshotUpdate": False,
    }
    (project_dir / f"{session_id}.jsonl").write_text(json.dumps(record) + "\n")

    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.get(f"/checkpoints/{session_id}", params={"cwd": project_path})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["checkpoints"][0]["message_id"] == "msg-1"
    assert "coverage_caveat" in body


def test_get_sandbox_config_returns_raw_passthrough(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {"sandbox": {"filesystem": {"allowManagedReadPathsOnly": True}}})
    app.dependency_overrides[get_global_settings_path] = lambda: settings_path

    response = client.get("/sandbox/config")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["enabled"] is True


def test_get_output_styles_returns_library_scanned_items(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    styles_dir = claude_home / "output-styles"
    styles_dir.mkdir(parents=True)
    (styles_dir / "concise.md").write_text("---\nname: concise\ndescription: Terse\n---\nBody.\n")

    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.get("/output-styles")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body[0]["name"] == "concise"
