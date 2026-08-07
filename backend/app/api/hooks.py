import sqlite3
import time
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import get_backend_port, get_db_connection, get_global_settings_path
from app.hooks_installer import (
    install_session_start_hook,
    is_session_start_hook_installed,
    uninstall_session_start_hook,
)
from app.hooks_installer.session_store import record_session_start

router = APIRouter(prefix="/hooks", tags=["hooks"])


class SessionStartNotification(BaseModel):
    """The Claude Code SessionStart hook sends its full stdin JSON payload
    (session_id, cwd, hook_event_name, transcript_path, ...) — only the
    fields we need are declared; the rest are ignored."""

    model_config = ConfigDict(extra="ignore")

    session_id: str
    cwd: str


@router.post("/session-start", status_code=204)
def post_session_start(
    body: SessionStartNotification, conn: sqlite3.Connection = Depends(get_db_connection)
) -> None:
    record_session_start(conn, body.session_id, body.cwd, int(time.time()))


@router.get("/session-start/status")
def get_session_start_hook_status(
    settings_path: Path = Depends(get_global_settings_path),
) -> dict:
    return {"installed": is_session_start_hook_installed(settings_path)}


@router.post("/session-start/install")
def post_install_session_start_hook(
    settings_path: Path = Depends(get_global_settings_path),
    port: int = Depends(get_backend_port),
) -> dict:
    installed = install_session_start_hook(settings_path, port=port)
    return {"installed": installed}


@router.delete("/session-start/install")
def delete_uninstall_session_start_hook(
    settings_path: Path = Depends(get_global_settings_path),
) -> dict:
    uninstalled = uninstall_session_start_hook(settings_path)
    return {"uninstalled": uninstalled}
