from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_claude_home_path, get_db_connection
from app.db.connection import connect
from app.main import app
from tests.api.db_override import db_override

client = TestClient(app)


def make_skill(claude_home: Path, name: str, description: str) -> None:
    skill_dir = claude_home / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\n---\n")


def test_get_library_returns_scanned_items_with_tags_and_bookmarks(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    make_skill(claude_home, "deploy", "Deploy the app")
    conn = connect(tmp_path / "index.sqlite")

    app.dependency_overrides[get_claude_home_path] = lambda: claude_home
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.get("/library")

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "deploy"
    assert body[0]["bookmarked"] is False
    assert body[0]["path"] == str(claude_home / "skills" / "deploy" / "SKILL.md")


def test_post_bookmark_sets_item_as_bookmarked(tmp_path: Path) -> None:
    claude_home = tmp_path / "claude-home"
    make_skill(claude_home, "deploy", "Deploy the app")
    conn = connect(tmp_path / "index.sqlite")

    app.dependency_overrides[get_claude_home_path] = lambda: claude_home
    app.dependency_overrides[get_db_connection] = db_override(conn)

    response = client.post(
        "/library/bookmark", json={"id": "skill:user:deploy", "bookmarked": True}
    )

    app.dependency_overrides.clear()
    conn.close()

    assert response.status_code == 200
    assert response.json()["bookmarked"] is True
