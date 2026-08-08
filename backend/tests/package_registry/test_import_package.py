from pathlib import Path

import pytest

from app.db.connection import connect
from app.package_registry import InvalidPackageIdentifierError, get_package, import_package


def _bundle(**overrides) -> dict:
    base = {
        "id": "obsidian-refactor",
        "name": "Obsidian Refactor",
        "version": "1.0.0",
        "scope": "global",
        "description": "Refactor from Obsidian notes",
        "folder": "Frontend",
        "canvas_layout": {"nodes": [], "edges": []},
        "files": {
            ".claude/skills/deploy/SKILL.md": "---\nname: deploy\n---\nDeploy content",
            ".claude/rules/style.md": "Usa 4 spazi.",
        },
    }
    base.update(overrides)
    return base


def test_import_package_materializes_bundle_files_and_registers_in_db(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    package = import_package(
        control_plane_home,
        conn,
        bundle=_bundle(),
        id="imported-pkg",
        scope="global",
        project_path=None,
        folder=None,
    )

    assert (package.content_path / ".claude" / "skills" / "deploy" / "SKILL.md").is_file()
    assert (package.content_path / ".claude" / "rules" / "style.md").read_text() == "Usa 4 spazi."
    assert get_package(conn, "imported-pkg") is not None


def test_import_package_uses_bundle_metadata_for_name_version_description(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    package = import_package(
        control_plane_home,
        conn,
        bundle=_bundle(),
        id="imported-pkg",
        scope="global",
        project_path=None,
        folder=None,
    )

    assert package.name == "Obsidian Refactor"
    assert package.version == "1.0.0"
    assert package.description == "Refactor from Obsidian notes"


def test_import_package_lets_caller_override_scope_and_folder(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    project_dir = tmp_path / "my-project"
    conn = connect(tmp_path / "index.sqlite")

    package = import_package(
        control_plane_home,
        conn,
        bundle=_bundle(),
        id="imported-pkg",
        scope="project",
        project_path=str(project_dir),
        folder="Backend",
    )

    assert package.scope == "project"
    assert package.folder == "Backend"
    assert (
        package.content_path == project_dir / ".claude-control-plane" / "packages" / "imported-pkg"
    )


def test_import_package_rejects_path_traversal_in_bundle_file_path(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    with pytest.raises(InvalidPackageIdentifierError):
        import_package(
            control_plane_home,
            conn,
            bundle=_bundle(files={"../../etc/passwd": "pwned"}),
            id="imported-pkg",
            scope="global",
            project_path=None,
            folder=None,
        )


def test_import_package_rejects_absolute_bundle_file_path(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    with pytest.raises(InvalidPackageIdentifierError):
        import_package(
            control_plane_home,
            conn,
            bundle=_bundle(files={"/etc/passwd": "pwned"}),
            id="imported-pkg",
            scope="global",
            project_path=None,
            folder=None,
        )


def test_import_package_rejects_unsafe_id(tmp_path: Path) -> None:
    control_plane_home = tmp_path / "control-plane-home"
    conn = connect(tmp_path / "index.sqlite")

    with pytest.raises(InvalidPackageIdentifierError):
        import_package(
            control_plane_home,
            conn,
            bundle=_bundle(),
            id="../escape",
            scope="global",
            project_path=None,
            folder=None,
        )
