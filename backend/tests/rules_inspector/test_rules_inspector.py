from pathlib import Path

from app.rules_inspector import scan_rules


def make_rule(
    root: Path, relative_path: str, paths_pattern: list[str], body: str = "Body."
) -> None:
    rule_file = root / relative_path
    rule_file.parent.mkdir(parents=True, exist_ok=True)
    patterns = "\n".join(f'  - "{p}"' for p in paths_pattern)
    rule_file.write_text(f"---\npaths:\n{patterns}\n---\n\n{body}\n")


def test_scan_rules_finds_user_level_rule(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    make_rule(claude_home / "rules", "markdown-docs.md", ["**/*.md"])

    rules = scan_rules(claude_home, None)

    assert len(rules) == 1
    assert rules[0].name == "markdown-docs"
    assert rules[0].paths == ["**/*.md"]
    assert rules[0].scope == "user"


def test_scan_rules_finds_nested_rule_recursively(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    make_rule(claude_home / "rules", "ecc/angular/hooks.md", ["*.ts"])

    rules = scan_rules(claude_home, None)

    assert len(rules) == 1
    assert rules[0].name == "hooks"
    assert rules[0].relative_folder == "ecc/angular"


def test_scan_rules_includes_project_scope(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    project_dir = tmp_path / "my-project"
    make_rule(claude_home / "rules", "user-rule.md", ["*.py"])
    make_rule(project_dir / ".claude" / "rules", "project-rule.md", ["*.ts"])

    rules = scan_rules(claude_home, project_dir)

    scopes = {r.scope for r in rules}
    assert scopes == {"user", "project"}


def test_scan_rules_skips_file_without_paths_frontmatter(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    rules_dir = claude_home / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "no-frontmatter.md").write_text("Just plain text, no rule.\n")

    rules = scan_rules(claude_home, None)

    assert rules == []


def test_scan_rules_returns_empty_list_when_no_rules_dir(tmp_path: Path) -> None:
    rules = scan_rules(tmp_path / "does-not-exist", None)

    assert rules == []


def test_scan_rules_handles_single_string_paths_value(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    rules_dir = claude_home / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "single.md").write_text('---\npaths: "*.md"\n---\n\nBody.\n')

    rules = scan_rules(claude_home, None)

    assert rules[0].paths == ["*.md"]
