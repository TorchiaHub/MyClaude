import json
from pathlib import Path

import pytest

from app.db.connection import connect
from app.package_registry import (
    InvalidPackageIdentifierError,
    PackageNode,
    create_package,
    delete_package,
    get_package,
    list_packages,
    resolve_content_path,
)


def make_skill_source(root: Path, name: str, description: str) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\n---\n")
    return skill_dir


def test_resolve_content_path_for_global_scope(tmp_path: Path) -> None:
    result = resolve_content_path(tmp_path, scope="global", project_path=None, package_id="pkg-1")

    assert result == tmp_path / "global-packages" / "pkg-1"


def test_resolve_content_path_for_project_scope(tmp_path: Path) -> None:
    project_dir = tmp_path / "my-project"
    result = resolve_content_path(
        tmp_path, scope="project", project_path=str(project_dir), package_id="pkg-1"
    )

    assert result == project_dir / ".claude-control-plane" / "packages" / "pkg-1"


def test_create_package_materializes_skill_node_and_registers_in_db(tmp_path: Path) -> None:
    sources_root = tmp_path / "sources"
    skill_source = make_skill_source(sources_root, "deploy", "Deploy the app")
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    package = create_package(
        control_plane_home,
        conn,
        id="obsidian-refactor",
        name="Obsidian Refactor",
        version="1.0.0",
        scope="global",
        project_path=None,
        folder="Frontend",
        description="Refactor from Obsidian notes",
        nodes=[PackageNode(type="skill", name="deploy", source_path=str(skill_source))],
        canvas_layout={"nodes": [], "edges": []},
    )

    assert package.content_path.is_dir()
    materialized_skill = package.content_path / ".claude" / "skills" / "deploy" / "SKILL.md"
    assert materialized_skill.is_file()
    assert "Deploy the app" in materialized_skill.read_text()

    manifest = json.loads((package.content_path / "package.json").read_text())
    assert manifest["id"] == "obsidian-refactor"
    assert manifest["scope"] == "global"

    fetched = get_package(conn, "obsidian-refactor")
    assert fetched is not None
    assert fetched.name == "Obsidian Refactor"


def test_create_package_materializes_agent_and_command_nodes(tmp_path: Path) -> None:
    sources_root = tmp_path / "sources"
    sources_root.mkdir()
    agent_source = sources_root / "reviewer.md"
    agent_source.write_text("---\nname: reviewer\ndescription: Reviews code\n---\nBody.\n")
    command_source = sources_root / "deploy.md"
    command_source.write_text("---\ndescription: Deploy\n---\nDeploy now.\n")
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    package = create_package(
        control_plane_home,
        conn,
        id="pkg-2",
        name="Pkg 2",
        version="1.0.0",
        scope="global",
        project_path=None,
        folder=None,
        description="",
        nodes=[
            PackageNode(type="agent", name="reviewer", source_path=str(agent_source)),
            PackageNode(type="command", name="deploy", source_path=str(command_source)),
        ],
        canvas_layout={"nodes": [], "edges": []},
    )

    assert (package.content_path / ".claude" / "agents" / "reviewer.md").is_file()
    assert (package.content_path / ".claude" / "commands" / "deploy.md").is_file()


