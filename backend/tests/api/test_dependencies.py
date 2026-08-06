from pathlib import Path

from app.api.dependencies import (
    get_claude_home_path,
    get_claude_json_path,
    get_global_settings_path,
)


def test_get_claude_json_path_defaults_under_home() -> None:
    assert get_claude_json_path() == Path.home() / ".claude.json"


def test_get_global_settings_path_defaults_under_home() -> None:
    assert get_global_settings_path() == Path.home() / ".claude" / "settings.json"


def test_get_claude_home_path_defaults_under_home() -> None:
    assert get_claude_home_path() == Path.home() / ".claude"
