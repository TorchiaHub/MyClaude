from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_claude_home_path
from app.main import app

client = TestClient(app)


def test_get_tree_lists_root_children(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("hello")
    (tmp_path / "skills").mkdir()
    app.dependency_overrides[get_claude_home_path] = lambda: tmp_path

    response = client.get("/claude-home/tree", params={"path": ""})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    names = {entry["name"] for entry in response.json()}
    assert names == {"CLAUDE.md", "skills"}


def test_get_tree_rejects_path_traversal(tmp_path: Path) -> None:
    app.dependency_overrides[get_claude_home_path] = lambda: tmp_path

    response = client.get("/claude-home/tree", params={"path": "../../etc"})

    app.dependency_overrides.clear()

    assert response.status_code == 400


def test_get_file_returns_content(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# Hello")
    app.dependency_overrides[get_claude_home_path] = lambda: tmp_path

    response = client.get("/claude-home/file", params={"path": "CLAUDE.md"})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["content"] == "# Hello"


def test_get_file_rejects_path_traversal(tmp_path: Path) -> None:
    app.dependency_overrides[get_claude_home_path] = lambda: tmp_path

    response = client.get("/claude-home/file", params={"path": "../../../etc/passwd"})

    app.dependency_overrides.clear()

    assert response.status_code == 400


def test_patch_rename_renames_entry(tmp_path: Path) -> None:
    (tmp_path / "old.md").write_text("content")
    app.dependency_overrides[get_claude_home_path] = lambda: tmp_path

    response = client.patch("/claude-home/rename", json={"path": "old.md", "new_name": "new.md"})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert (tmp_path / "new.md").exists()


def test_patch_rename_rejects_root(tmp_path: Path) -> None:
    app.dependency_overrides[get_claude_home_path] = lambda: tmp_path

    response = client.patch("/claude-home/rename", json={"path": "", "new_name": "x"})

    app.dependency_overrides.clear()

    assert response.status_code == 400


def test_delete_entry_removes_file(tmp_path: Path) -> None:
    (tmp_path / "gone.md").write_text("bye")
    app.dependency_overrides[get_claude_home_path] = lambda: tmp_path

    response = client.request("DELETE", "/claude-home/entry", params={"path": "gone.md"})

    app.dependency_overrides.clear()

    assert response.status_code == 204
    assert not (tmp_path / "gone.md").exists()


def test_delete_entry_rejects_root(tmp_path: Path) -> None:
    app.dependency_overrides[get_claude_home_path] = lambda: tmp_path

    response = client.request("DELETE", "/claude-home/entry", params={"path": ""})

    app.dependency_overrides.clear()

    assert response.status_code == 400


def test_patch_move_moves_entry(tmp_path: Path) -> None:
    (tmp_path / "loose.md").write_text("content")
    (tmp_path / "archive").mkdir()
    app.dependency_overrides[get_claude_home_path] = lambda: tmp_path

    response = client.patch(
        "/claude-home/move",
        json={"path": "loose.md", "new_path": "archive/loose.md"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert (tmp_path / "archive" / "loose.md").exists()


def test_get_graph_returns_nodes_and_edges(tmp_path: Path) -> None:
    (tmp_path / "skills" / "deploy").mkdir(parents=True)
    (tmp_path / "skills" / "deploy" / "SKILL.md").write_text("---\nname: deploy\n---\n")
    app.dependency_overrides[get_claude_home_path] = lambda: tmp_path

    response = client.get("/claude-home/graph")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert any(n["id"] == "file:CLAUDE.md" for n in body["nodes"])
    assert any(n["label"] == "deploy" for n in body["nodes"])
    assert "edges" in body


def test_patch_move_rejects_destination_traversal(tmp_path: Path) -> None:
    (tmp_path / "loose.md").write_text("content")
    app.dependency_overrides[get_claude_home_path] = lambda: tmp_path

    response = client.patch(
        "/claude-home/move",
        json={"path": "loose.md", "new_path": "../escaped.md"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
