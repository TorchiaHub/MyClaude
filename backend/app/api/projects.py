import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_claude_json_path, get_db_connection
from app.project_discovery import list_projects, register_project

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    path: str


@router.get("")
def get_projects(
    claude_json_path: Path = Depends(get_claude_json_path),
    conn: sqlite3.Connection = Depends(get_db_connection),
) -> list[dict]:
    entries = list_projects(claude_json_path, conn)
    return [{"path": entry.path, "source": entry.source} for entry in entries]


@router.post("", status_code=201)
def post_project(
    body: ProjectCreate, conn: sqlite3.Connection = Depends(get_db_connection)
) -> dict:
    register_project(conn, Path(body.path))
    return {"path": body.path, "source": "manual"}
