import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ActivityEvent:
    timestamp: str
    tool_name: str
    session_id: str | None


def parse_activity_events(jsonl_path: Path) -> list[ActivityEvent]:
    """Extract tool_use activity (incl. Task subagent calls) from a session
    transcript for the "what is this session doing right now" drill-down.

    Like transcript_parser, this degrades gracefully on malformed lines or an
    unrecognized shape rather than raising, since the .jsonl format is internal
    to Claude Code and not guaranteed stable across versions.
    """
    if not jsonl_path.is_file():
        return []

    events = []
    for line in jsonl_path.read_text().splitlines():
        events.extend(_parse_line(line))
    return events


def _parse_line(line: str) -> list[ActivityEvent]:
    if not line.strip():
        return []

    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return []

    if not isinstance(record, dict) or record.get("type") != "assistant":
        return []

    content = record.get("message", {}).get("content")
    if not isinstance(content, list):
        return []

    timestamp = record.get("timestamp", "")
    session_id = record.get("sessionId")

    events = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            name = block.get("name")
            if isinstance(name, str):
                events.append(
                    ActivityEvent(timestamp=timestamp, tool_name=name, session_id=session_id)
                )
    return events
