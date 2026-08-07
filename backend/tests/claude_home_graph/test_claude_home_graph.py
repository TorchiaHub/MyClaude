import json
from pathlib import Path

from app.claude_home_graph import build_claude_home_graph


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def make_skill(root: Path, relative_dir: str, name: str) -> None:
    skill_dir = root / "skills" / relative_dir
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n")


def test_graph_always_includes_claude_md_and_settings_nodes(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# Hello")
    write_json(tmp_path / "settings.json", {})

    graph = build_claude_home_graph(tmp_path)

    node_ids = {n.id for n in graph.nodes}
    assert "file:CLAUDE.md" in node_ids
    assert "file:settings.json" in node_ids


def test_graph_includes_skill_nodes(tmp_path: Path) -> None:
    make_skill(tmp_path, "deploy", "deploy")
    write_json(tmp_path / "settings.json", {})

    graph = build_claude_home_graph(tmp_path)

    skill_nodes = [n for n in graph.nodes if n.type == "skill"]
    assert any(n.label == "deploy" for n in skill_nodes)


def test_graph_links_nested_skill_to_parent(tmp_path: Path) -> None:
    make_skill(tmp_path, "app-store", "app-store")
    make_skill(tmp_path, "app-store/ad-attribution", "ad-attribution")
    write_json(tmp_path / "settings.json", {})

    graph = build_claude_home_graph(tmp_path)

    parent_id = "skill:user:app-store"
    child_id = "skill:user:app-store/ad-attribution"
    assert any(e.source == parent_id and e.target == child_id for e in graph.edges)


def test_graph_links_hook_to_existing_script_file(tmp_path: Path) -> None:
    (tmp_path / "hooks" / "scripts").mkdir(parents=True)
    (tmp_path / "hooks" / "scripts" / "hooks.py").write_text("print('hi')")
    write_json(
        tmp_path / "settings.json",
        {
            "hooks": {
                "PreToolUse": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 ~/.claude/hooks/scripts/hooks.py",
                            }
                        ]
                    }
                ]
            }
        },
    )

    graph = build_claude_home_graph(tmp_path)

    script_node_ids = {n.id for n in graph.nodes if n.type == "script"}
    assert "file:hooks/scripts/hooks.py" in script_node_ids
    assert any(
        e.source == "file:settings.json" and e.target == "file:hooks/scripts/hooks.py"
        for e in graph.edges
    )


def test_graph_ignores_hook_command_referencing_nonexistent_script(tmp_path: Path) -> None:
    write_json(
        tmp_path / "settings.json",
        {
            "hooks": {
                "PreToolUse": [
                    {"hooks": [{"type": "command", "command": "python3 ~/.claude/missing.py"}]}
                ]
            }
        },
    )

    graph = build_claude_home_graph(tmp_path)

    assert not any(n.type == "script" for n in graph.nodes)


def test_graph_includes_rule_nodes(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "python.md").write_text("---\npaths:\n  - '**/*.py'\n---\nUse type hints.")
    write_json(tmp_path / "settings.json", {})

    graph = build_claude_home_graph(tmp_path)

    rule_nodes = [n for n in graph.nodes if n.type == "rule"]
    assert any(n.label == "python" for n in rule_nodes)


def test_graph_ignores_malformed_hooks_value(tmp_path: Path) -> None:
    write_json(tmp_path / "settings.json", {"hooks": {"PreToolUse": "not-a-list"}})

    graph = build_claude_home_graph(tmp_path)

    assert not any(n.type == "script" for n in graph.nodes)


def test_graph_handles_missing_settings_file(tmp_path: Path) -> None:
    graph = build_claude_home_graph(tmp_path)

    node_ids = {n.id for n in graph.nodes}
    assert "file:settings.json" in node_ids
