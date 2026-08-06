from pathlib import Path

from app.library_registry.frontmatter import parse_frontmatter
from app.library_registry.models import LibraryItem, ResourceType, Scope

RESOURCE_SUBDIRS: dict[ResourceType, str] = {
    "agent": "agents",
    "command": "commands",
    "output_style": "output-styles",
}


def scan_library(claude_home: Path, project_dir: Path | None) -> list[LibraryItem]:
    items = _scan_scope_root(claude_home, "user")

    if project_dir is not None:
        items += _scan_scope_root(project_dir / ".claude", "project")

    return items


def _scan_scope_root(root: Path, scope: Scope) -> list[LibraryItem]:
    items = _scan_skills(root / "skills", scope)
    for resource_type, subdir in RESOURCE_SUBDIRS.items():
        items += _scan_markdown_resources(root / subdir, resource_type, scope)
    return items


def _scan_skills(root: Path, scope: Scope) -> list[LibraryItem]:
    if not root.is_dir():
        return []

    items = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        relative_dir = skill_md.parent.relative_to(root)
        frontmatter = parse_frontmatter(skill_md.read_text())
        folder = "" if relative_dir.parent == Path(".") else relative_dir.parent.as_posix()
        items.append(
            LibraryItem(
                id=f"skill:{scope}:{relative_dir.as_posix()}",
                resource_type="skill",
                scope=scope,
                name=frontmatter.get("name") or relative_dir.name,
                description=frontmatter.get("description", ""),
                folder=folder,
                path=str(skill_md),
                tags=_extract_tags(frontmatter),
            )
        )
    return items


def _scan_markdown_resources(
    root: Path, resource_type: ResourceType, scope: Scope
) -> list[LibraryItem]:
    if not root.is_dir():
        return []

    items = []
    for md_file in sorted(root.rglob("*.md")):
        relative = md_file.relative_to(root)
        frontmatter = parse_frontmatter(md_file.read_text())
        folder = "" if relative.parent == Path(".") else relative.parent.as_posix()
        items.append(
            LibraryItem(
                id=f"{resource_type}:{scope}:{relative.as_posix()}",
                resource_type=resource_type,
                scope=scope,
                name=frontmatter.get("name") or relative.stem,
                description=frontmatter.get("description", ""),
                folder=folder,
                path=str(md_file),
                tags=_extract_tags(frontmatter),
            )
        )
    return items


def _extract_tags(frontmatter: dict) -> list[str]:
    tags = frontmatter.get("tags")
    if isinstance(tags, list):
        return [str(tag) for tag in tags]
    if isinstance(tags, str):
        return [tag for tag in tags.replace(",", " ").split() if tag]
    return []
