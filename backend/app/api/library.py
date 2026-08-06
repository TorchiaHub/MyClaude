import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.dependencies import get_claude_home_path, get_db_connection
from app.library_registry import get_tags, is_bookmarked, scan_library, set_bookmark

router = APIRouter(prefix="/library", tags=["library"])


class BookmarkUpdate(BaseModel):
    id: str
    bookmarked: bool


@router.get("")
def get_library(
    project_path: str | None = Query(default=None),
    claude_home: Path = Depends(get_claude_home_path),
    conn: sqlite3.Connection = Depends(get_db_connection),
) -> list[dict]:
    project_dir = Path(project_path) if project_path else None
    items = scan_library(claude_home, project_dir)
    return [
        {
            "id": item.id,
            "resource_type": item.resource_type,
            "scope": item.scope,
            "name": item.name,
            "description": item.description,
            "folder": item.folder,
            "tags": sorted(set(item.tags) | set(get_tags(conn, item.id))),
            "bookmarked": is_bookmarked(conn, item.id),
        }
        for item in items
    ]


@router.post("/bookmark")
def post_bookmark(
    body: BookmarkUpdate, conn: sqlite3.Connection = Depends(get_db_connection)
) -> dict:
    set_bookmark(conn, body.id, body.bookmarked)
    return {"id": body.id, "bookmarked": body.bookmarked}
