from dataclasses import dataclass
from pathlib import Path

from app.json_store import read_json


@dataclass(frozen=True)
class ProjectCumulativeUsage:
    cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    total_cache_creation_input_tokens: int
    total_cache_read_input_tokens: int
    last_session_id: str | None
    model_usage: dict


def read_project_cumulative_usage(
    claude_json_path: Path, project_path: str
) -> ProjectCumulativeUsage | None:
    projects = read_json(claude_json_path).get("projects", {})
    project = projects.get(project_path)
    if project is None:
        return None

    return ProjectCumulativeUsage(
        cost_usd=project.get("lastCost", 0.0),
        total_input_tokens=project.get("lastTotalInputTokens", 0),
        total_output_tokens=project.get("lastTotalOutputTokens", 0),
        total_cache_creation_input_tokens=project.get("lastTotalCacheCreationInputTokens", 0),
        total_cache_read_input_tokens=project.get("lastTotalCacheReadInputTokens", 0),
        last_session_id=project.get("lastSessionId"),
        model_usage=project.get("lastModelUsage", {}),
    )
