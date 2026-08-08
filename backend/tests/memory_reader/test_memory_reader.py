from pathlib import Path

from app.memory_reader import read_project_memory
from app.telemetry_reader.project_paths import encode_project_path


def make_memory_dir(claude_home: Path, project_path: str) -> Path:
    memory_dir = claude_home / "projects" / encode_project_path(project_path) / "memory"
    memory_dir.mkdir(parents=True)
    return memory_dir


def test_read_project_memory_parses_index_and_topic_files(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    memory_dir = make_memory_dir(claude_home, "/home/matt/my-project")
    (memory_dir / "MEMORY.md").write_text(
        "# Memory Index\n\n- [User Context](user_context.md) — chi è l'utente\n"
    )
    (memory_dir / "user_context.md").write_text(
        "---\nname: user-context\ndescription: Contesto utente\nmetadata:\n  type: user\n---\n"
        "L'utente lavora su un progetto scolastico.\n"
    )

    result = read_project_memory(claude_home / "projects", "/home/matt/my-project")

    assert result is not None
    assert "Memory Index" in result.index_content
    assert len(result.topics) == 1
    assert result.topics[0].name == "user-context"
    assert result.topics[0].description == "Contesto utente"
    assert result.topics[0].metadata == {"type": "user"}
    assert "progetto scolastico" in result.topics[0].content


def test_read_project_memory_returns_none_when_no_memory_dir(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"

    result = read_project_memory(claude_home / "projects", "/home/matt/unknown-project")

    assert result is None


def test_read_project_memory_handles_missing_index_gracefully(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    memory_dir = make_memory_dir(claude_home, "/home/matt/my-project")
    (memory_dir / "topic.md").write_text("---\nname: topic\ndescription: d\n---\ncontent\n")

    result = read_project_memory(claude_home / "projects", "/home/matt/my-project")

    assert result is not None
    assert result.index_content == ""
    assert len(result.topics) == 1


def test_read_project_memory_skips_topic_file_without_frontmatter(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    memory_dir = make_memory_dir(claude_home, "/home/matt/my-project")
    (memory_dir / "MEMORY.md").write_text("# Memory Index\n")
    (memory_dir / "malformed.md").write_text("no frontmatter here\n")

    result = read_project_memory(claude_home / "projects", "/home/matt/my-project")

    assert result is not None
    assert result.topics == []


def test_read_project_memory_topic_modified_reflects_file_mtime(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    memory_dir = make_memory_dir(claude_home, "/home/matt/my-project")
    (memory_dir / "MEMORY.md").write_text("# Memory Index\n")
    topic_file = memory_dir / "topic.md"
    topic_file.write_text("---\nname: topic\ndescription: d\n---\ncontent\n")

    result = read_project_memory(claude_home / "projects", "/home/matt/my-project")

    assert result is not None
    assert result.topics[0].modified == topic_file.stat().st_mtime
