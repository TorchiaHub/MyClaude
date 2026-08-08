import json

from app.package_registry.dependencies import (
    bundle_agent_names,
    bundle_command_names,
    bundle_mcp_server_names,
    bundle_skill_names,
    detect_missing_dependencies,
)


def _bundle_with_files(files: dict) -> dict:
    return {"files": files}


def test_bundle_skill_names_extracts_top_level_skill_directory_names():
    bundle = _bundle_with_files(
        {
            ".claude/skills/deploy/SKILL.md": "...",
            ".claude/skills/deploy/scripts/run.sh": "...",
            ".claude/skills/refactor/SKILL.md": "...",
        }
    )

    assert bundle_skill_names(bundle) == {"deploy", "refactor"}


def test_bundle_agent_names_extracts_stem_of_agent_files():
    bundle = _bundle_with_files({".claude/agents/reviewer.md": "..."})

    assert bundle_agent_names(bundle) == {"reviewer"}


def test_bundle_command_names_extracts_stem_of_command_files():
    bundle = _bundle_with_files({".claude/commands/deploy.md": "..."})

    assert bundle_command_names(bundle) == {"deploy"}


def test_bundle_mcp_server_names_reads_mcp_json_server_keys():
    bundle = _bundle_with_files({".mcp.json": '{"mcpServers": {"obsidian": {}, "postgres": {}}}'})

    assert bundle_mcp_server_names(bundle) == {"obsidian", "postgres"}


def test_bundle_mcp_server_names_empty_when_no_mcp_json():
    assert bundle_mcp_server_names(_bundle_with_files({})) == set()


def test_bundle_mcp_server_names_empty_when_mcp_json_is_malformed():
    bundle = _bundle_with_files({".mcp.json": "not valid json"})

    assert bundle_mcp_server_names(bundle) == set()


def test_bundle_mcp_server_names_empty_when_mcp_json_is_not_an_object():
    bundle = _bundle_with_files({".mcp.json": json.dumps([1, 2, 3])})

    assert bundle_mcp_server_names(bundle) == set()


def test_bundle_mcp_server_names_empty_when_mcp_servers_value_is_not_an_object():
    bundle = _bundle_with_files({".mcp.json": json.dumps({"mcpServers": ["not", "a", "dict"]})})

    assert bundle_mcp_server_names(bundle) == set()


def test_detect_missing_dependencies_reports_only_names_absent_locally():
    bundle = _bundle_with_files(
        {
            ".claude/skills/deploy/SKILL.md": "...",
            ".claude/skills/refactor/SKILL.md": "...",
            ".claude/agents/reviewer.md": "...",
            ".mcp.json": '{"mcpServers": {"obsidian": {}, "postgres": {}}}',
        }
    )

    missing = detect_missing_dependencies(
        bundle,
        local_skill_names={"deploy"},
        local_agent_names=set(),
        local_command_names=set(),
        local_mcp_server_names={"postgres"},
    )

    assert missing == {
        "missing_skills": ["refactor"],
        "missing_agents": ["reviewer"],
        "missing_commands": [],
        "missing_mcp_servers": ["obsidian"],
    }
