from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from app.telemetry_reader.cumulative_usage import (
    ProjectCumulativeUsage,
    read_project_cumulative_usage,
)
from app.telemetry_reader.project_paths import find_transcript_files
from app.telemetry_reader.transcript_parser import parse_transcript_turns


@dataclass(frozen=True)
class ProjectTelemetrySummary:
    cumulative: ProjectCumulativeUsage | None
    turn_count: int
    period_input_tokens: int
    period_output_tokens: int
    tokens_by_model: dict = field(default_factory=dict)


def summarize_project_telemetry(
    claude_json_path: Path,
    claude_projects_root: Path,
    project_path: str,
    *,
    since: str | None = None,
    until: str | None = None,
) -> ProjectTelemetrySummary:
    cumulative = read_project_cumulative_usage(claude_json_path, project_path)

    turns = [
        turn
        for transcript_file in find_transcript_files(claude_projects_root, project_path)
        for turn in parse_transcript_turns(transcript_file)
    ]
    turns = [turn for turn in turns if _in_period(turn.timestamp, since, until)]

    tokens_by_model: dict[str, dict[str, int]] = defaultdict(
        lambda: {"input_tokens": 0, "output_tokens": 0}
    )
    for turn in turns:
        tokens_by_model[turn.model]["input_tokens"] += turn.input_tokens
        tokens_by_model[turn.model]["output_tokens"] += turn.output_tokens

    return ProjectTelemetrySummary(
        cumulative=cumulative,
        turn_count=len(turns),
        period_input_tokens=sum(turn.input_tokens for turn in turns),
        period_output_tokens=sum(turn.output_tokens for turn in turns),
        tokens_by_model=dict(tokens_by_model),
    )


def _in_period(timestamp: str, since: str | None, until: str | None) -> bool:
    if since is not None and timestamp < since:
        return False
    if until is not None and timestamp >= until:
        return False
    return True
