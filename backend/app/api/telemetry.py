from pathlib import Path

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_claude_home_path, get_claude_json_path
from app.telemetry_reader import summarize_project_telemetry

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/summary")
def get_telemetry_summary(
    project_path: str = Query(...),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    claude_json_path: Path = Depends(get_claude_json_path),
    claude_home: Path = Depends(get_claude_home_path),
) -> dict:
    summary = summarize_project_telemetry(
        claude_json_path, claude_home / "projects", project_path, since=since, until=until
    )
    return {
        "cumulative": (
            None
            if summary.cumulative is None
            else {
                "cost_usd": summary.cumulative.cost_usd,
                "total_input_tokens": summary.cumulative.total_input_tokens,
                "total_output_tokens": summary.cumulative.total_output_tokens,
                "total_cache_creation_input_tokens": (
                    summary.cumulative.total_cache_creation_input_tokens
                ),
                "total_cache_read_input_tokens": summary.cumulative.total_cache_read_input_tokens,
                "last_session_id": summary.cumulative.last_session_id,
                "model_usage": summary.cumulative.model_usage,
            }
        ),
        "turn_count": summary.turn_count,
        "period_input_tokens": summary.period_input_tokens,
        "period_output_tokens": summary.period_output_tokens,
        "tokens_by_model": summary.tokens_by_model,
    }
