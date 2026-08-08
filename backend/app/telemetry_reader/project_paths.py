import re
from pathlib import Path

_NON_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]")


def encode_project_path(project_path: str) -> str:
    """Encode an absolute project path into the directory name Claude Code
    uses under ~/.claude/projects/.

    This scheme is NOT documented officially — reverse-engineered by
    comparing real project paths (from ~/.claude.json) against their
    corresponding ~/.claude/projects/ directory names: every character
    outside [A-Za-z0-9] becomes '-'. Treat as a best-effort heuristic that
    may break between Claude Code versions, matching the project's stance
    that the transcript storage layout is an internal, unstable format.
    """
    return _NON_ALPHANUMERIC.sub("-", project_path)


def find_transcript_files(claude_projects_root: Path, project_path: str) -> list[Path]:
    project_dir = claude_projects_root / encode_project_path(project_path)
    if not project_dir.is_dir():
        return []
    return sorted(project_dir.glob("*.jsonl"))
