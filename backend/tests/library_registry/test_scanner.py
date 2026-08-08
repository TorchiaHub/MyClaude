from pathlib import Path

from app.library_registry.scanner import scan_library


def make_skill(root: Path, relative_dir: str, name: str, description: str) -> None:
    skill_dir = root / "skills" / relative_dir
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\ntags: [a, b]\n---\nBody.\n"
    )


def make_markdown_resource(root: Path, subdir: str, filename: str, description: str) -> None:
    resource_dir = root / subdir
    resource_dir.mkdir(parents=True, exist_ok=True)
    (resource_dir / filename).write_text(f"---\ndescription: {description}\n---\nBody.\n")


def test_scan_library_finds_user_level_skills(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    make_skill(claude_home, "deploy", "deploy", "Deploy the app")

    items = scan_library(claude_home, None)

    skill_items = [item for item in items if item.resource_type == "skill"]
    assert len(skill_items) == 1
    assert skill_items[0].name == "deploy"
    assert skill_items[0].description == "Deploy the app"
    assert skill_items[0].scope == "user"
    assert skill_items[0].tags == ["a", "b"]


def test_scan_library_computes_folder_for_nested_skill(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    make_skill(claude_home, "apps/web/deploy", "deploy", "Deploy the web app")

    items = scan_library(claude_home, None)

    skill_items = [item for item in items if item.resource_type == "skill"]
    assert skill_items[0].folder == "apps/web"


def test_scan_library_finds_agents_commands_and_output_styles(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    make_markdown_resource(claude_home, "agents", "code-reviewer.md", "Reviews code")
    make_markdown_resource(claude_home, "commands", "deploy.md", "Deploy command")
    make_markdown_resource(claude_home, "output-styles", "concise.md", "Concise output")

    items = scan_library(claude_home, None)

    by_type = {item.resource_type: item for item in items}
    assert by_type["agent"].name == "code-reviewer"
    assert by_type["agent"].description == "Reviews code"
    assert by_type["command"].name == "deploy"
    assert by_type["output_style"].name == "concise"


def test_scan_library_includes_project_scope_when_project_dir_given(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    project_dir = tmp_path / "my-project"
    make_skill(claude_home, "personal-skill", "personal-skill", "A personal skill")
    make_skill(project_dir / ".claude", "project-skill", "project-skill", "A project skill")

    items = scan_library(claude_home, project_dir)

    scopes = {item.scope for item in items}
    assert scopes == {"user", "project"}


def test_scan_library_returns_empty_list_when_no_directories_exist(tmp_path: Path) -> None:
    items = scan_library(tmp_path / "does-not-exist", None)

    assert items == []


def test_scan_library_item_id_is_stable_and_unique(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    make_skill(claude_home, "deploy", "deploy", "Deploy the app")

    first = scan_library(claude_home, None)
    second = scan_library(claude_home, None)

    assert first[0].id == second[0].id
