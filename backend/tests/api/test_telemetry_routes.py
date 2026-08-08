import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_claude_home_path, get_claude_json_path
from app.main import app
from app.telemetry_reader.project_paths import encode_project_path

client = TestClient(app)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_get_telemetry_summary_returns_cumulative_and_period_totals(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    claude_home = tmp_path / "claude-home"
    project_path = "/home/matt/my-project"
    write_json(
        claude_json,
        {"projects": {project_path: {"lastCost": 1.5, "lastTotalInputTokens": 100}}},
    )
    project_dir = claude_home / "projects" / encode_project_path(project_path)
    project_dir.mkdir(parents=True)
    (project_dir / "session.jsonl").write_text(
        json.dumps(
            {
                "type": "assistant",
                "timestamp": "2026-08-01T10:00:00Z",
                "message": {
                    "model": "claude-sonnet-5",
                    "usage": {"input_tokens": 10, "output_tokens": 20},
                },
            }
        )
        + "\n"
    )

    app.dependency_overrides[get_claude_json_path] = lambda: claude_json
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.get("/telemetry/summary", params={"project_path": project_path})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["cumulative"]["cost_usd"] == 1.5
    assert body["turn_count"] == 1
    assert body["period_input_tokens"] == 10
    assert body["tokens_by_model"]["claude-sonnet-5"] == {"input_tokens": 10, "output_tokens": 20}


def test_get_telemetry_summary_handles_unknown_project(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    claude_home = tmp_path / "claude-home"
    write_json(claude_json, {"projects": {}})

    app.dependency_overrides[get_claude_json_path] = lambda: claude_json
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.get("/telemetry/summary", params={"project_path": "/unknown"})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["cumulative"] is None
    assert body["turn_count"] == 0


def test_get_telemetry_summary_applies_since_and_until_filters(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    claude_home = tmp_path / "claude-home"
    project_path = "/home/matt/my-project"
    write_json(claude_json, {"projects": {project_path: {}}})
    project_dir = claude_home / "projects" / encode_project_path(project_path)
    project_dir.mkdir(parents=True)
    records = [
        {
            "type": "assistant",
            "timestamp": ts,
            "message": {
                "model": "claude-sonnet-5",
                "usage": {"input_tokens": 1, "output_tokens": 0},
            },
        }
        for ts in ["2026-08-01T00:00:00Z", "2026-08-10T00:00:00Z"]
    ]
    (project_dir / "session.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")

    app.dependency_overrides[get_claude_json_path] = lambda: claude_json
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.get(
        "/telemetry/summary",
        params={
            "project_path": project_path,
            "since": "2026-08-05T00:00:00Z",
            "until": "2026-08-15T00:00:00Z",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["turn_count"] == 1