def test_create_package_materializes_mcp_node_into_mcp_json(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    package = create_package(
        control_plane_home,
        conn,
        id="pkg-3",
        name="Pkg 3",
        version="1.0.0",
        scope="global",
        project_path=None,
        folder=None,
        description="",
        nodes=[
            PackageNode(type="mcp", name="ollama", config={"type": "stdio", "command": "ollama"})
        ],
        canvas_layout={"nodes": [], "edges": []},
    )

    mcp_json = json.loads((package.content_path / ".mcp.json").read_text())
    assert mcp_json["mcpServers"]["ollama"]["command"] == "ollama"


def test_create_package_materializes_rule_and_prompt_nodes(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    package = create_package(
        control_plane_home,
        conn,
        id="pkg-4",
        name="Pkg 4",
        version="1.0.0",
        scope="global",
        project_path=None,
        folder=None,
        description="",
        nodes=[
            PackageNode(type="rule", name="my-rule", content="Always do X."),
            PackageNode(type="prompt", name="context", content="Remember Y."),
        ],
        canvas_layout={"nodes": [], "edges": []},
    )

    assert (package.content_path / ".claude" / "rules" / "my-rule.md").read_text() == "Always do X."
    assert "Remember Y." in (package.content_path / "CLAUDE.md").read_text()


def test_list_packages_returns_all_registered_packages(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")
    create_package(
        control_plane_home,
        conn,
        id="pkg-a",
        name="A",
        version="1.0.0",
        scope="global",
        project_path=None,
        folder=None,
        description="",
        nodes=[],
        canvas_layout={"nodes": [], "edges": []},
    )
    create_package(
        control_plane_home,
        conn,
        id="pkg-b",
        name="B",
        version="1.0.0",
        scope="global",
        project_path=None,
        folder=None,
        description="",
        nodes=[],
        canvas_layout={"nodes": [], "edges": []},
    )

    result = list_packages(conn)

    assert {p.id for p in result} == {"pkg-a", "pkg-b"}


def test_get_package_returns_none_when_not_found(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")

    result = get_package(conn, "does-not-exist")

    assert result is None


def test_delete_package_removes_content_and_db_row(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")
    package = create_package(
        control_plane_home,
        conn,
        id="pkg-delete",
        name="Delete me",
        version="1.0.0",
        scope="global",
        project_path=None,
        folder=None,
        description="",
        nodes=[],
        canvas_layout={"nodes": [], "edges": []},
    )

    delete_package(conn, "pkg-delete")

    assert not package.content_path.exists()
    assert get_package(conn, "pkg-delete") is None


def test_create_package_project_scope_stores_content_inside_project(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    project_dir = tmp_path / "my-project"
    conn = connect(tmp_path / "index.sqlite")

    package = create_package(
        control_plane_home,
        conn,
        id="pkg-proj",
        name="Project pkg",
        version="1.0.0",
        scope="project",
        project_path=str(project_dir),
        folder=None,
        description="",
        nodes=[],
        canvas_layout={"nodes": [], "edges": []},
    )

    assert package.content_path == (project_dir / ".claude-control-plane" / "packages" / "pkg-proj")


def test_create_package_rejects_path_traversal_in_id(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    with pytest.raises(InvalidPackageIdentifierError):
        create_package(
            control_plane_home,
            conn,
            id="../../../etc/evil",
            name="Evil",
            version="1.0.0",
            scope="global",
            project_path=None,
            folder=None,
            description="",
            nodes=[],
            canvas_layout={},
        )

    assert not (tmp_path / "etc" / "evil").exists()
    assert list_packages(conn) == []


def test_create_package_rejects_dotdot_id_that_looks_like_a_slug(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    with pytest.raises(InvalidPackageIdentifierError):
        create_package(
            control_plane_home,
            conn,
            id="..",
            name="Evil",
            version="1.0.0",
            scope="global",
            project_path=None,
            folder=None,
            description="",
            nodes=[],
            canvas_layout={},
        )


def test_create_package_rejects_path_traversal_in_node_name(tmp_path: Path) -> None:
    sources_root = tmp_path / "sources"
    sources_root.mkdir()
    agent_source = sources_root / "reviewer.md"
    agent_source.write_text("harmless")
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    with pytest.raises(InvalidPackageIdentifierError):
        create_package(
            control_plane_home,
            conn,
            id="pkg-safe",
            name="Safe",
            version="1.0.0",
            scope="global",
            project_path=None,
            folder=None,
            description="",
            nodes=[
                PackageNode(type="agent", name="../../../etc/evil", source_path=str(agent_source))
            ],
            canvas_layout={},
        )

    assert not (tmp_path / "etc" / "evil").exists()


def test_resolve_content_path_rejects_relative_project_path() -> None:
    with pytest.raises(InvalidPackageIdentifierError):
        resolve_content_path(
            Path("/control-plane-home"),
            scope="project",
            project_path="relative/path",
            package_id="pkg-1",
        )


def test_resolve_content_path_rejects_traversal_id() -> None:
    with pytest.raises(InvalidPackageIdentifierError):
        resolve_content_path(
            Path("/control-plane-home"),
            scope="global",
            project_path=None,
            package_id="../escape",
        )
