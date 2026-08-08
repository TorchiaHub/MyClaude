from pathlib import Path

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.dependencies import get_claude_json_path, get_global_settings_path
from app.config_reader import (
    compute_effective_permissions,
    read_global_config,
    read_global_settings,
    read_local_settings,
    read_project_mcp_config,
    replace_permission_rules,
)
from app.json_store import write_json

router = APIRouter(prefix="/config", tags=["config"])


class PermissionRulesUpdate(BaseModel):
    allow: list[str]
    ask: list[str]
    deny: list[str]


@router.get("/global")
def get_global_config(
    claude_json_path: Path = Depends(get_claude_json_path),
    settings_path: Path = Depends(get_global_settings_path),
) -> dict:
    settings = read_global_settings(settings_path)
    return {
        "claude_json": read_global_config(claude_json_path),
        "settings": settings,
        "effective_permissions": compute_effective_permissions(settings, {}, {}),
    }


@router.get("/project")
def get_project_config(
    path: str = Query(..., description="Absolute path to the project"),
    settings_path: Path = Depends(get_global_settings_path),
) -> dict:
    project_dir = Path(path)
    user_settings = read_global_settings(settings_path)
    project_settings = read_global_settings(project_dir / ".claude" / "settings.json")
    local_settings = read_local_settings(project_dir / ".claude" / "settings.local.json")

    return {
        "settings": project_settings,
        "local_settings": local_settings,
        "mcp_servers": read_project_mcp_config(project_dir / ".mcp.json"),
        "own_permissions": compute_effective_permissions({}, project_settings, {}),
        "effective_permissions": compute_effective_permissions(
            user_settings, project_settings, local_settings
        ),
    }


@router.put("/global/permissions")
def put_global_permissions(
    body: PermissionRulesUpdate,
    settings_path: Path = Depends(get_global_settings_path),
) -> dict:
    settings = read_global_settings(settings_path)
    updated = replace_permission_rules(settings, body.model_dump())
    write_json(settings_path, updated)
    return {"effective_permissions": compute_effective_permissions(updated, {}, {})}


@router.put("/project/permissions")
def put_project_permissions(
    body: PermissionRulesUpdate,
    path: str = Query(..., description="Absolute path to the project"),
) -> dict:
    project_settings_path = Path(path) / ".claude" / "settings.json"
    settings = read_global_settings(project_settings_path)
    updated = replace_permission_rules(settings, body.model_dump())
    write_json(project_settings_path, updated)
    return {"own_permissions": compute_effective_permissions({}, updated, {})}
