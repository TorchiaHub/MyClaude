from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.library_registry.frontmatter import parse_frontmatter

Scope = Literal["user", "project"]


@dataclass(frozen=True)
class RuleInfo:
    name: str
    scope: Scope
    relative_folder: str
    paths: list[str]
    file_path: str


def scan_rules(claude_home: Path, project_dir: Path | None) -> list[RuleInfo]:
    rules = _scan_rules_dir(claude_home / "rules", "user")
    if project_dir is not None:
        rules += _scan_rules_dir(project_dir / ".claude" / "rules", "project")
    return rules


def _scan_rules_dir(root: Path, scope: Scope) -> list[RuleInfo]:
    if not root.is_dir():
        return []

    rules = []
    for rule_file in sorted(root.rglob("*.md")):
        frontmatter = parse_frontmatter(rule_file.read_text())
        paths = _normalize_paths(frontmatter.get("paths"))
        if not paths:
            continue

        relative = rule_file.relative_to(root)
        folder = "" if relative.parent == Path(".") else relative.parent.as_posix()
        rules.append(
            RuleInfo(
                name=rule_file.stem,
                scope=scope,
                relative_folder=folder,
                paths=paths,
                file_path=str(rule_file),
            )
        )
    return rules


def _normalize_paths(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [value]
    return []
