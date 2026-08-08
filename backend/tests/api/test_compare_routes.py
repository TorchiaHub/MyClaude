import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_claude_home_path, get_claude_json_path, get_db_connection
from app.db.connection import connect
from app.main import app
from app.package_registry import create_package
from app.telemetry_reader.project_paths import encode_project_path
from tests.api.db_override import db_override

client = TestClient(app)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def make_package(conn, control_plane_home: Path, package_id: str, canvas_nodes: list[dict]) -> None:
    create_package(
        control_plane_home,
        conn,
        id=package_id,
        name=package_id,
        version="1.0.0",
        scope="global",
        project_path=None,
        folder=None,
        description="",
        nodes=[],
        canvas_layout={"nodes": canvas_nodes, "edges": []},
    )


def node(node_type: str, name: str) -> dict:
    return {"data": {"nodeType": node_type, "name": name}}


def test_compare_static_mode_returns_diff(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    control_plane_home = tmp_path / "control-plane-home"
    make_package(conn, control_plane_home, "pkg-a", [node("skill", "deploy")])
    make_package(conn, control_plane_home, "pkg-b", [node("skill", "other")])
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.get(
        "/packages/compare", params={"mode": "static", "a": "pkg-a", "b": "pkg-b"}
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
    body = response.json()
    assert body["static_diff"]["by_type"]["skill"]["only_in_a"] == ["deploy"]
    assert body["static_diff"]["by_type"]["skill"]["only_in_b"] == ["other"]
    assert body["static_diff"]["is_identical"] is False


def test_compare_static_mode_returns_404_when_package_missing(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    control_plane_home = tmp_path / "control-plane-home"
    make_package(conn, control_plane_home, "pkg-a", [])
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.get(
        "/packages/compare", params={"mode": "static", "a": "pkg-a", "b": "does-not-exist"}
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 404


def test_compare_isolated_mode_returns_diff_and_per_package_telemetry(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    control_plane_home = tmp_path / "control-plane-home"
    claude_home = tmp_path / "claude-home"
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {}})
    project_path = "/proj"

    make_package(conn, control_plane_home, "pkg-a", [node("skill", "deploy")])
    make_package(conn, control_plane_home, "pkg-b", [node("skill", "other")])
    conn.execute(
        "INSERT INTO activation_log (package_id, project_path, action, occurred_at) VALUES (?, ?, 'activate', ?)",
        ("pkg-a", project_path, 1000),
    )
    conn.commit()

    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home
    app.dependency_overrides[get_claude_json_path] = lambda: claude_json

    response = client.get(
        "/packages/compare",
        params={"mode": "isolated", "a": "pkg-a", "b": "pkg-b", "project_path": project_path},
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
    body = response.json()
    assert body["static_diff"]["is_identical"] is False
    assert body["isolated"]["a"]["package_id"] == "pkg-a"
    assert len(body["isolated"]["a"]["windows"]) == 1
    assert body["isolated"]["b"]["windows"] == []


def test_compare_combination_mode_returns_two_period_summaries(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    claude_home = tmp_path / "claude-home"
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {}})
    project_path = "/proj"

    conn.execute(
        "INSERT INTO activation_log (package_id, project_path, action, occurred_at) VALUES (?, ?, 'activate', ?)",
        ("pkg-obsidian", project_path, 1000),
    )
    conn.commit()

    project_dir = claude_home / "projects" / encode_project_path(project_path)
    project_dir.mkdir(parents=True)
    (project_dir / "s.jsonl").write_text(
        json.dumps(
            {
                "type": "assistant",
                "timestamp": "2026-01-15T00:00:00Z",
                "message": {
                    "model": "claude-sonnet-5",
                    "usage": {"input_tokens": 5, "output_tokens": 5},
                },
            }
        )
        + "\n"
    )

    app.dependency_overrides[get_db_connection] = db_override(conn)
    app.dependency_overrides[get_claude_home_path] = lambda: claude_home
    app.dependency_overrides[get_claude_json_path] = lambda: claude_json

    response = client.get(
        "/packages/compare",
        params={
            "mode": "combination",
            "project_path": project_path,
            "since_a": "2026-01-01T00:00:00Z",
            "until_a": "2026-01-31T00:00:00Z",
            "since_b": "2026-02-01T00:00:00Z",
            "until_b": "2026-02-28T00:00:00Z",
        },
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
    body = response.json()
    assert body["combination"]["a"]["active_package_ids"] == ["pkg-obsidian"]
    assert body["combination"]["a"]["telemetry"]["turn_count"] == 1
    assert body["combination"]["b"]["telemetry"]["turn_count"] == 0


def test_compare_requires_project_path_for_isolated_mode(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    control_plane_home = tmp_path / "control-plane-home"
    make_package(conn, control_plane_home, "pkg-a", [])
    make_package(conn, control_plane_home, "pkg-b", [])
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.get(
        "/packages/compare", params={"mode": "isolated", "a": "pkg-a", "b": "pkg-b"}
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 400
