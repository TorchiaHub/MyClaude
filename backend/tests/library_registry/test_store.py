from pathlib import Path

from app.db.connection import connect
from app.library_registry.store import add_tag, get_tags, is_bookmarked, remove_tag, set_bookmark


def test_add_tag_and_get_tags(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")

    add_tag(conn, "skill:user:deploy", "infra")
    add_tag(conn, "skill:user:deploy", "ci")

    assert get_tags(conn, "skill:user:deploy") == ["ci", "infra"]


def test_add_tag_is_idempotent(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")

    add_tag(conn, "skill:user:deploy", "infra")
    add_tag(conn, "skill:user:deploy", "infra")

    assert get_tags(conn, "skill:user:deploy") == ["infra"]


def test_remove_tag(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    add_tag(conn, "skill:user:deploy", "infra")

    remove_tag(conn, "skill:user:deploy", "infra")

    assert get_tags(conn, "skill:user:deploy") == []


def test_get_tags_returns_empty_list_for_unknown_item(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")

    assert get_tags(conn, "skill:user:unknown") == []


def test_set_bookmark_true_then_false(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")

    set_bookmark(conn, "skill:user:deploy", True)
    assert is_bookmarked(conn, "skill:user:deploy") is True

    set_bookmark(conn, "skill:user:deploy", False)
    assert is_bookmarked(conn, "skill:user:deploy") is False


def test_is_bookmarked_defaults_to_false(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")

    assert is_bookmarked(conn, "skill:user:never-bookmarked") is False
