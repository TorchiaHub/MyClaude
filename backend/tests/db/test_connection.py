from pathlib import Path

from app.db.connection import connect


def test_connect_creates_parent_directory_and_file(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "index.sqlite"

    conn = connect(db_path)
    conn.close()

    assert db_path.is_file()


def test_connect_initializes_schema_tables(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")

    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    conn.close()

    assert {
        "library_item_tags",
        "library_bookmarks",
        "registered_projects",
        "packages",
        "activation_log",
        "written_files",
        "session_started",
    } <= tables


def test_connect_is_idempotent_across_calls(tmp_path: Path) -> None:
    db_path = tmp_path / "index.sqlite"

    connect(db_path).close()
    conn = connect(db_path)
    conn.close()

    assert db_path.is_file()
