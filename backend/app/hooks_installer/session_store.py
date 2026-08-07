import sqlite3


def record_session_start(
    conn: sqlite3.Connection, session_id: str, cwd: str, started_at: int
) -> None:
    conn.execute(
        """
        INSERT INTO session_started (session_id, cwd, started_at) VALUES (?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET cwd = excluded.cwd, started_at = excluded.started_at
        """,
        (session_id, cwd, started_at),
    )
    conn.commit()
