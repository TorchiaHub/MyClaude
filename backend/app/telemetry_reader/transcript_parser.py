import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TurnUsage:
    model: str
    timestamp: str
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int


def parse_transcript_turns(jsonl_path: Path) -> list[TurnUsage]:
    """Parse a Claude Code session transcript for per-turn token usage.

    The .jsonl transcript format is internal to Claude Code and not
    guaranteed stable across versions, so this degrades gracefully:
    malformed lines and lines that don't look like an assistant message
    with usage data are skipped rather than raising.
    """
    if not jsonl_path.is_file():
        return []

    turns = []
    for line in jsonl_path.read_text().splitlines():
        turn = _parse_line(line)
        if turn is not None:
            turns.append(turn)
    return turns


def _parse_line(line: str) -> TurnUsage | None:
    if not line.strip():
        return None

    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None

    if not isinstance(record, dict) or record.get("type") != "assistant":
        return None

    message = record.get("message", {})
    usage = message.get("usage")
    if not isinstance(usage, dict):
        return None

    try:
        return TurnUsage(
            model=message.get("model", "unknown"),
            timestamp=record.get("timestamp", ""),
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            cache_creation_input_tokens=usage.get("cache_creation_input_tokens", 0),
            cache_read_input_tokens=usage.get("cache_read_input_tokens", 0),
        )
    except (KeyError, TypeError):
        return None
