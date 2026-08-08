from dataclasses import dataclass, field
from pathlib import Path

from app.library_registry.frontmatter import parse_frontmatter
from app.telemetry_reader.project_paths import encode_project_path


@dataclass(frozen=True)
class MemoryTopic:
    filename: str
    name: str
    description: str
    metadata: dict
    content: str
    modified: float


@dataclass(frozen=True)
class ProjectMemory:
    index_content: str
    topics: list[MemoryTopic] = field(default_factory=list)


def read_project_memory(claude_projects_root: Path, project_path: str) -> ProjectMemory | None:
    """Read the auto memory (~/.claude/projects/<project>/memory/) that Claude
    Code writes on its own without user intervention: MEMORY.md is a plain
    index; topic files carry frontmatter (name, description, metadata) --
    no "modified" frontmatter field is present in real files despite the
    docs mentioning one, so "modified" here is the file's real mtime.
    """
    memory_dir = claude_projects_root / encode_project_path(project_path) / "memory"
    if not memory_dir.is_dir():
        return None

    index_path = memory_dir / "MEMORY.md"
    index_content = index_path.read_text() if index_path.is_file() else ""

    topics = []
    for topic_file in sorted(memory_dir.glob("*.md")):
        if topic_file.name == "MEMORY.md":
            continue
        topic = _parse_topic_file(topic_file)
        if topic is not None:
            topics.append(topic)

    return ProjectMemory(index_content=index_content, topics=topics)


def _parse_topic_file(topic_file: Path) -> MemoryTopic | None:
    raw = topic_file.read_text()
    frontmatter = parse_frontmatter(raw)
    if not frontmatter:
        return None

    body = raw.split("---", 2)[-1].lstrip("\n") if raw.startswith("---") else raw

    return MemoryTopic(
        filename=topic_file.name,
        name=frontmatter.get("name", topic_file.stem),
        description=frontmatter.get("description", ""),
        metadata=frontmatter.get("metadata", {}) or {},
        content=body,
        modified=topic_file.stat().st_mtime,
    )
