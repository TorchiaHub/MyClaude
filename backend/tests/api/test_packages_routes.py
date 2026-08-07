import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_claude_home_path,
    get_claude_json_path,
    get_control_plane_home,
    get_db_connection,
)
from app.main import app
from tests.api.db_override import db_override

client = TestClient(app)


def make_skill_source(root: Path, name: str, description: str) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\n---\n")
    return skill_dir


def test_post_packages_creates_package(tmp_path: Path) -> None:
    from app.db.connection import connect

    claude_home = tmp_path / "claude-home"
    make_skill_source(claude_home / "skills", "deploy", "Deploy the app")
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_control_plane_home] = lambda: tmp_path / "control-plane-home"
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.post(
        "/packages",
        json={
            "id": "pkg-1",
            "name": "Pkg 1",
            "version": "1.0.0",
            "scope": "global",
            "nodes": [{"type": "skill", "name": "deploy", "library_item_id": "skill:user:deploy"}],
        },
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "pkg-1"
    assert body["scope"] == "global"


def test_post_packages_rejects_unknown_library_item_id(tmp_path: Path) -> None:
    from app.db.connection import connect

    claude_home = tmp_path / "claude-home"
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_control_plane_home] = lambda: tmp_path / "control-plane-home"
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.post(
        "/packages",
        json={
            "id": "pkg-ghost",
            "name": "Ghost",
            "version": "1.0.0",
            "scope": "global",
            "nodes": [
                {"type": "skill", "name": "evil", "library_item_id": "skill:user:does-not-exist"}
            ],
        },
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 400


def test_post_packages_ignores_raw_source_path_from_client(tmp_path: Path) -> None:
    """A client cannot smuggle an arbitrary filesystem path in as `source_path`
    (the old, removed field) to make create_package copy files it shouldn't."""
    from app.db.connection import connect

    claude_home = tmp_path / "claude-home"
    secret_dir = tmp_path / "secret"
    secret_dir.mkdir()
    (secret_dir / "id_rsa").write_text("not a real key, but pretend this is sensitive")
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_control_plane_home] = lambda: tmp_path / "control-plane-home"
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.post(
        "/packages",
        json={
            "id": "pkg-attack",
            "name": "Attack",
            "version": "1.0.0",
            "scope": "global",
            "nodes": [
                {
                    "type": "skill",
                    "name": "evil",
                    "source_path": str(secret_dir),
                    "library_item_id": "skill:user:does-not-exist",
                }
            ],
        },
    )

    app.dependency_overrides.clear()
    conn.close()

    # The unknown library_item_id is rejected — the smuggled source_path is
    # never consulted, so nothing gets copied.
    assert response.status_code == 400
    assert not (tmp_path / "control-plane-home" / "global-packages" / "pkg-attack").exists()


def test_post_packages_rejects_path_traversal_id(tmp_path: Path) -> None:
    from app.db.connection import connect

    conn = connect(tmp_path / "index.sqlite")
    control_plane_home = tmp_path / "control-plane-home"
    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_control_plane_home] = lambda: control_plane_home

    response = client.post(
        "/packages",
        json={
            "id": "../../etc/evil",
            "name": "Evil",
            "version": "1.0.0",
            "scope": "global",
            "nodes": [],
        },
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 400
    assert not (tmp_path / "etc" / "evil").exists()


def test_get_packages_lists_created_packages(tmp_path: Path) -> None:
    from app.db.connection import connect
    from app.package_registry import create_package

    conn = connect(tmp_path / "index.sqlite")
    control_plane_home = tmp_path / "control-plane-home"
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
        canvas_layout={},
    )
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.get("/packages")

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == ["pkg-a"]


def test_get_package_by_id_returns_404_when_missing(tmp_path: Path) -> None:
    from app.db.connection import connect

    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.get("/packages/missing")

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 404


def test_delete_package_removes_it(tmp_path: Path) -> None:
    from app.db.connection import connect
    from app.package_registry import create_package

    conn = connect(tmp_path / "index.sqlite")
    control_plane_home = tmp_path / "control-plane-home"
    create_package(
        control_plane_home,
        conn,
        id="pkg-del",
        name="Del",
        version="1.0.0",
        scope="global",
        project_path=None,
        folder=None,
        description="",
        nodes=[],
        canvas_layout={},
    )
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.delete("/packages/pkg-del")

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 204


def test_activate_package_writes_files_to_global_claude_home(tmp_path: Path) -> None:
    from app.db.connection import connect
    from app.package_registry import PackageNode, create_package

    skill_source = make_skill_source(tmp_path / "sources", "deploy", "Deploy the app")
    conn = connect(tmp_path / "index.sqlite")
    control_plane_home = tmp_path / "control-plane-home"
    claude_home = tmp_path / "claude-home"
    claude_json = tmp_path / ".claude.json"
    claude_json.write_text(json.dumps({}))

    package = create_package(
        control_plane_home,
        conn,
        id="pkg-activate",
        name="Activate",
        version="1.0.0",
        scope="global",
        project_path=None,
        folder=None,
        description="",
        nodes=[PackageNode(type="skill", name="deploy", source_path=str(skill_source))],
        canvas_layout={},
    )
    assert package is not None

    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home
    app.dependency_overrides[get_claude_json_path] = lambda: claude_json

    response = client.post("/packages/pkg-activate/activate")

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
    assert (claude_home / "skills" / "deploy" / "SKILL.md").is_file()


def test_preview_package_activation_returns_diffs(tmp_path: Path) -> None:
    from app.db.connection import connect
    from app.package_registry import PackageNode, create_package

    skill_source = make_skill_source(tmp_path / "sources", "deploy", "Deploy the app")
    conn = connect(tmp_path / "index.sqlite")
    control_plane_home = tmp_path / "control-plane-home"
    claude_home = tmp_path / "claude-home"

    create_package(
        control_plane_home,
        conn,
        id="pkg-preview",
        name="Preview",
        version="1.0.0",
        scope="global",
        project_path=None,
        folder=None,
        description="",
        nodes=[PackageNode(type="skill", name="deploy", source_path=str(skill_source))],
        canvas_layout={},
    )

    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home

    response = client.get("/packages/pkg-preview/preview-activation")

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
    diffs = response.json()
    assert any(d["relative_path"] == ".claude/skills/deploy/SKILL.md" for d in diffs)
    assert all(d["action"] == "create" for d in diffs)


def test_deactivate_package_removes_written_files(tmp_path: Path) -> None:
    from app.db.connection import connect
    from app.package_registry import PackageNode, create_package

    skill_source = make_skill_source(tmp_path / "sources", "deploy", "Deploy the app")
    conn = connect(tmp_path / "index.sqlite")
    control_plane_home = tmp_path / "control-plane-home"
    claude_home = tmp_path / "claude-home"
    claude_json = tmp_path / ".claude.json"
    claude_json.write_text(json.dumps({}))

    create_package(
        control_plane_home,
        conn,
        id="pkg-deact",
        name="Deact",
        version="1.0.0",
        scope="global",
        project_path=None,
        folder=None,
        description="",
        nodes=[PackageNode(type="skill", name="deploy", source_path=str(skill_source))],
        canvas_layout={},
    )

    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home
    app.dependency_overrides[get_claude_json_path] = lambda: claude_json

    client.post("/packages/pkg-deact/activate")
    response = client.post("/packages/pkg-deact/deactivate")

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
    assert not (claude_home / "skills" / "deploy" / "SKILL.md").exists()
    assert response.json()["removed"] == [".claude/skills/deploy/SKILL.md"]
