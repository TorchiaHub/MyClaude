from pathlib import Path

from app.json_store import read_json

PERMISSION_RULE_TYPES = ("allow", "ask", "deny")


def read_global_config(claude_json_path: Path) -> dict:
    return read_json(claude_json_path)


def read_global_settings(settings_json_path: Path) -> dict:
    return read_json(settings_json_path)


def read_local_settings(local_settings_path: Path) -> dict:
    return read_json(local_settings_path)


def read_project_mcp_config(mcp_json_path: Path) -> dict:
    return read_json(mcp_json_path).get("mcpServers", {})


def compute_effective_permissions(
    user_settings: dict, project_settings: dict, local_settings: dict
) -> dict:
    """Compute the permission rules Claude Code actually applies.

    User and project settings merge (concatenate) their allow/ask/deny lists,
    matching documented behavior. `settings.local.json` is handled separately:
    for any rule type it defines, it REPLACES the merged list wholesale rather
    than appending to it — this replicates a known Claude Code bug where the
    documented "merge across scopes" does not hold for the local scope.
    """
    effective = {rule_type: [] for rule_type in PERMISSION_RULE_TYPES}
    for scope in (user_settings, project_settings):
        scope_permissions = scope.get("permissions", {})
        for rule_type in PERMISSION_RULE_TYPES:
            effective[rule_type].extend(scope_permissions.get(rule_type, []))

    local_permissions = local_settings.get("permissions", {})
    for rule_type in PERMISSION_RULE_TYPES:
        if rule_type in local_permissions:
            effective[rule_type] = list(local_permissions[rule_type])

    return effective
