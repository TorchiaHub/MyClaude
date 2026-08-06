from pathlib import Path

from app.telemetry_reader.project_paths import encode_project_path, find_transcript_files


def test_encode_project_path_replaces_slashes() -> None:
    assert encode_project_path("/home/matt/Documents/MY_CLaude") == "-home-matt-Documents-MY-CLaude"


def test_encode_project_path_replaces_underscore_and_dot() -> None:
    assert encode_project_path("/home/matt/.claude-mem") == "-home-matt--claude-mem"


def test_encode_project_path_replaces_spaces_and_parens() -> None:
    path = "/home/matt/Documents/antonio/DiMarco_HR_Suite_Linux (2)/dimarco_linux"
    expected = "-home-matt-Documents-antonio-DiMarco-HR-Suite-Linux--2--dimarco-linux"

    assert encode_project_path(path) == expected


def test_find_transcript_files_returns_sorted_jsonl_paths(tmp_path: Path) -> None:
    projects_root = tmp_path / "projects"
    project_dir = projects_root / encode_project_path("/home/matt/my-project")
    project_dir.mkdir(parents=True)
    (project_dir / "b.jsonl").write_text("")
    (project_dir / "a.jsonl").write_text("")
    (project_dir / "notes.txt").write_text("")

    result = find_transcript_files(projects_root, "/home/matt/my-project")

    assert [p.name for p in result] == ["a.jsonl", "b.jsonl"]


def test_find_transcript_files_returns_empty_list_when_project_dir_missing(tmp_path: Path) -> None:
    result = find_transcript_files(tmp_path / "projects", "/home/matt/unknown")

    assert result == []
