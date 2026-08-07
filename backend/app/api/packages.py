import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.activation_engine import activate_package, deactivate_package, preview_activation
from app.api.dependencies import (
    get_claude_home_path,
    get_claude_json_path,
    get_control_plane_home,
    get_db_connection,
)
from app.library_registry import scan_library
from app.package_registry import (
    InvalidPackageIdentifierError,
    Package,
    PackageNode,
    create_package,
    delete_package,
    get_package,
)
from app.package_registry import list_packages as list_packages_registry

router = APIRouter(prefix="/packages", tags=["packages"])

# Node types whose content comes from an existing catalogued library resource,
# resolved server-side by id rather than trusting a client-supplied filesystem
# path (which would let a caller point create_package at arbitrary files).
LIBRARY_BACKED_NODE_TYPES = {"skill", "agent", "command"}


class PackageNodeIn(BaseModel):
    type: str
    name: str
    library_item_id: str | None = None
    config: dict | None = None
    content: str | None = None


class PackageCreate(BaseModel):
    id: str
    name: str
    version: str
    scope: str
    project_path: str | None = None
    folder: str | None = None
    description: str = ""
    nodes: list[PackageNodeIn] = []
    canvas_layout: dict = {}


def _serialize(package: Package) -> dict:
    return {
        "id": package.id,
        "name": package.name,
        "version": package.version,
        "scope": package.scope,
        "project_path": package.project_path,
        "content_path": str(package.content_path),
        "folder": package.folder,
        "description": package.description,
        "updated_at": package.updated_at,
        "canvas_layout": package.canvas_layout,
    }


def _get_package_or_404(conn: sqlite3.Connection, package_id: str) -> Package:
    package = get_package(conn, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail=f"Package '{package_id}' not found")
    return package


def _resolve_activation_targets(
    package: Package, claude_home: Path, claude_json_path: Path
) -> tuple[Path, Path]:
    if package.scope == "global":
        return claude_home, claude_json_path
    project_root = Path(package.project_path)
    return project_root, project_root / ".mcp.json"


@router.get("")
def get_packages(conn: sqlite3.Connection = Depends(get_db_connection)) -> list[dict]:
    return [_serialize(p) for p in list_packages_registry(conn)]


def _resolve_library_source_path(item_path: str, node_type: str) -> str:
    if node_type == "skill":
        return str(Path(item_path).parent)
    return item_path


def _resolve_nodes(
    nodes_in: list[PackageNodeIn], claude_home: Path, project_path: str | None
) -> list[PackageNode]:
    project_dir = Path(project_path) if project_path else None
    library_items_by_id = {item.id: item for item in scan_library(claude_home, project_dir)}

    nodes = []
    for n in nodes_in:
        source_path = None
        if n.type in LIBRARY_BACKED_NODE_TYPES:
            if not n.library_item_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Node '{n.name}' of type '{n.type}' requires library_item_id",
                )
            item = library_items_by_id.get(n.library_item_id)
            if item is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown library_item_id '{n.library_item_id}'",
                )
            source_path = _resolve_library_source_path(item.path, n.type)
        nodes.append(
            PackageNode(
                type=n.type,
                name=n.name,
                source_path=source_path,
                config=n.config,
                content=n.content,
            )
        )
    return nodes


@router.post("", status_code=201)
def post_package(
    body: PackageCreate,
    control_plane_home: Path = Depends(get_control_plane_home),
    claude_home: Path = Depends(get_claude_home_path),
    conn: sqlite3.Connection = Depends(get_db_connection),
) -> dict:
    nodes = _resolve_nodes(body.nodes, claude_home, body.project_path)
    try:
        package = create_package(
            control_plane_home,
            conn,
            id=body.id,
            name=body.name,
            version=body.version,
            scope=body.scope,
            project_path=body.project_path,
            folder=body.folder,
            description=body.description,
            nodes=nodes,
            canvas_layout=body.canvas_layout,
        )
    except InvalidPackageIdentifierError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _serialize(package)


@router.get("/{package_id}")
def get_package_by_id(
    package_id: str, conn: sqlite3.Connection = Depends(get_db_connection)
) -> dict:
    return _serialize(_get_package_or_404(conn, package_id))


@router.delete("/{package_id}", status_code=204)
def delete_package_by_id(
    package_id: str, conn: sqlite3.Connection = Depends(get_db_connection)
) -> None:
    _get_package_or_404(conn, package_id)
    delete_package(conn, package_id)


@router.get("/{package_id}/preview-activation")
def get_preview_activation(
    package_id: str,
    claude_home: Path = Depends(get_claude_home_path),
    conn: sqlite3.Connection = Depends(get_db_connection),
) -> list[dict]:
    package = _get_package_or_404(conn, package_id)
    target_root, _ = _resolve_activation_targets(package, claude_home, claude_home)
    diffs = preview_activation(package, target_root)
    return [{"relative_path": d.relative_path, "action": d.action} for d in diffs]


@router.post("/{package_id}/activate")
def post_activate_package(
    package_id: str,
    claude_home: Path = Depends(get_claude_home_path),
    claude_json_path: Path = Depends(get_claude_json_path),
    conn: sqlite3.Connection = Depends(get_db_connection),
) -> dict:
    package = _get_package_or_404(conn, package_id)
    target_root, mcp_target_path = _resolve_activation_targets(
        package, claude_home, claude_json_path
    )
    activate_package(conn, package, target_root, mcp_target_path)
    return {"activated": package_id}


@router.post("/{package_id}/deactivate")
def post_deactivate_package(
    package_id: str,
    claude_home: Path = Depends(get_claude_home_path),
    claude_json_path: Path = Depends(get_claude_json_path),
    conn: sqlite3.Connection = Depends(get_db_connection),
) -> dict:
    package = _get_package_or_404(conn, package_id)
    target_root, mcp_target_path = _resolve_activation_targets(
        package, claude_home, claude_json_path
    )
    result = deactivate_package(conn, package, target_root, mcp_target_path)
    return {"removed": result.removed, "preserved": result.preserved}
