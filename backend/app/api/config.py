from pathlib import Path

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_claude_json_path, get_global_settings_path
from app.config_reader import (
    compute_effective_permissions,
    read_global_config,
    read_global_settings,
    read_local_settings,
    read_project_mcp_config,
)

router = APIRouter(prefix="/config", tags=["config"])


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
        "effective_permissions": compute_effective_permissions(
            user_settings, project_settings, local_settings
        ),
    }
