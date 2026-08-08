import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.telemetry_reader import ProjectTelemetrySummary
from app.telemetry_reader.summary import summarize_project_telemetry


@dataclass(frozen=True)
class CombinationSummary:
    active_package_ids: list[str]
    telemetry: ProjectTelemetrySummary


@dataclass(frozen=True)
class IsolatedSummary:
    package_id: str
    windows: list[tuple[int, int | None]]
    turn_count: int
    period_input_tokens: int
    period_output_tokens: int
    tokens_by_model: dict


def reconstruct_active_windows(
    conn: sqlite3.Connection, project_path: str, package_id: str
) -> list[tuple[int, int | None]]:
    """Reconstruct (start, end) activation windows for one package in one
    project from the activate/deactivate event log, ordered chronologically.
    An open (still active) window has end=None."""
    rows = conn.execute(
        "SELECT action, occurred_at FROM activation_log "
        "WHERE package_id = ? AND project_path = ? ORDER BY occurred_at ASC",
        (package_id, project_path),
    ).fetchall()

    windows: list[tuple[int, int | None]] = []
    open_start: int | None = None
    for row in rows:
        if row["action"] == "activate" and open_start is None:
            open_start = row["occurred_at"]
        elif row["action"] == "deactivate" and open_start is not None:
            windows.append((open_start, row["occurred_at"]))
            open_start = None

    if open_start is not None:
        windows.append((open_start, None))

    return windows


def _epoch_to_iso(epoch_seconds: int) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _active_package_ids(
    conn: sqlite3.Connection, project_path: str, since: str | None, until: str | None
) -> list[str]:
    package_ids = {
        row["package_id"]
        for row in conn.execute(
            "SELECT DISTINCT package_id FROM activation_log WHERE project_path = ?",
            (project_path,),
        ).fetchall()
    }

    active = []
    for package_id in sorted(package_ids):
        windows = reconstruct_active_windows(conn, project_path, package_id)
        if any(_windows_overlap_period(window, since, until) for window in windows):
            active.append(package_id)
    return active


def _windows_overlap_period(
    window: tuple[int, int | None], since: str | None, until: str | None
) -> bool:
    window_start_iso = _epoch_to_iso(window[0])
    window_end_iso = _epoch_to_iso(window[1]) if window[1] is not None else None

    if until is not None and window_start_iso >= until:
        return False
    if since is not None and window_end_iso is not None and window_end_iso < since:
        return False
    return True


def combination_mode_summary(
    conn: sqlite3.Connection,
    claude_json_path: Path,
    claude_projects_root: Path,
    project_path: str,
    *,
    since: str | None = None,
    until: str | None = None,
) -> CombinationSummary:
    active_package_ids = _active_package_ids(conn, project_path, since, until)
    telemetry = summarize_project_telemetry(
        claude_json_path, claude_projects_root, project_path, since=since, until=until
    )
    return CombinationSummary(active_package_ids=active_package_ids, telemetry=telemetry)


def isolated_mode_summary(
    conn: sqlite3.Connection,
    claude_json_path: Path,
    claude_projects_root: Path,
    project_path: str,
    package_id: str,
    *,
    since: str | None = None,
    until: str | None = None,
) -> IsolatedSummary:
    windows = reconstruct_active_windows(conn, project_path, package_id)
    windows = [w for w in windows if _windows_overlap_period(w, since, until)]

    turn_count = 0
    period_input_tokens = 0
    period_output_tokens = 0
    tokens_by_model: dict[str, dict[str, int]] = defaultdict(
        lambda: {"input_tokens": 0, "output_tokens": 0}
    )

    for window_start, window_end in windows:
        window_since = _clip_bound(_epoch_to_iso(window_start), since, is_lower_bound=True)
        window_end_iso = _epoch_to_iso(window_end) if window_end is not None else None
        window_until = _clip_bound(window_end_iso, until, is_lower_bound=False)

        window_telemetry = summarize_project_telemetry(
            claude_json_path,
            claude_projects_root,
            project_path,
            since=window_since,
            until=window_until,
        )
        turn_count += window_telemetry.turn_count
        period_input_tokens += window_telemetry.period_input_tokens
        period_output_tokens += window_telemetry.period_output_tokens
        for model, counts in window_telemetry.tokens_by_model.items():
            tokens_by_model[model]["input_tokens"] += counts["input_tokens"]
            tokens_by_model[model]["output_tokens"] += counts["output_tokens"]

    return IsolatedSummary(
        package_id=package_id,
        windows=windows,
        turn_count=turn_count,
        period_input_tokens=period_input_tokens,
        period_output_tokens=period_output_tokens,
        tokens_by_model=dict(tokens_by_model),
    )


def _clip_bound(
    window_bound: str | None, period_bound: str | None, *, is_lower_bound: bool
) -> str | None:
    if window_bound is None:
        return period_bound
    if period_bound is None:
        return window_bound
    return max(window_bound, period_bound) if is_lower_bound else min(window_bound, period_bound)
