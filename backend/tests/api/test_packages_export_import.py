import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_claude_home_path,
    get_claude_json_path,
    get_control_plane_home,
    get_db_connection,
    get_home_path,
)
from app.db.connection import connect
from app.main import app
from tests.api.db_override import db_override

client = TestClient(app)


def make_skill_source(root: Path, name: str, description: str) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\n---\n")
    return skill_dir


def test_get_package_export_returns_sanitized_bundle(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    make_skill_source(claude_home / "skills", "deploy", "Deploy the app")
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_control_plane_home] = lambda: tmp_path / "control-plane-home"
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home
    app.dependency_overrides[get_home_path] = lambda: tmp_path

    client.post(
        "/packages",
        json={
            "id": "pkg-export",
            "name": "Pkg Export",
            "version": "1.0.0",
            "scope": "global",
            "nodes": [
                {"type": "skill", "name": "deploy", "library_item_id": "skill:user:deploy"},
                {
                    "type": "mcp",
                    "name": "obsidian",
                    "config": {"env": {"API_KEY": "sk-super-secret"}},
                },
            ],
        },
    )

    response = client.get("/packages/pkg-export/export")

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
    bundle = response.json()
    raw_text = json.dumps(bundle)
    assert "sk-super-secret" not in raw_text
    assert bundle["files"][".claude/skills/deploy/SKILL.md"]


def test_get_package_export_404_for_unknown_package(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_home_path] = lambda: tmp_path

    response = client.get("/packages/does-not-exist/export")

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 404


