import json
from dataclasses import dataclass, field
from pathlib import Path

# Explicit, always-true caveat: Claude Code's checkpoint mechanism only
# tracks files it edits itself via Edit/Write (file-history-delta entries).
# It never records changes made by raw Bash commands (rm/mv/cp/sed, ...) or
# by a background subagent — those are structurally invisible in this data,
# not something a specific checkpoint can be flagged as "missing". Callers
# (the API/UI) must surface this note alongside any checkpoint timeline so
# a user never assumes rewind covers those cases.
CHECKPOINT_COVERAGE_CAVEAT = (
    "I checkpoint coprono solo le modifiche fatte da Claude Code tramite i tool "
    "Edit/Write. Le modifiche da comandi Bash (rm, mv, cp, sed, ...) e quelle di "
    "un subagent in background NON sono tracciate e non possono essere ripristinate "
    "da qui — serve Git per quei casi."
)


@dataclass(frozen=True)
class Checkpoint:
    message_id: str
    timestamp: str
    changed_files: list[str] = field(default_factory=list)


def extract_checkpoints(jsonl_path: Path) -> list[Checkpoint]:
    """Reconstruct the checkpoint timeline for a session from its transcript.

    Like the other transcript readers, this degrades gracefully on malformed
    lines or an unrecognized shape, since .jsonl is an internal, unstable
    format.
    """
    if not jsonl_path.is_file():
        return []

    checkpoints_by_message_id: dict[str, Checkpoint] = {}
    order: list[str] = []

    for line in jsonl_path.read_text().splitlines():
        record = _parse_line(line)
        if record is None:
            continue

        if record["type"] == "snapshot":
            message_id = record["message_id"]
            if message_id not in checkpoints_by_message_id:
                checkpoints_by_message_id[message_id] = Checkpoint(
                    message_id=message_id, timestamp=record["timestamp"]
                )
                order.append(message_id)
        elif record["type"] == "delta":
            snapshot_message_id = record["snapshot_message_id"]
            checkpoint = checkpoints_by_message_id.get(snapshot_message_id)
            if checkpoint is not None:
                checkpoint.changed_files.append(record["tracking_path"])

    return [checkpoints_by_message_id[message_id] for message_id in order]


def _parse_line(line: str) -> dict | None:
    if not line.strip():
        return None

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    record_type = data.get("type")

    if record_type == "file-history-snapshot":
        snapshot = data.get("snapshot")
        message_id = data.get("messageId")
        if not isinstance(snapshot, dict) or not isinstance(message_id, str):
            return None
        timestamp = snapshot.get("timestamp")
        if not isinstance(timestamp, str):
            return None
        return {"type": "snapshot", "message_id": message_id, "timestamp": timestamp}

    if record_type == "file-history-delta":
        snapshot_message_id = data.get("snapshotMessageId")
        tracking_path = data.get("trackingPath")
        if not isinstance(snapshot_message_id, str) or not isinstance(tracking_path, str):
            return None
        return {
            "type": "delta",
            "snapshot_message_id": snapshot_message_id,
            "tracking_path": tracking_path,
        }

    return None
