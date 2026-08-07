import re
from dataclasses import dataclass, field
from pathlib import Path

from app.config_reader import read_global_settings
from app.library_registry import scan_library
from app.rules_inspector import scan_rules

__all__ = ["GraphNode", "GraphEdge", "ClaudeHomeGraph", "build_claude_home_graph"]

_SCRIPT_REFERENCE_PATTERN = re.compile(r"(~?/?[^\s]*\.claude/[^\s]+)")


@dataclass(frozen=True)
class GraphNode:
    id: str
    type: str
    label: str


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    kind: str


@dataclass(frozen=True)
class ClaudeHomeGraph:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)


def _extract_script_relative_paths(command: str, claude_home: Path) -> list[str]:
    relative_paths = []
    for match in _SCRIPT_REFERENCE_PATTERN.findall(command):
        expanded = f"{claude_home.parent}{match[1:]}" if match.startswith("~") else match
        marker = ".claude/"
        # The regex requires ".claude/" to be part of the match, so it is always found.
        relative = expanded[expanded.index(marker) + len(marker) :]
        if (claude_home / relative).is_file():
            relative_paths.append(relative)
    return relative_paths


def _hook_commands(settings: dict) -> list[str]:
    commands = []
    for hook_entries in settings.get("hooks", {}).values():
        if not isinstance(hook_entries, list):
            continue
        for entry in hook_entries:
            for hook in entry.get("hooks", []):
                command = hook.get("command")
                if isinstance(command, str):
                    commands.append(command)
    return commands


def build_claude_home_graph(claude_home: Path) -> ClaudeHomeGraph:
    nodes: list[GraphNode] = [
        GraphNode(id="file:CLAUDE.md", type="memory", label="CLAUDE.md"),
        GraphNode(id="file:settings.json", type="settings", label="settings.json"),
    ]
    edges: list[GraphEdge] = []

    settings = read_global_settings(claude_home / "settings.json")

    library_items = scan_library(claude_home, None)
    skill_ids_by_relative_dir = {}
    for item in library_items:
        nodes.append(GraphNode(id=item.id, type=item.resource_type, label=item.name))
        if item.resource_type == "skill":
            relative_dir = item.id.split(":", 2)[2]
            skill_ids_by_relative_dir[relative_dir] = item.id

    for item in library_items:
        if item.resource_type == "skill" and item.folder:
            parent_id = skill_ids_by_relative_dir.get(item.folder)
            if parent_id:
                edges.append(GraphEdge(source=parent_id, target=item.id, kind="nested_skill"))

    for rule in scan_rules(claude_home, None):
        rule_id = f"rule:{rule.scope}:{rule.file_path}"
        nodes.append(GraphNode(id=rule_id, type="rule", label=rule.name))

    seen_script_paths: set[str] = set()
    for command in _hook_commands(settings):
        for relative_path in _extract_script_relative_paths(command, claude_home):
            script_id = f"file:{relative_path}"
            if relative_path not in seen_script_paths:
                seen_script_paths.add(relative_path)
                nodes.append(GraphNode(id=script_id, type="script", label=relative_path))
            edges.append(GraphEdge(source="file:settings.json", target=script_id, kind="hook"))

    return ClaudeHomeGraph(nodes=nodes, edges=edges)
