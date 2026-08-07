import json
from pathlib import Path

from app.config_reader import (
    compute_effective_permissions,
    read_global_config,
    read_global_settings,
    read_local_settings,
    read_project_mcp_config,
    replace_permission_rules,
)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_read_global_config_returns_parsed_json(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"mcpServers": {"ollama": {"command": "ollama"}}})

    result = read_global_config(claude_json)

    assert result == {"mcpServers": {"ollama": {"command": "ollama"}}}


def test_read_global_config_returns_empty_dict_when_file_missing(tmp_path: Path) -> None:
    result = read_global_config(tmp_path / "does-not-exist.json")

    assert result == {}


def test_read_global_settings_returns_parsed_json(tmp_path: Path) -> None:
    settings_json = tmp_path / "settings.json"
    write_json(settings_json, {"permissions": {"allow": ["Bash(git *)"]}})

    result = read_global_settings(settings_json)

    assert result == {"permissions": {"allow": ["Bash(git *)"]}}


def test_read_local_settings_returns_parsed_json(tmp_path: Path) -> None:
    local_settings = tmp_path / "settings.local.json"
    write_json(local_settings, {"permissions": {"allow": ["Bash(npm test)"]}})

    result = read_local_settings(local_settings)

    assert result == {"permissions": {"allow": ["Bash(npm test)"]}}


def test_read_local_settings_returns_empty_dict_when_file_missing(tmp_path: Path) -> None:
    result = read_local_settings(tmp_path / "settings.local.json")

    assert result == {}


def test_read_project_mcp_config_returns_mcp_servers_dict(tmp_path: Path) -> None:
    mcp_json = tmp_path / ".mcp.json"
    write_json(mcp_json, {"mcpServers": {"db": {"type": "stdio", "command": "dbhub"}}})

    result = read_project_mcp_config(mcp_json)

    assert result == {"db": {"type": "stdio", "command": "dbhub"}}


def test_read_project_mcp_config_returns_empty_dict_when_key_missing(tmp_path: Path) -> None:
    mcp_json = tmp_path / ".mcp.json"
    write_json(mcp_json, {})

    result = read_project_mcp_config(mcp_json)

    assert result == {}


def test_compute_effective_permissions_merges_user_and_project_scopes() -> None:
    user_settings = {"permissions": {"allow": ["Bash(git *)"], "deny": [], "ask": []}}
    project_settings = {"permissions": {"allow": ["Edit(src/**)"], "deny": [], "ask": []}}
    local_settings: dict = {}

    result = compute_effective_permissions(user_settings, project_settings, local_settings)

    assert result == {
        "allow": ["Bash(git *)", "Edit(src/**)"],
        "ask": [],
        "deny": [],
    }


def test_compute_effective_permissions_local_settings_replaces_not_merges() -> None:
    """Reproduces the documented Claude Code bug: settings.local.json permission
    arrays overwrite the merged user+project result instead of appending to it."""
    user_settings = {"permissions": {"allow": ["Bash(git *)", "Read(*.env)"]}}
    project_settings = {"permissions": {"allow": ["Edit(src/**)"]}}
    local_settings = {"permissions": {"allow": ["Bash(npm test)"]}}

    result = compute_effective_permissions(user_settings, project_settings, local_settings)

    assert result["allow"] == ["Bash(npm test)"]


def test_compute_effective_permissions_local_settings_only_overrides_defined_rule_types() -> None:
    user_settings = {"permissions": {"allow": ["Bash(git *)"], "deny": ["Bash(rm *)"]}}
    project_settings = {"permissions": {"allow": ["Edit(src/**)"]}}
    local_settings = {"permissions": {"deny": ["Bash(curl *)"]}}

    result = compute_effective_permissions(user_settings, project_settings, local_settings)

    assert result["allow"] == ["Bash(git *)", "Edit(src/**)"]
    assert result["deny"] == ["Bash(curl *)"]


def test_replace_permission_rules_replaces_allow_ask_deny() -> None:
    settings = {"permissions": {"allow": ["Bash(git *)"], "ask": [], "deny": []}}

    result = replace_permission_rules(
        settings, {"allow": ["Edit(*)"], "ask": ["Bash(rm *)"], "deny": []}
    )

    assert result["permissions"]["allow"] == ["Edit(*)"]
    assert result["permissions"]["ask"] == ["Bash(rm *)"]
    assert result["permissions"]["deny"] == []


def test_replace_permission_rules_preserves_other_permission_keys() -> None:
    settings = {"permissions": {"allow": [], "ask": [], "deny": [], "defaultMode": "acceptEdits"}}

    result = replace_permission_rules(settings, {"allow": ["Edit(*)"], "ask": [], "deny": []})

    assert result["permissions"]["defaultMode"] == "acceptEdits"


def test_replace_permission_rules_preserves_other_top_level_keys() -> None:
    settings = {
        "permissions": {"allow": [], "ask": [], "deny": []},
        "model": "sonnet",
        "hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "echo hi"}]}]},
    }

    result = replace_permission_rules(settings, {"allow": ["Edit(*)"], "ask": [], "deny": []})

    assert result["model"] == "sonnet"
    assert result["hooks"] == settings["hooks"]


def test_replace_permission_rules_works_when_settings_has_no_permissions_key() -> None:
    result = replace_permission_rules({}, {"allow": ["Edit(*)"], "ask": [], "deny": []})

    assert result["permissions"] == {"allow": ["Edit(*)"], "ask": [], "deny": []}


def test_replace_permission_rules_does_not_mutate_input() -> None:
    settings = {"permissions": {"allow": ["Bash(git *)"], "ask": [], "deny": []}}

    replace_permission_rules(settings, {"allow": ["Edit(*)"], "ask": [], "deny": []})

    assert settings["permissions"]["allow"] == ["Bash(git *)"]
