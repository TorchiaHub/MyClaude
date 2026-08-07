import json
from pathlib import Path

from app.activity_monitor.drilldown import parse_activity_events


def write_lines(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")


def tool_use_record(
    *, tool_name: str, timestamp: str = "2026-08-06T18:53:34.234Z", session_id: str = "sess-1"
) -> dict:
    return {
        "type": "assistant",
        "timestamp": timestamp,
        "sessionId": session_id,
        "message": {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "toolu_1", "name": tool_name, "input": {}}],
        },
    }


def test_parse_activity_events_extracts_tool_use_blocks(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    write_lines(path, [tool_use_record(tool_name="Bash")])

    events = parse_activity_events(path)

    assert len(events) == 1
    assert events[0].tool_name == "Bash"
    assert events[0].timestamp == "2026-08-06T18:53:34.234Z"
    assert events[0].session_id == "sess-1"


def test_parse_activity_events_extracts_task_subagent_calls(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    write_lines(path, [tool_use_record(tool_name="Task")])

    events = parse_activity_events(path)

    assert events[0].tool_name == "Task"


def test_parse_activity_events_handles_multiple_tool_use_blocks_in_one_message(
    tmp_path: Path,
) -> None:
    path = tmp_path / "session.jsonl"
    record = {
        "type": "assistant",
        "timestamp": "2026-08-06T18:53:34.234Z",
        "sessionId": "sess-1",
        "message": {
            "content": [
                {"type": "tool_use", "name": "Read", "input": {}},
                {"type": "tool_use", "name": "Bash", "input": {}},
            ]
        },
    }
    write_lines(path, [record])

    events = parse_activity_events(path)

    assert [e.tool_name for e in events] == ["Read", "Bash"]


def test_parse_activity_events_ignores_text_content_blocks(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    record = {
        "type": "assistant",
        "timestamp": "2026-08-06T18:53:34.234Z",
        "sessionId": "sess-1",
        "message": {"content": [{"type": "text", "text": "hello"}]},
    }
    write_lines(path, [record])

    events = parse_activity_events(path)

    assert events == []


def test_parse_activity_events_ignores_non_assistant_lines(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    write_lines(path, [{"type": "user", "message": {"role": "user"}}])

    events = parse_activity_events(path)

    assert events == []


def test_parse_activity_events_skips_malformed_json_lines(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    good = json.dumps(tool_use_record(tool_name="Bash"))
    path.write_text(f"{good}\nnot valid json\n{good}\n")

    events = parse_activity_events(path)

    assert len(events) == 2


def test_parse_activity_events_handles_unrecognized_content_shape(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    record = {
        "type": "assistant",
        "timestamp": "2026-08-06T18:53:34.234Z",
        "sessionId": "sess-1",
        "message": {"content": "a bare string, not a list"},
    }
    write_lines(path, [record])

    events = parse_activity_events(path)

    assert events == []


def test_parse_activity_events_returns_empty_list_for_missing_file(tmp_path: Path) -> None:
    events = parse_activity_events(tmp_path / "does-not-exist.jsonl")

    assert events == []
