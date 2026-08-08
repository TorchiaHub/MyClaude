import json
from pathlib import Path

from app.activity_monitor.sessions import list_sessions


def write_session(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_list_sessions_parses_real_session_shape(tmp_path: Path) -> None:
    write_session(
        tmp_path / "285990.json",
        {
            "pid": 285990,
            "sessionId": "0eb9cb3a-fcec-4968-a909-28d4de260888",
            "cwd": "/home/matt/Documents/MY_CLaude",
            "startedAt": 1786019963661,
            "version": "2.1.222",
            "kind": "interactive",
            "name": "control-plane-observability-design",
            "status": "busy",
            "updatedAt": 1786044192263,
        },
    )

    sessions = list_sessions(tmp_path)

    assert len(sessions) == 1
    session = sessions[0]
    assert session.pid == 285990
    assert session.session_id == "0eb9cb3a-fcec-4968-a909-28d4de260888"
    assert session.cwd == "/home/matt/Documents/MY_CLaude"
    assert session.status == "busy"
    assert session.name == "control-plane-observability-design"
    assert session.updated_at == 1786044192263


def test_list_sessions_returns_multiple_sessions_sorted_by_filename(tmp_path: Path) -> None:
    write_session(
        tmp_path / "222.json",
        {"pid": 222, "sessionId": "s2", "cwd": "/b", "status": "idle"},
    )
    write_session(
        tmp_path / "111.json",
        {"pid": 111, "sessionId": "s1", "cwd": "/a", "status": "busy"},
    )

    sessions = list_sessions(tmp_path)

    assert [s.pid for s in sessions] == [111, 222]


def test_list_sessions_skips_malformed_json_file(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("not valid json")
    write_session(
        tmp_path / "good.json", {"pid": 1, "sessionId": "s1", "cwd": "/a", "status": "busy"}
    )

    sessions = list_sessions(tmp_path)

    assert len(sessions) == 1
    assert sessions[0].pid == 1


def test_list_sessions_skips_file_missing_required_fields(tmp_path: Path) -> None:
    write_session(tmp_path / "incomplete.json", {"pid": 1})

    sessions = list_sessions(tmp_path)

    assert sessions == []


def test_list_sessions_returns_empty_list_when_directory_missing(tmp_path: Path) -> None:
    sessions = list_sessions(tmp_path / "does-not-exist")

    assert sessions == []


def test_list_sessions_defaults_optional_fields_to_none(tmp_path: Path) -> None:
    write_session(
        tmp_path / "minimal.json", {"pid": 1, "sessionId": "s1", "cwd": "/a", "status": "busy"}
    )

    sessions = list_sessions(tmp_path)

    assert sessions[0].name is None
    assert sessions[0].started_at is None
    assert sessions[0].updated_at is None
