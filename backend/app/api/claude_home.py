from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.dependencies import get_claude_home_path
from app.claude_home_graph import build_claude_home_graph
from app.home_browser import (
    PathEscapesRootError,
    RootEntryError,
    delete_entry,
    list_directory,
    move_entry,
    read_file_preview,
    rename_entry,
)

router = APIRouter(prefix="/claude-home", tags=["claude-home"])

MAX_PREVIEW_BYTES = 200_000


class RenameRequest(BaseModel):
    path: str
    new_name: str


class MoveRequest(BaseModel):
    path: str
    new_path: str


@router.get("/graph")
def get_graph(claude_home: Path = Depends(get_claude_home_path)) -> dict:
    graph = build_claude_home_graph(claude_home)
    return {
        "nodes": [{"id": n.id, "type": n.type, "label": n.label} for n in graph.nodes],
        "edges": [{"source": e.source, "target": e.target, "kind": e.kind} for e in graph.edges],
    }


@router.get("/tree")
def get_tree(
    path: str = Query(default=""),
    claude_home: Path = Depends(get_claude_home_path),
) -> list[dict]:
    try:
        entries = list_directory(claude_home, path)
    except PathEscapesRootError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [{"name": e.name, "is_dir": e.is_dir, "size": e.size} for e in entries]


@router.get("/file")
def get_file(
    path: str = Query(...),
    claude_home: Path = Depends(get_claude_home_path),
) -> dict:
    try:
        content = read_file_preview(claude_home, path, max_bytes=MAX_PREVIEW_BYTES)
    except PathEscapesRootError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"content": content}


@router.patch("/rename")
def patch_rename(
    body: RenameRequest,
    claude_home: Path = Depends(get_claude_home_path),
) -> dict:
    try:
        destination = rename_entry(claude_home, body.path, body.new_name)
    except (PathEscapesRootError, RootEntryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"path": str(destination.relative_to(claude_home.resolve()))}


@router.delete("/entry", status_code=204)
def delete_entry_route(
    path: str = Query(...),
    claude_home: Path = Depends(get_claude_home_path),
) -> None:
    try:
        delete_entry(claude_home, path)
    except (PathEscapesRootError, RootEntryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/move")
def patch_move(
    body: MoveRequest,
    claude_home: Path = Depends(get_claude_home_path),
) -> dict:
    try:
        destination = move_entry(claude_home, body.path, body.new_path)
    except (PathEscapesRootError, RootEntryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"path": str(destination.relative_to(claude_home.resolve()))}
