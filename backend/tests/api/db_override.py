import sqlite3
from collections.abc import Callable, Generator


def db_override(
    conn: sqlite3.Connection,
) -> Callable[[], Generator[sqlite3.Connection, None, None]]:
    def override() -> Generator[sqlite3.Connection, None, None]:
        yield conn

    return override