def test_post_packages_import_materializes_package_and_reports_missing_dependencies(
    tmp_path: Path,
) -> None:
    claude_home = tmp_path / "claude-home"
    claude_home.mkdir()
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_control_plane_home] = lambda: tmp_path / "control-plane-home"
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home
    app.dependency_overrides[get_claude_json_path] = lambda: tmp_path / "claude.json"

    bundle = {
        "id": "obsidian-refactor",
        "name": "Obsidian Refactor",
        "version": "1.0.0",
        "description": "Un pacchetto importato",
        "folder": None,
        "canvas_layout": {"nodes": [], "edges": []},
        "files": {
            ".claude/skills/deploy/SKILL.md": "---\nname: deploy\n---\n",
            ".mcp.json": json.dumps({"mcpServers": {"obsidian": {}}}),
        },
    }

    response = client.post(
        "/packages/import",
        json={"bundle": bundle, "id": "imported-pkg", "scope": "global"},
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 201
    body = response.json()
    assert body["package"]["id"] == "imported-pkg"
    assert body["missing_dependencies"]["missing_skills"] == ["deploy"]
    assert body["missing_dependencies"]["missing_mcp_servers"] == ["obsidian"]


def test_post_packages_import_no_missing_dependencies_when_present_locally(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    make_skill_source(claude_home / "skills", "deploy", "Deploy the app")
    claude_json_path = tmp_path / "claude.json"
    claude_json_path.write_text(json.dumps({"mcpServers": {"obsidian": {}}}))
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_control_plane_home] = lambda: tmp_path / "control-plane-home"
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home
    app.dependency_overrides[get_claude_json_path] = lambda: claude_json_path

    bundle = {
        "id": "obsidian-refactor",
        "name": "Obsidian Refactor",
        "version": "1.0.0",
        "description": "",
        "folder": None,
        "canvas_layout": {},
        "files": {
            ".claude/skills/deploy/SKILL.md": "---\nname: deploy\n---\n",
            ".mcp.json": json.dumps({"mcpServers": {"obsidian": {}}}),
        },
    }

    response = client.post(
        "/packages/import",
        json={"bundle": bundle, "id": "imported-pkg-2", "scope": "global"},
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 201
    body = response.json()
    assert body["missing_dependencies"] == {
        "missing_skills": [],
        "missing_agents": [],
        "missing_commands": [],
        "missing_mcp_servers": [],
    }


def test_post_packages_import_and_then_export_survive_malformed_mcp_servers_value(
    tmp_path: Path,
) -> None:
    """A .mcp.json whose "mcpServers" value isn't an object must not crash import
    (leaving a half-imported package that can never be exported again)."""
    claude_home = tmp_path / "claude-home"
    claude_home.mkdir()
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_control_plane_home] = lambda: tmp_path / "control-plane-home"
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home
    app.dependency_overrides[get_claude_json_path] = lambda: tmp_path / "claude.json"
    app.dependency_overrides[get_home_path] = lambda: tmp_path

    bundle = {
        "id": "weird-pkg",
        "name": "Weird",
        "version": "1.0.0",
        "description": "",
        "folder": None,
        "canvas_layout": {},
        "files": {".mcp.json": json.dumps({"mcpServers": ["not", "a", "dict"]})},
    }

    import_response = client.post(
        "/packages/import",
        json={"bundle": bundle, "id": "weird-pkg", "scope": "global"},
    )
    export_response = client.get("/packages/weird-pkg/export")

    app.dependency_overrides.clear()
    conn.close()

    assert import_response.status_code == 201
    assert import_response.json()["missing_dependencies"]["missing_mcp_servers"] == []
    assert export_response.status_code == 200


def test_export_then_import_round_trip_contains_no_sensitive_data(tmp_path: Path) -> None:
    """DoD Fase 6: un pacchetto esportato e re-importato su una cartella pulita
    non contiene alcun dato locale sensibile (chiave API, percorso assoluto locale)."""
    source_home = tmp_path / "source-home"
    claude_home = source_home / ".claude"
    make_skill_source(claude_home / "skills", "deploy", "Deploy the app")
    conn = connect(tmp_path / "index.sqlite")
    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_control_plane_home] = lambda: source_home / ".claude-control-plane"
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home
    app.dependency_overrides[get_home_path] = lambda: source_home

    client.post(
        "/packages",
        json={
            "id": "round-trip-pkg",
            "name": "Round Trip",
            "version": "1.0.0",
            "scope": "global",
            "nodes": [
                {"type": "skill", "name": "deploy", "library_item_id": "skill:user:deploy"},
                {
                    "type": "mcp",
                    "name": "obsidian",
                    "config": {
                        "command": str(source_home / "bin" / "obsidian-mcp"),
                        "env": {"API_KEY": "sk-round-trip-secret"},
                    },
                },
            ],
        },
    )
    export_response = client.get("/packages/round-trip-pkg/export")
    bundle = export_response.json()

    target_home = tmp_path / "target-home"
    target_claude_home = target_home / ".claude"
    target_claude_home.mkdir(parents=True)
    app.dependency_overrides[get_control_plane_home] = lambda: target_home / ".claude-control-plane"
    app.dependency_overrides[get_claude_home_path] = lambda: target_claude_home
    app.dependency_overrides[get_claude_json_path] = lambda: target_home / "claude.json"

    import_response = client.post(
        "/packages/import",
        json={"bundle": bundle, "id": "round-trip-pkg-imported", "scope": "global"},
    )

    app.dependency_overrides.clear()

    imported = (
        connect(tmp_path / "index.sqlite")
        .execute("SELECT content_path FROM packages WHERE id = ?", ("round-trip-pkg-imported",))
        .fetchone()
    )
    content_path = Path(imported["content_path"])
    on_disk_text = "\n".join(
        p.read_text() for p in content_path.rglob("*") if p.is_file() and p.name != "package.json"
    )
    conn.close()

    assert export_response.status_code == 200
    assert import_response.status_code == 201
    assert "sk-round-trip-secret" not in json.dumps(bundle)
    assert str(source_home) not in json.dumps(bundle)
    assert "sk-round-trip-secret" not in on_disk_text
    assert str(source_home) not in on_disk_text
