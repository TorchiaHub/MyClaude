from pathlib import Path

from app.db.connection import connect
from app.hooks_installer.session_store import record_session_start


def test_record_session_start_inserts_row(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")

    record_session_start(conn, "sess-1", "/home/matt/my-project", 1000)

    row = conn.execute(
        "SELECT cwd, started_at FROM session_started WHERE session_id = ?", ("sess-1",)
    ).fetchone()
    assert row["cwd"] == "/home/matt/my-project"
    assert row["started_at"] == 1000


def test_record_session_start_upserts_on_resume(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    record_session_start(conn, "sess-1", "/home/matt/my-project", 1000)

    record_session_start(conn, "sess-1", "/home/matt/my-project", 2000)

    rows = conn.execute(
        "SELECT * FROM session_started WHERE session_id = ?", ("sess-1",)
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["started_at"] == 2000
