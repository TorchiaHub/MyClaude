import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.activity_monitor import list_sessions, parse_activity_events, resolve_transcript_path
from app.api.dependencies import get_claude_home_path

router = APIRouter(prefix="/activity", tags=["activity"])

POLL_INTERVAL_SECONDS = 1.0


def _serialize_session(session) -> dict:
    return {
        "pid": session.pid,
        "session_id": session.session_id,
        "cwd": session.cwd,
        "status": session.status,
        "name": session.name,
        "started_at": session.started_at,
        "updated_at": session.updated_at,
    }


@router.websocket("/live")
async def websocket_live_activity(
    websocket: WebSocket, claude_home: Path = Depends(get_claude_home_path)
) -> None:
    await websocket.accept()
    try:
        while True:
            sessions = list_sessions(claude_home / "sessions")
            await websocket.send_json([_serialize_session(s) for s in sessions])
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except WebSocketDisconnect:
        pass


@router.get("/sessions/{session_id}/drilldown")
def get_session_drilldown(
    session_id: str,
    cwd: str = Query(...),
    claude_home: Path = Depends(get_claude_home_path),
) -> list[dict]:
    transcript_path = resolve_transcript_path(claude_home / "projects", cwd, session_id)
    events = parse_activity_events(transcript_path)
    return [
        {"timestamp": e.timestamp, "tool_name": e.tool_name, "session_id": e.session_id}
        for e in events
    ]
