import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.activity_monitor import encode_project_path
from app.api.dependencies import get_claude_home_path
from app.main import app

client = TestClient(app)


def write_session(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_websocket_live_activity_pushes_current_sessions(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    sessions_dir = claude_home / "sessions"
    sessions_dir.mkdir(parents=True)
    write_session(
        sessions_dir / "123.json",
        {"pid": 123, "sessionId": "sess-1", "cwd": "/home/matt/proj", "status": "busy"},
    )

    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    with client.websocket_connect("/activity/live") as websocket:
        message = websocket.receive_json()

    app.dependency_overrides.clear()

    assert len(message) == 1
    assert message[0]["session_id"] == "sess-1"
    assert message[0]["status"] == "busy"


def test_websocket_live_activity_sends_empty_list_when_no_sessions(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"

    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    with client.websocket_connect("/activity/live") as websocket:
        message = websocket.receive_json()

    app.dependency_overrides.clear()

    assert message == []


def test_get_session_drilldown_returns_recent_tool_use_events(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    cwd = "/home/matt/proj"
    session_id = "sess-1"
    transcript_dir = claude_home / "projects" / encode_project_path(cwd)
    transcript_dir.mkdir(parents=True)
    record = {
        "type": "assistant",
        "timestamp": "2026-08-06T18:00:00Z",
        "sessionId": session_id,
        "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {}}]},
    }
    (transcript_dir / f"{session_id}.jsonl").write_text(json.dumps(record) + "\n")

    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.get(f"/activity/sessions/{session_id}/drilldown", params={"cwd": cwd})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    events = response.json()
    assert events == [
        {"timestamp": "2026-08-06T18:00:00Z", "tool_name": "Bash", "session_id": session_id}
    ]


def test_get_session_drilldown_returns_empty_list_when_transcript_missing(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"

    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.get("/activity/sessions/unknown-session/drilldown", params={"cwd": "/nope"})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []
