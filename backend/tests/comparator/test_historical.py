import json
from pathlib import Path

from app.comparator.historical import (
    combination_mode_summary,
    isolated_mode_summary,
    reconstruct_active_windows,
)
from app.db.connection import connect
from app.telemetry_reader.project_paths import encode_project_path


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def log_activation(conn, package_id: str, project_path: str, action: str, occurred_at: int) -> None:
    conn.execute(
        "INSERT INTO activation_log (package_id, project_path, action, occurred_at) VALUES (?, ?, ?, ?)",
        (package_id, project_path, action, occurred_at),
    )
    conn.commit()


def make_transcript(claude_home: Path, project_path: str, records: list[dict]) -> None:
    project_dir = claude_home / "projects" / encode_project_path(project_path)
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "session.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")


def assistant_record(*, timestamp: str, input_tokens: int = 1, output_tokens: int = 1) -> dict:
    return {
        "type": "assistant",
        "timestamp": timestamp,
        "message": {
            "model": "claude-sonnet-5",
            "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        },
    }


def test_reconstruct_active_windows_open_window_when_never_deactivated(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    log_activation(conn, "pkg-1", "/proj", "activate", 1000)

    windows = reconstruct_active_windows(conn, "/proj", "pkg-1")

    assert windows == [(1000, None)]


def test_reconstruct_active_windows_closed_window(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    log_activation(conn, "pkg-1", "/proj", "activate", 1000)
    log_activation(conn, "pkg-1", "/proj", "deactivate", 2000)

    windows = reconstruct_active_windows(conn, "/proj", "pkg-1")

    assert windows == [(1000, 2000)]


def test_reconstruct_active_windows_multiple_cycles(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    log_activation(conn, "pkg-1", "/proj", "activate", 1000)
    log_activation(conn, "pkg-1", "/proj", "deactivate", 2000)
    log_activation(conn, "pkg-1", "/proj", "activate", 3000)

    windows = reconstruct_active_windows(conn, "/proj", "pkg-1")

    assert windows == [(1000, 2000), (3000, None)]


def test_reconstruct_active_windows_ignores_other_packages_and_projects(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    log_activation(conn, "pkg-1", "/proj", "activate", 1000)
    log_activation(conn, "pkg-2", "/proj", "activate", 1500)
    log_activation(conn, "pkg-1", "/other-proj", "activate", 1600)

    windows = reconstruct_active_windows(conn, "/proj", "pkg-1")

    assert windows == [(1000, None)]


def test_combination_mode_lists_active_packages_and_telemetry(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    claude_home = tmp_path / "claude-home"
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {"/proj": {}}})
    project_path = "/proj"

    log_activation(conn, "pkg-a", project_path, "activate", 1000)
    log_activation(conn, "pkg-b", project_path, "activate", 1500)

    make_transcript(
        claude_home,
        project_path,
        [assistant_record(timestamp="2026-08-06T00:00:10Z")],
    )

    result = combination_mode_summary(
        conn,
        claude_json,
        claude_home / "projects",
        project_path,
        since="2026-08-06T00:00:00Z",
        until="2026-08-06T00:01:00Z",
    )

    assert result.active_package_ids == ["pkg-a", "pkg-b"]
    assert result.telemetry.turn_count == 1


def test_isolated_mode_sums_telemetry_across_multiple_windows(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    claude_home = tmp_path / "claude-home"
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {}})
    project_path = "/proj"

    log_activation(conn, "pkg-1", project_path, "activate", 1000)
    log_activation(conn, "pkg-1", project_path, "deactivate", 1000000000)
    log_activation(conn, "pkg-1", project_path, "activate", 1000000001)

    make_transcript(
        claude_home,
        project_path,
        [
            assistant_record(timestamp="2000-01-01T00:00:05Z", input_tokens=10),
            assistant_record(timestamp="2035-01-01T00:00:05Z", input_tokens=20),
        ],
    )

    result = isolated_mode_summary(
        conn, claude_json, claude_home / "projects", project_path, "pkg-1"
    )

    assert result.package_id == "pkg-1"
    assert result.turn_count == 2
    assert result.period_input_tokens == 30
    assert len(result.windows) == 2


def test_isolated_mode_returns_zero_when_package_never_active(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    claude_home = tmp_path / "claude-home"
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {}})

    result = isolated_mode_summary(
        conn, claude_json, claude_home / "projects", "/proj", "pkg-ghost"
    )

    assert result.turn_count == 0
    assert result.windows == []


def test_isolated_mode_excludes_window_entirely_after_until(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    claude_home = tmp_path / "claude-home"
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {}})
    project_path = "/proj"

    # Window starts in 2030 — entirely after the requested "until" of 2020.
    log_activation(conn, "pkg-1", project_path, "activate", 1893456000)

    result = isolated_mode_summary(
        conn,
        claude_json,
        claude_home / "projects",
        project_path,
        "pkg-1",
        until="2020-01-01T00:00:00Z",
    )

    assert result.windows == []


def test_isolated_mode_excludes_window_entirely_before_since(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    claude_home = tmp_path / "claude-home"
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {}})
    project_path = "/proj"

    log_activation(conn, "pkg-1", project_path, "activate", 1000)
    log_activation(conn, "pkg-1", project_path, "deactivate", 2000)

    result = isolated_mode_summary(
        conn,
        claude_json,
        claude_home / "projects",
        project_path,
        "pkg-1",
        since="2030-01-01T00:00:00Z",
    )

    assert result.windows == []


def test_isolated_mode_clips_window_telemetry_to_period_bounds(tmp_path: Path) -> None:
    conn = connect(tmp_path / "index.sqlite")
    claude_home = tmp_path / "claude-home"
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {}})
    project_path = "/proj"

    # Window spans all of January 2020; since/until narrow it to Jan 10-20.
    log_activation(conn, "pkg-1", project_path, "activate", 1577836800)
    log_activation(conn, "pkg-1", project_path, "deactivate", 1580515200)

    make_transcript(
        claude_home,
        project_path,
        [
            assistant_record(timestamp="2020-01-05T00:00:00Z", input_tokens=1),
            assistant_record(timestamp="2020-01-15T00:00:00Z", input_tokens=100),
            assistant_record(timestamp="2020-01-25T00:00:00Z", input_tokens=1),
        ],
    )

    result = isolated_mode_summary(
        conn,
        claude_json,
        claude_home / "projects",
        project_path,
        "pkg-1",
        since="2020-01-10T00:00:00Z",
        until="2020-01-20T00:00:00Z",
    )

    assert result.turn_count == 1
    assert result.period_input_tokens == 100
