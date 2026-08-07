import json
from pathlib import Path

from app.hooks_installer import (
    SESSION_START_HOOK_COMMAND,
    build_session_start_hook_command,
    install_session_start_hook,
    is_session_start_hook_installed,
    uninstall_session_start_hook,
)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_install_appends_entry_to_empty_settings(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})

    installed = install_session_start_hook(settings_path)

    assert installed is True
    data = json.loads(settings_path.read_text())
    session_start = data["hooks"]["SessionStart"]
    assert len(session_start) == 1
    assert session_start[0]["hooks"][0]["command"] == SESSION_START_HOOK_COMMAND
    assert session_start[0]["hooks"][0]["type"] == "command"


def test_install_preserves_other_tools_hook_entries(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(
        settings_path,
        {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "startup",
                        "hooks": [{"type": "command", "command": "other-tool.sh"}],
                    }
                ],
                "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "x"}]}],
            }
        },
    )

    install_session_start_hook(settings_path)

    data = json.loads(settings_path.read_text())
    session_start = data["hooks"]["SessionStart"]
    assert len(session_start) == 2
    assert session_start[0]["hooks"][0]["command"] == "other-tool.sh"
    assert data["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "x"


def test_install_is_idempotent(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})

    first = install_session_start_hook(settings_path)
    second = install_session_start_hook(settings_path)

    assert first is True
    assert second is False
    data = json.loads(settings_path.read_text())
    assert len(data["hooks"]["SessionStart"]) == 1


def test_is_session_start_hook_installed_false_when_missing(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})

    assert is_session_start_hook_installed(settings_path) is False


def test_is_session_start_hook_installed_true_after_install(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})
    install_session_start_hook(settings_path)

    assert is_session_start_hook_installed(settings_path) is True


def test_uninstall_removes_only_our_entry(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(
        settings_path,
        {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "startup",
                        "hooks": [{"type": "command", "command": "other-tool.sh"}],
                    }
                ]
            }
        },
    )
    install_session_start_hook(settings_path)

    removed = uninstall_session_start_hook(settings_path)

    assert removed is True
    data = json.loads(settings_path.read_text())
    session_start = data["hooks"]["SessionStart"]
    assert len(session_start) == 1
    assert session_start[0]["hooks"][0]["command"] == "other-tool.sh"


def test_uninstall_returns_false_when_not_installed(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})

    removed = uninstall_session_start_hook(settings_path)

    assert removed is False


def test_build_session_start_hook_command_embeds_given_port() -> None:
    command = build_session_start_hook_command(port=9999)

    assert "http://127.0.0.1:9999/hooks/session-start" in command


def test_install_with_custom_port_is_detected_as_installed(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})

    install_session_start_hook(settings_path, port=9999)

    assert is_session_start_hook_installed(settings_path) is True
    data = json.loads(settings_path.read_text())
    assert "9999" in data["hooks"]["SessionStart"][0]["hooks"][0]["command"]


def test_install_with_custom_port_is_idempotent_regardless_of_port_used_to_check(
    tmp_path: Path,
) -> None:
    """Re-running install (e.g. after the app restarted on a different port)
    must recognize the existing entry and not create a duplicate."""
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})

    install_session_start_hook(settings_path, port=8000)
    second = install_session_start_hook(settings_path, port=9999)

    assert second is False
    data = json.loads(settings_path.read_text())
    assert len(data["hooks"]["SessionStart"]) == 1


def test_uninstall_removes_entry_installed_with_a_custom_port(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})
    install_session_start_hook(settings_path, port=9999)

    removed = uninstall_session_start_hook(settings_path)

    assert removed is True
    assert is_session_start_hook_installed(settings_path) is False
