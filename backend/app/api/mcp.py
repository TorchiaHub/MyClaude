from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.dependencies import get_claude_json_path
from app.mcp_manager import add_server, list_servers, remove_server

router = APIRouter(prefix="/mcp", tags=["mcp"])


class McpServerCreate(BaseModel):
    name: str
    scope: str
    project_path: str | None = None
    config: dict


class McpServerScope(BaseModel):
    scope: str
    project_path: str | None = None


def _resolve_config_path(scope: str, project_path: str | None, claude_json_path: Path) -> Path:
    if scope == "global":
        return claude_json_path
    if scope == "project":
        if not project_path:
            raise HTTPException(
                status_code=400, detail="project_path is required for project scope"
            )
        return Path(project_path) / ".mcp.json"
    raise HTTPException(status_code=400, detail=f"Unknown scope '{scope}'")


@router.get("/servers")
def get_servers(
    project_path: str | None = Query(default=None),
    claude_json_path: Path = Depends(get_claude_json_path),
) -> list[dict]:
    project_mcp_path = Path(project_path) / ".mcp.json" if project_path else None
    entries = list_servers(claude_json_path, project_mcp_path)
    return [{"name": entry.name, "scope": entry.scope, "config": entry.config} for entry in entries]


@router.post("/servers", status_code=201)
def post_server(
    body: McpServerCreate, claude_json_path: Path = Depends(get_claude_json_path)
) -> dict:
    config_path = _resolve_config_path(body.scope, body.project_path, claude_json_path)
    add_server(config_path, body.name, body.config)
    return {"name": body.name, "scope": body.scope, "config": body.config}


@router.delete("/servers/{name}", status_code=204)
def delete_server(
    name: str, body: McpServerScope, claude_json_path: Path = Depends(get_claude_json_path)
) -> None:
    config_path = _resolve_config_path(body.scope, body.project_path, claude_json_path)
    removed = remove_server(config_path, name)
    if not removed:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")
