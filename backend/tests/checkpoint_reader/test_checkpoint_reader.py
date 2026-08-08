import json
from pathlib import Path

from app.checkpoint_reader import extract_checkpoints


def write_lines(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")


def snapshot_record(*, message_id: str, timestamp: str) -> dict:
    return {
        "type": "file-history-snapshot",
        "messageId": message_id,
        "snapshot": {"messageId": message_id, "trackedFileBackups": {}, "timestamp": timestamp},
        "isSnapshotUpdate": False,
    }


def delta_record(*, snapshot_message_id: str, tracking_path: str, timestamp: str) -> dict:
    return {
        "type": "file-history-delta",
        "messageId": "delta-msg",
        "snapshotMessageId": snapshot_message_id,
        "trackingPath": tracking_path,
        "backup": {
            "backupFileName": None,
            "version": 1,
            "backupTime": timestamp,
            "realParentDir": "/home/matt/project",
        },
        "timestamp": timestamp,
    }


def test_extract_checkpoints_creates_one_checkpoint_per_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    write_lines(
        path,
        [
            snapshot_record(message_id="msg-1", timestamp="2026-08-06T13:09:07.006Z"),
            snapshot_record(message_id="msg-2", timestamp="2026-08-06T14:00:00.000Z"),
        ],
    )

    checkpoints = extract_checkpoints(path)

    assert len(checkpoints) == 2
    assert checkpoints[0].message_id == "msg-1"
    assert checkpoints[0].timestamp == "2026-08-06T13:09:07.006Z"


def test_extract_checkpoints_attributes_deltas_to_their_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    write_lines(
        path,
        [
            snapshot_record(message_id="msg-1", timestamp="2026-08-06T13:00:00.000Z"),
            delta_record(
                snapshot_message_id="msg-1",
                tracking_path="CLAUDE.md",
                timestamp="2026-08-06T13:05:00.000Z",
            ),
            delta_record(
                snapshot_message_id="msg-1",
                tracking_path="README.md",
                timestamp="2026-08-06T13:06:00.000Z",
            ),
        ],
    )

    checkpoints = extract_checkpoints(path)

    assert checkpoints[0].changed_files == ["CLAUDE.md", "README.md"]


def test_extract_checkpoints_ignores_delta_for_unknown_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    write_lines(
        path,
        [delta_record(snapshot_message_id="ghost", tracking_path="x.md", timestamp="t")],
    )

    checkpoints = extract_checkpoints(path)

    assert checkpoints == []


def test_extract_checkpoints_skips_malformed_json_lines(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    good = json.dumps(snapshot_record(message_id="msg-1", timestamp="t"))
    path.write_text(f"{good}\nnot valid json\n")

    checkpoints = extract_checkpoints(path)

    assert len(checkpoints) == 1


def test_extract_checkpoints_ignores_unrelated_record_types(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    write_lines(path, [{"type": "assistant", "message": {}}])

    checkpoints = extract_checkpoints(path)

    assert checkpoints == []


def test_extract_checkpoints_returns_empty_list_for_missing_file(tmp_path: Path) -> None:
    checkpoints = extract_checkpoints(tmp_path / "does-not-exist.jsonl")

    assert checkpoints == []
