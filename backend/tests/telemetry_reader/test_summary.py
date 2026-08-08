import json
from pathlib import Path

from app.telemetry_reader.project_paths import encode_project_path
from app.telemetry_reader.summary import summarize_project_telemetry


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def make_transcript(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")


def assistant_record(
    *, model: str = "claude-sonnet-5", input_tokens: int, output_tokens: int, timestamp: str
) -> dict:
    return {
        "type": "assistant",
        "timestamp": timestamp,
        "message": {
            "model": model,
            "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        },
    }


def setup_project(tmp_path: Path, project_path: str) -> tuple[Path, Path]:
    claude_json = tmp_path / ".claude.json"
    projects_root = tmp_path / "projects"
    write_json(
        claude_json,
        {
            "projects": {
                project_path: {
                    "lastCost": 1.5,
                    "lastTotalInputTokens": 100,
                    "lastTotalOutputTokens": 200,
                }
            }
        },
    )
    project_dir = projects_root / encode_project_path(project_path)
    project_dir.mkdir(parents=True)
    return claude_json, project_dir


def test_summarize_project_telemetry_combines_cumulative_and_turn_totals(tmp_path: Path) -> None:
    claude_json, project_dir = setup_project(tmp_path, "/home/matt/my-project")
    make_transcript(
        project_dir / "session-a.jsonl",
        [
            assistant_record(input_tokens=10, output_tokens=20, timestamp="2026-08-01T10:00:00Z"),
            assistant_record(input_tokens=5, output_tokens=15, timestamp="2026-08-02T10:00:00Z"),
        ],
    )

    result = summarize_project_telemetry(claude_json, project_dir.parent, "/home/matt/my-project")

    assert result.cumulative.cost_usd == 1.5
    assert result.turn_count == 2
    assert result.period_input_tokens == 15
    assert result.period_output_tokens == 35


def test_summarize_project_telemetry_aggregates_across_multiple_sessions(tmp_path: Path) -> None:
    claude_json, project_dir = setup_project(tmp_path, "/home/matt/my-project")
    make_transcript(
        project_dir / "session-a.jsonl",
        [assistant_record(input_tokens=10, output_tokens=20, timestamp="2026-08-01T10:00:00Z")],
    )
    make_transcript(
        project_dir / "session-b.jsonl",
        [assistant_record(input_tokens=1, output_tokens=2, timestamp="2026-08-02T10:00:00Z")],
    )

    result = summarize_project_telemetry(claude_json, project_dir.parent, "/home/matt/my-project")

    assert result.turn_count == 2
    assert result.period_input_tokens == 11


def test_summarize_project_telemetry_filters_by_since_and_until(tmp_path: Path) -> None:
    claude_json, project_dir = setup_project(tmp_path, "/home/matt/my-project")
    make_transcript(
        project_dir / "session-a.jsonl",
        [
            assistant_record(input_tokens=10, output_tokens=0, timestamp="2026-08-01T10:00:00Z"),
            assistant_record(input_tokens=20, output_tokens=0, timestamp="2026-08-05T10:00:00Z"),
            assistant_record(input_tokens=30, output_tokens=0, timestamp="2026-08-10T10:00:00Z"),
        ],
    )

    result = summarize_project_telemetry(
        claude_json,
        project_dir.parent,
        "/home/matt/my-project",
        since="2026-08-02T00:00:00Z",
        until="2026-08-06T00:00:00Z",
    )

    assert result.turn_count == 1
    assert result.period_input_tokens == 20


def test_summarize_project_telemetry_breaks_down_tokens_by_model(tmp_path: Path) -> None:
    claude_json, project_dir = setup_project(tmp_path, "/home/matt/my-project")
    make_transcript(
        project_dir / "session-a.jsonl",
        [
            assistant_record(
                model="claude-sonnet-5",
                input_tokens=10,
                output_tokens=5,
                timestamp="2026-08-01T10:00:00Z",
            ),
            assistant_record(
                model="claude-haiku-4-5",
                input_tokens=1,
                output_tokens=1,
                timestamp="2026-08-01T11:00:00Z",
            ),
        ],
    )

    result = summarize_project_telemetry(claude_json, project_dir.parent, "/home/matt/my-project")

    assert result.tokens_by_model["claude-sonnet-5"] == {"input_tokens": 10, "output_tokens": 5}
    assert result.tokens_by_model["claude-haiku-4-5"] == {"input_tokens": 1, "output_tokens": 1}


def test_summarize_project_telemetry_handles_project_with_no_transcripts(tmp_path: Path) -> None:
    claude_json, project_dir = setup_project(tmp_path, "/home/matt/my-project")

    result = summarize_project_telemetry(claude_json, project_dir.parent, "/home/matt/my-project")

    assert result.turn_count == 0
    assert result.period_input_tokens == 0
    assert result.cumulative.cost_usd == 1.5


def test_summarize_project_telemetry_handles_unknown_project_gracefully(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {}})

    result = summarize_project_telemetry(
        claude_json, tmp_path / "projects", "/home/matt/unregistered"
    )

    assert result.cumulative is None
    assert result.turn_count == 0
