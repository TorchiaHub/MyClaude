from pathlib import Path

from app.json_store import read_json, write_json

# Reads the hook's stdin JSON (session_id, cwd, hook_event_name, ...) and
# forwards it as-is to the Control Plane backend so it can correlate real
# sessions with whichever packages were active at that moment. Silent/best
# effort: never blocks a Claude Code session if the backend isn't running.
_HOOK_PATH = "/hooks/session-start"


def build_session_start_hook_command(port: int) -> str:
    return (
        f"curl -s -X POST http://127.0.0.1:{port}{_HOOK_PATH} "
        "-H 'Content-Type: application/json' -d @- --max-time 2 -o /dev/null || true"
    )


# Back-compat default (also what tests assert against when port doesn't matter).
SESSION_START_HOOK_COMMAND = build_session_start_hook_command(8000)


def _is_our_command(command: str) -> bool:
    # Match by endpoint path + curl prefix rather than the full string, so an
    # entry installed under a different port (app restarted with PORT= set)
    # is still recognized as "ours" instead of producing a duplicate.
    return command.startswith("curl") and _HOOK_PATH in command


def _find_our_group_index(session_start: list) -> int | None:
    for index, group in enumerate(session_start):
        for hook in group.get("hooks", []):
            if _is_our_command(hook.get("command", "")):
                return index
    return None


def is_session_start_hook_installed(settings_path: Path) -> bool:
    data = read_json(settings_path)
    session_start = data.get("hooks", {}).get("SessionStart", [])
    return _find_our_group_index(session_start) is not None


def install_session_start_hook(settings_path: Path, *, port: int = 8000) -> bool:
    """Append our SessionStart hook entry, additive to whatever else is
    already registered there. Idempotent: returns False without writing if
    already installed (regardless of which port it was originally installed
    with)."""
    data = read_json(settings_path)
    hooks = data.setdefault("hooks", {})
    session_start = hooks.setdefault("SessionStart", [])

    if _find_our_group_index(session_start) is not None:
        return False

    session_start.append(
        {
            "matcher": "",
            "hooks": [{"type": "command", "command": build_session_start_hook_command(port)}],
        }
    )
    write_json(settings_path, data)
    return True


def uninstall_session_start_hook(settings_path: Path) -> bool:
    """Remove only our own SessionStart entry, leaving any other tool's
    entries untouched. Returns False if we were never installed."""
    data = read_json(settings_path)
    session_start = data.get("hooks", {}).get("SessionStart", [])

    index = _find_our_group_index(session_start)
    if index is None:
        return False

    del session_start[index]
    write_json(settings_path, data)
    return True
