import sqlite3


def add_tag(conn: sqlite3.Connection, item_id: str, tag: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO library_item_tags (item_id, tag) VALUES (?, ?)", (item_id, tag)
    )
    conn.commit()


def remove_tag(conn: sqlite3.Connection, item_id: str, tag: str) -> None:
    conn.execute("DELETE FROM library_item_tags WHERE item_id = ? AND tag = ?", (item_id, tag))
    conn.commit()


def get_tags(conn: sqlite3.Connection, item_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT tag FROM library_item_tags WHERE item_id = ? ORDER BY tag", (item_id,)
    ).fetchall()
    return [row["tag"] for row in rows]


def set_bookmark(conn: sqlite3.Connection, item_id: str, bookmarked: bool) -> None:
    if bookmarked:
        conn.execute("INSERT OR IGNORE INTO library_bookmarks (item_id) VALUES (?)", (item_id,))
    else:
        conn.execute("DELETE FROM library_bookmarks WHERE item_id = ?", (item_id,))
    conn.commit()


def is_bookmarked(conn: sqlite3.Connection, item_id: str) -> bool:
    row = conn.execute("SELECT 1 FROM library_bookmarks WHERE item_id = ?", (item_id,)).fetchone()
    return row is not None
