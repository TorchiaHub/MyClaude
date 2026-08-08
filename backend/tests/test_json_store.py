from pathlib import Path

import pytest

from app.json_store import read_json, write_json


def test_write_json_then_read_json_roundtrips(tmp_path: Path) -> None:
    path = tmp_path / "config.json"

    write_json(path, {"mcpServers": {"ollama": {"command": "ollama"}}})

    assert read_json(path) == {"mcpServers": {"ollama": {"command": "ollama"}}}


def test_write_json_creates_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "dir" / "config.json"

    write_json(path, {"a": 1})

    assert path.is_file()


def test_write_json_does_not_leave_temp_files_behind(tmp_path: Path) -> None:
    path = tmp_path / "config.json"

    write_json(path, {"a": 1})

    assert list(tmp_path.iterdir()) == [path]


def test_write_json_replaces_existing_file_atomically(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    write_json(path, {"a": 1})

    write_json(path, {"a": 2})

    assert read_json(path) == {"a": 2}
    assert list(tmp_path.iterdir()) == [path]


def test_write_json_preserves_original_content_if_serialization_fails(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    write_json(path, {"a": 1})

    class Unserializable:
        pass

    with pytest.raises(TypeError):
        write_json(path, {"a": Unserializable()})

    assert read_json(path) == {"a": 1}
    assert list(tmp_path.iterdir()) == [path]


def test_write_json_leaves_original_file_intact_if_final_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Proves the write goes through a temp file + os.replace: if the final
    replace step fails (simulating an interruption), the real config file
    that Claude Code reads must be left exactly as it was, never partially
    overwritten or truncated."""
    path = tmp_path / "config.json"
    write_json(path, {"a": 1})

    def failing_replace(src: str, dst: str) -> None:
        raise OSError("simulated crash during replace")

    monkeypatch.setattr("app.json_store.os.replace", failing_replace)

    with pytest.raises(OSError):
        write_json(path, {"a": 2})

    assert read_json(path) == {"a": 1}
    assert list(tmp_path.iterdir()) == [path]
