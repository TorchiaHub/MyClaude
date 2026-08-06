import json
from pathlib import Path

from app.telemetry_reader.cumulative_usage import read_project_cumulative_usage


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_read_project_cumulative_usage_extracts_known_fields(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(
        claude_json,
        {
            "projects": {
                "/home/matt/my-project": {
                    "lastCost": 2.31,
                    "lastTotalInputTokens": 542,
                    "lastTotalOutputTokens": 9534,
                    "lastTotalCacheCreationInputTokens": 179552,
                    "lastTotalCacheReadInputTokens": 3631619,
                    "lastModelUsage": {
                        "claude-sonnet-5": {
                            "inputTokens": 542,
                            "outputTokens": 9534,
                            "costUSD": 2.31,
                        }
                    },
                    "lastSessionId": "5029a49f-084e-465d-9396-9ec3dd03f503",
                }
            }
        },
    )

    result = read_project_cumulative_usage(claude_json, "/home/matt/my-project")

    assert result is not None
    assert result.cost_usd == 2.31
    assert result.total_input_tokens == 542
    assert result.total_output_tokens == 9534
    assert result.total_cache_creation_input_tokens == 179552
    assert result.total_cache_read_input_tokens == 3631619
    assert result.last_session_id == "5029a49f-084e-465d-9396-9ec3dd03f503"
    assert result.model_usage == {
        "claude-sonnet-5": {"inputTokens": 542, "outputTokens": 9534, "costUSD": 2.31}
    }


def test_read_project_cumulative_usage_returns_none_for_unknown_project(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {}})

    result = read_project_cumulative_usage(claude_json, "/home/matt/unknown-project")

    assert result is None


def test_read_project_cumulative_usage_defaults_missing_fields_to_zero(tmp_path: Path) -> None:
    claude_json = tmp_path / ".claude.json"
    write_json(claude_json, {"projects": {"/home/matt/bare-project": {}}})

    result = read_project_cumulative_usage(claude_json, "/home/matt/bare-project")

    assert result is not None
    assert result.cost_usd == 0.0
    assert result.total_input_tokens == 0
    assert result.model_usage == {}


def test_read_project_cumulative_usage_returns_none_when_claude_json_missing(
    tmp_path: Path,
) -> None:
    result = read_project_cumulative_usage(tmp_path / "does-not-exist.json", "/anything")

    assert result is None
