import json
from pathlib import Path

from app.activation_engine import (
    activate_package,
    deactivate_package,
    list_active_package_ids,
    preview_activation,
)
from app.db.connection import connect
from app.package_registry import PackageNode, create_package


def make_skill_source(root: Path, name: str, description: str) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\n---\n")
    return skill_dir


def make_test_package(
    tmp_path: Path,
    conn,
    *,
    package_id: str = "pkg-1",
    scope: str = "global",
    project_path: str | None = None,
    skill_description: str = "Deploy the app",
):
    sources_root = tmp_path / "sources" / package_id
    skill_source = make_skill_source(sources_root, "deploy", skill_description)
    control_plane_home = tmp_path / "control-plane-home"
    return create_package(
        control_plane_home,
        conn,
        id=package_id,
        name=package_id,
        version="1.0.0",
        scope=scope,
        project_path=project_path,
        folder=None,
        description="",
        nodes=[
            PackageNode(type="skill", name="deploy", source_path=str(skill_source)),
            PackageNode(type="mcp", name="ollama", config={"command": "ollama"}),
        ],
        canvas_layout={"nodes": [], "edges": []},
    )


def test_preview_activation_reports_create_for_new_file(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    package = make_test_package(tmp_path, conn)
    target_root = tmp_path / "claude-target"

    diffs = preview_activation(package, target_root)

    skill_diff = next(d for d in diffs if d.relative_path == ".claude/skills/deploy/SKILL.md")
    assert skill_diff.action == "create"


def test_preview_activation_reports_overwrite_conflict_for_different_existing_content(
    tmp_path: Path,
) -> None:
    conn = connect(tmp_path / "index.sqlite")
    package = make_test_package(tmp_path, conn)
    target_root = tmp_path / "claude-target"
    existing = target_root / "skills" / "deploy" / "SKILL.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("completely different content, never written by us")

    diffs = preview_activation(package, target_root)

    skill_diff = next(d for d in diffs if d.relative_path == ".claude/skills/deploy/SKILL.md")
    assert skill_diff.action == "overwrite_conflict"


def test_preview_activation_reports_overwrite_identical_when_content_matches(
    tmp_path: Path,
) -> None:
    conn = connect(tmp_path / "index.sqlite")
    package = make_test_package(tmp_path, conn)
    target_root = tmp_path / "claude-target"
    source_content = (
        package.content_path / ".claude" / "skills" / "deploy" / "SKILL.md"
    ).read_bytes()
    existing = target_root / "skills" / "deploy" / "SKILL.md"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(source_content)

    diffs = preview_activation(package, target_root)

    skill_diff = next(d for d in diffs if d.relative_path == ".claude/skills/deploy/SKILL.md")
    assert skill_diff.action == "overwrite_identical"


def test_activate_package_writes_files_and_manifest(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    package = make_test_package(tmp_path, conn)
    target_root = tmp_path / "claude-target"
    mcp_target = tmp_path / "claude-target" / ".mcp.json"

    activate_package(conn, package, target_root, mcp_target)

    written_skill = target_root / "skills" / "deploy" / "SKILL.md"
    assert written_skill.is_file()
    assert "Deploy the app" in written_skill.read_text()

    mcp_data = json.loads(mcp_target.read_text())
    assert mcp_data["mcpServers"]["ollama"]["command"] == "ollama"

    manifest_rows = conn.execute(
        "SELECT file_path FROM written_files WHERE package_id = ?", (package.id,)
    ).fetchall()
    manifest_paths = {row["file_path"] for row in manifest_rows}
    assert ".claude/skills/deploy/SKILL.md" in manifest_paths
    assert ".mcp.json::ollama" in manifest_paths

    log_rows = conn.execute(
        "SELECT action FROM activation_log WHERE package_id = ?", (package.id,)
    ).fetchall()
    assert [row["action"] for row in log_rows] == ["activate"]


def test_deactivate_package_removes_unmodified_files(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    package = make_test_package(tmp_path, conn)
    target_root = tmp_path / "claude-target"
    mcp_target = tmp_path / "claude-target" / ".mcp.json"
    activate_package(conn, package, target_root, mcp_target)

    result = deactivate_package(conn, package, target_root, mcp_target)

    assert not (target_root / "skills" / "deploy" / "SKILL.md").exists()
    assert "ollama" not in json.loads(mcp_target.read_text()).get("mcpServers", {})
    assert ".claude/skills/deploy/SKILL.md" in result.removed
    assert result.preserved == []

    manifest_rows = conn.execute(
        "SELECT * FROM written_files WHERE package_id = ?", (package.id,)
    ).fetchall()
    assert manifest_rows == []


def test_deactivate_package_preserves_manually_modified_file(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    package = make_test_package(tmp_path, conn)
    target_root = tmp_path / "claude-target"
    mcp_target = tmp_path / "claude-target" / ".mcp.json"
    activate_package(conn, package, target_root, mcp_target)

    written_skill = target_root / "skills" / "deploy" / "SKILL.md"
    written_skill.write_text("the user manually edited this after activation")

    result = deactivate_package(conn, package, target_root, mcp_target)

    assert written_skill.is_file()
    assert written_skill.read_text() == "the user manually edited this after activation"
    assert ".claude/skills/deploy/SKILL.md" in result.preserved
    assert ".claude/skills/deploy/SKILL.md" not in result.removed


def test_deactivate_package_preserves_manually_modified_mcp_server(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    package = make_test_package(tmp_path, conn)
    target_root = tmp_path / "claude-target"
    mcp_target = tmp_path / "claude-target" / ".mcp.json"
    activate_package(conn, package, target_root, mcp_target)

    mcp_data = json.loads(mcp_target.read_text())
    mcp_data["mcpServers"]["ollama"] = {"command": "ollama-modified-by-user"}
    mcp_target.write_text(json.dumps(mcp_data))

    result = deactivate_package(conn, package, target_root, mcp_target)

    remaining = json.loads(mcp_target.read_text())
    assert remaining["mcpServers"]["ollama"]["command"] == "ollama-modified-by-user"
    assert ".mcp.json::ollama" in result.preserved


def test_activating_global_package_deactivates_previous_global_package(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    first = make_test_package(tmp_path, conn, package_id="pkg-first", skill_description="First")
    second = make_test_package(tmp_path, conn, package_id="pkg-second", skill_description="Second")
    target_root = tmp_path / "claude-target"
    mcp_target = tmp_path / "claude-target" / ".mcp.json"

    activate_package(conn, first, target_root, mcp_target)
    activate_package(conn, second, target_root, mcp_target)

    assert list_active_package_ids(conn, project_path=None) == ["pkg-second"]
    first_manifest = conn.execute(
        "SELECT * FROM written_files WHERE package_id = ?", (first.id,)
    ).fetchall()
    assert first_manifest == []


def test_activating_project_packages_allows_multiple_simultaneously(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    project_path = str(tmp_path / "my-project")
    first = make_test_package(
        tmp_path,
        conn,
        package_id="pkg-a",
        scope="project",
        project_path=project_path,
        skill_description="A",
    )
    second = make_test_package(
        tmp_path,
        conn,
        package_id="pkg-b",
        scope="project",
        project_path=project_path,
        skill_description="B",
    )
    target_root = Path(project_path)
    mcp_target = Path(project_path) / ".mcp.json"

    activate_package(conn, first, target_root, mcp_target)
    activate_package(conn, second, target_root, mcp_target)

    assert set(list_active_package_ids(conn, project_path=project_path)) == {"pkg-a", "pkg-b"}


def test_activate_package_project_scope_keeps_claude_prefix_in_target_path(
    tmp_path: Path,
) -> None:
    conn = connect(tmp_path / "index.sqlite")
    project_path = str(tmp_path / "my-project")
    package = make_test_package(tmp_path, conn, scope="project", project_path=project_path)
    target_root = Path(project_path)
    mcp_target = Path(project_path) / ".mcp.json"

    activate_package(conn, package, target_root, mcp_target)

    assert (target_root / ".claude" / "skills" / "deploy" / "SKILL.md").is_file()
