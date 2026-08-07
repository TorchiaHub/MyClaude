import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.activation_engine import activate_package, deactivate_package, preview_activation
from app.api.dependencies import (
    get_claude_home_path,
    get_claude_json_path,
    get_control_plane_home,
    get_db_connection,
    get_home_path,
)
from app.comparator import compare_static
from app.comparator.historical import combination_mode_summary, isolated_mode_summary
from app.library_registry import scan_library
from app.mcp_manager import list_servers
from app.package_registry import (
    InvalidPackageIdentifierError,
    Package,
    PackageNode,
    create_package,
    delete_package,
    get_package,
    import_package,
)
from app.package_registry import list_packages as list_packages_registry
from app.package_registry.dependencies import detect_missing_dependencies
from app.sanitizer import build_export_bundle

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


class PackageImportRequest(BaseModel):
    bundle: dict
    id: str
    scope: str
    project_path: str | None = None
    folder: str | None = None


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


def _serialize_static_diff(diff) -> dict:
    return {
        "package_a_id": diff.package_a_id,
        "package_b_id": diff.package_b_id,
        "is_identical": diff.is_identical,
        "by_type": {
            node_type: {
                "only_in_a": type_diff.only_in_a,
                "only_in_b": type_diff.only_in_b,
                "common": type_diff.common,
            }
            for node_type, type_diff in diff.by_type.items()
        },
    }


def _serialize_isolated_summary(summary) -> dict:
    return {
        "package_id": summary.package_id,
        "windows": summary.windows,
        "turn_count": summary.turn_count,
        "period_input_tokens": summary.period_input_tokens,
        "period_output_tokens": summary.period_output_tokens,
        "tokens_by_model": summary.tokens_by_model,
    }


def _serialize_telemetry(telemetry) -> dict:
    return {
        "turn_count": telemetry.turn_count,
        "period_input_tokens": telemetry.period_input_tokens,
        "period_output_tokens": telemetry.period_output_tokens,
        "tokens_by_model": telemetry.tokens_by_model,
    }


@router.get("/compare")
def get_compare(
    mode: str = Query(...),
    a: str | None = Query(default=None),
    b: str | None = Query(default=None),
    project_path: str | None = Query(default=None),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    since_a: str | None = Query(default=None),
    until_a: str | None = Query(default=None),
    since_b: str | None = Query(default=None),
    until_b: str | None = Query(default=None),
    claude_home: Path = Depends(get_claude_home_path),
    claude_json_path: Path = Depends(get_claude_json_path),
    conn: sqlite3.Connection = Depends(get_db_connection),
) -> dict:
    if mode not in ("static", "combination", "isolated"):
        raise HTTPException(status_code=400, detail=f"Unknown mode '{mode}'")

    result: dict = {}

    if mode in ("static", "isolated"):
        if not a or not b:
            raise HTTPException(status_code=400, detail="mode requires 'a' and 'b' package ids")
        package_a = _get_package_or_404(conn, a)
        package_b = _get_package_or_404(conn, b)
        result["static_diff"] = _serialize_static_diff(compare_static(package_a, package_b))

    if mode == "isolated":
        if not project_path:
            raise HTTPException(status_code=400, detail="mode='isolated' requires project_path")
        result["isolated"] = {
            "a": _serialize_isolated_summary(
                isolated_mode_summary(
                    conn,
                    claude_json_path,
                    claude_home / "projects",
                    project_path,
                    a,
                    since=since,
                    until=until,
                )
            ),
            "b": _serialize_isolated_summary(
                isolated_mode_summary(
                    conn,
                    claude_json_path,
                    claude_home / "projects",
                    project_path,
                    b,
                    since=since,
                    until=until,
                )
            ),
        }

    if mode == "combination":
        if not project_path or not since_a or not until_a or not since_b or not until_b:
            raise HTTPException(
                status_code=400,
                detail="mode='combination' requires project_path, since_a/until_a, since_b/until_b",
            )
        summary_a = combination_mode_summary(
            conn,
            claude_json_path,
            claude_home / "projects",
            project_path,
            since=since_a,
            until=until_a,
        )
        summary_b = combination_mode_summary(
            conn,
            claude_json_path,
            claude_home / "projects",
            project_path,
            since=since_b,
            until=until_b,
        )
        result["combination"] = {
            "a": {
                "active_package_ids": summary_a.active_package_ids,
                "telemetry": _serialize_telemetry(summary_a.telemetry),
            },
            "b": {
                "active_package_ids": summary_b.active_package_ids,
                "telemetry": _serialize_telemetry(summary_b.telemetry),
            },
        }

    return result


def _local_dependency_names(
    claude_home: Path, claude_json_path: Path, project_path: str | None
) -> dict[str, set[str]]:
    project_dir = Path(project_path) if project_path else None
    library_items = scan_library(claude_home, project_dir)
    mcp_servers = list_servers(
        claude_json_path, (project_dir / ".mcp.json") if project_dir else None
    )
    return {
        "skill": {i.name for i in library_items if i.resource_type == "skill"},
        "agent": {i.name for i in library_items if i.resource_type == "agent"},
        "command": {i.name for i in library_items if i.resource_type == "command"},
        "mcp": {entry.name for entry in mcp_servers},
    }


@router.post("/import", status_code=201)
def post_package_import(
    body: PackageImportRequest,
    control_plane_home: Path = Depends(get_control_plane_home),
    claude_home: Path = Depends(get_claude_home_path),
    claude_json_path: Path = Depends(get_claude_json_path),
    conn: sqlite3.Connection = Depends(get_db_connection),
) -> dict:
    try:
        package = import_package(
            control_plane_home,
            conn,
            bundle=body.bundle,
            id=body.id,
            scope=body.scope,
            project_path=body.project_path,
            folder=body.folder,
        )
    except InvalidPackageIdentifierError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    local = _local_dependency_names(claude_home, claude_json_path, body.project_path)
    missing = detect_missing_dependencies(
        body.bundle,
        local_skill_names=local["skill"],
        local_agent_names=local["agent"],
        local_command_names=local["command"],
        local_mcp_server_names=local["mcp"],
    )
    return {"package": _serialize(package), "missing_dependencies": missing}


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


@router.get("/{package_id}/export")
def get_package_export(
    package_id: str,
    home: Path = Depends(get_home_path),
    conn: sqlite3.Connection = Depends(get_db_connection),
) -> dict:
    package = _get_package_or_404(conn, package_id)
    return build_export_bundle(package.content_path, package, home)


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
