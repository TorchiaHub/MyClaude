import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SessionInfo:
    pid: int
    session_id: str
    cwd: str
    status: str
    name: str | None = None
    started_at: int | None = None
    updated_at: int | None = None


def list_sessions(sessions_dir: Path) -> list[SessionInfo]:
    """List active Claude Code sessions from ~/.claude/sessions/*.json.

    This registry format is not documented as a stable public API, so parsing
    degrades gracefully: malformed JSON or files missing required fields are
    skipped rather than raising.
    """
    if not sessions_dir.is_dir():
        return []

    sessions = []
    for file in sorted(sessions_dir.glob("*.json")):
        session = _parse_session_file(file)
        if session is not None:
            sessions.append(session)
    return sessions


def _parse_session_file(path: Path) -> SessionInfo | None:
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    if not isinstance(data, dict):
        return None

    try:
        return SessionInfo(
            pid=data["pid"],
            session_id=data["sessionId"],
            cwd=data["cwd"],
            status=data["status"],
            name=data.get("name"),
            started_at=data.get("startedAt"),
            updated_at=data.get("updatedAt"),
        )
    except KeyError:
        return None
