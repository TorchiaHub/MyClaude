import json
from pathlib import Path

from app.telemetry_reader.transcript_parser import parse_transcript_turns


def write_lines(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")


def assistant_record(
    *,
    model: str = "claude-sonnet-5",
    input_tokens: int = 10,
    output_tokens: int = 20,
    cache_creation_input_tokens: int = 0,
    cache_read_input_tokens: int = 0,
    timestamp: str = "2026-08-06T18:53:34.234Z",
) -> dict:
    return {
        "type": "assistant",
        "timestamp": timestamp,
        "message": {
            "model": model,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_creation_input_tokens": cache_creation_input_tokens,
                "cache_read_input_tokens": cache_read_input_tokens,
            },
        },
    }


def test_parse_transcript_turns_extracts_usage_from_assistant_messages(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    write_lines(
        path,
        [
            {"type": "user", "message": {"role": "user"}},
            assistant_record(input_tokens=10, output_tokens=20),
        ],
    )

    turns = parse_transcript_turns(path)

    assert len(turns) == 1
    assert turns[0].model == "claude-sonnet-5"
    assert turns[0].input_tokens == 10
    assert turns[0].output_tokens == 20
    assert turns[0].timestamp == "2026-08-06T18:53:34.234Z"


def test_parse_transcript_turns_ignores_non_assistant_lines(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    write_lines(
        path,
        [
            {"type": "queue-operation", "operation": "enqueue"},
            {"type": "user", "message": {"role": "user"}},
        ],
    )

    turns = parse_transcript_turns(path)

    assert turns == []


def test_parse_transcript_turns_skips_malformed_json_lines(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    good = json.dumps(assistant_record(input_tokens=5, output_tokens=7))
    path.write_text(f"{good}\nnot valid json\n{good}\n")

    turns = parse_transcript_turns(path)

    assert len(turns) == 2


def test_parse_transcript_turns_skips_assistant_lines_without_usage(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    write_lines(
        path,
        [
            {"type": "assistant", "message": {"model": "claude-sonnet-5"}},
            assistant_record(),
        ],
    )

    turns = parse_transcript_turns(path)

    assert len(turns) == 1


def test_parse_transcript_turns_returns_empty_list_for_missing_file(tmp_path: Path) -> None:
    turns = parse_transcript_turns(tmp_path / "does-not-exist.jsonl")

    assert turns == []


def test_parse_transcript_turns_includes_cache_tokens() -> None:
    record = assistant_record(cache_creation_input_tokens=100, cache_read_input_tokens=200)
    assert record["message"]["usage"]["cache_creation_input_tokens"] == 100


def test_parse_transcript_turns_reads_cache_tokens_from_file(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    write_lines(
        path, [assistant_record(cache_creation_input_tokens=100, cache_read_input_tokens=200)]
    )

    turns = parse_transcript_turns(path)

    assert turns[0].cache_creation_input_tokens == 100
    assert turns[0].cache_read_input_tokens == 200
