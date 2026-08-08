import json
from pathlib import PurePosixPath

__all__ = [
    "bundle_skill_names",
    "bundle_agent_names",
    "bundle_command_names",
    "bundle_mcp_server_names",
    "detect_missing_dependencies",
]


def _bundle_resource_names(bundle: dict, *, prefix: str) -> set[str]:
    names = set()
    for relative_path in bundle.get("files", {}):
        parts = PurePosixPath(relative_path).parts
        if len(parts) >= 3 and f"{parts[0]}/{parts[1]}" == prefix:
            names.add(parts[2])
    return names


def bundle_skill_names(bundle: dict) -> set[str]:
    return _bundle_resource_names(bundle, prefix=".claude/skills")


def _bundle_markdown_resource_names(bundle: dict, *, folder: str) -> set[str]:
    names = set()
    for relative_path in bundle.get("files", {}):
        path = PurePosixPath(relative_path)
        if path.parent.as_posix() == f".claude/{folder}" and path.suffix == ".md":
            names.add(path.stem)
    return names


def bundle_agent_names(bundle: dict) -> set[str]:
    return _bundle_markdown_resource_names(bundle, folder="agents")


def bundle_command_names(bundle: dict) -> set[str]:
    return _bundle_markdown_resource_names(bundle, folder="commands")


def bundle_mcp_server_names(bundle: dict) -> set[str]:
    mcp_json = bundle.get("files", {}).get(".mcp.json")
    if not mcp_json:
        return set()
    try:
        data = json.loads(mcp_json)
    except json.JSONDecodeError:
        return set()
    if not isinstance(data, dict) or not isinstance(data.get("mcpServers"), dict):
        return set()
    return set(data["mcpServers"])


def detect_missing_dependencies(
    bundle: dict,
    *,
    local_skill_names: set[str],
    local_agent_names: set[str],
    local_command_names: set[str],
    local_mcp_server_names: set[str],
) -> dict[str, list[str]]:
    return {
        "missing_skills": sorted(bundle_skill_names(bundle) - local_skill_names),
        "missing_agents": sorted(bundle_agent_names(bundle) - local_agent_names),
        "missing_commands": sorted(bundle_command_names(bundle) - local_command_names),
        "missing_mcp_servers": sorted(bundle_mcp_server_names(bundle) - local_mcp_server_names),
    }
