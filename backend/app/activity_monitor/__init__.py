from pathlib import Path

from app.activity_monitor.drilldown import ActivityEvent, parse_activity_events
from app.activity_monitor.sessions import SessionInfo, list_sessions
from app.telemetry_reader.project_paths import encode_project_path

__all__ = [
    "SessionInfo",
    "list_sessions",
    "ActivityEvent",
    "parse_activity_events",
    "resolve_transcript_path",
]


def resolve_transcript_path(claude_projects_root: Path, cwd: str, session_id: str) -> Path:
    return claude_projects_root / encode_project_path(cwd) / f"{session_id}.jsonl"
