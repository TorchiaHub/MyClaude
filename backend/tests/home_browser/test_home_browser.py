from pathlib import Path

import pytest

from app.home_browser import (
    PathEscapesRootError,
    RootEntryError,
    delete_entry,
    list_directory,
    move_entry,
    read_file_preview,
    rename_entry,
)


def test_list_directory_lists_immediate_children_only(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("hello")
    (tmp_path / "skills").mkdir()
    (tmp_path / "skills" / "deploy").mkdir()

    entries = list_directory(tmp_path, "")

    names = {e.name for e in entries}
    assert names == {"CLAUDE.md", "skills"}
    assert not any(e.name == "deploy" for e in entries)


def test_list_directory_reports_is_dir_and_size(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("12345")
    (tmp_path / "folder").mkdir()

    entries = {e.name: e for e in list_directory(tmp_path, "")}

    assert entries["file.txt"].is_dir is False
    assert entries["file.txt"].size == 5
    assert entries["folder"].is_dir is True


def test_list_directory_on_nested_relative_path(tmp_path: Path) -> None:
    (tmp_path / "skills" / "deploy").mkdir(parents=True)
    (tmp_path / "skills" / "deploy" / "SKILL.md").write_text("---\nname: deploy\n---\n")

    entries = list_directory(tmp_path, "skills/deploy")

    assert [e.name for e in entries] == ["SKILL.md"]


def test_list_directory_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathEscapesRootError):
        list_directory(tmp_path, "../../etc")


def test_list_directory_does_not_leak_metadata_of_symlink_target_outside_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "claude-home"
    root.mkdir()
    outside_secret = tmp_path / "outside_secret.txt"
    outside_secret.write_text("s" * 9999)
    (root / "evil_link").symlink_to(outside_secret)

    entries = {e.name: e for e in list_directory(root, "")}

    assert entries["evil_link"].size != 9999
    assert entries["evil_link"].is_dir is False


def test_read_file_preview_returns_text_content(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# Hello\nWorld")

    content = read_file_preview(tmp_path, "CLAUDE.md", max_bytes=1000)

    assert content == "# Hello\nWorld"


def test_read_file_preview_truncates_to_max_bytes(tmp_path: Path) -> None:
    (tmp_path / "big.md").write_text("a" * 100)

    content = read_file_preview(tmp_path, "big.md", max_bytes=10)

    assert len(content) == 10


def test_read_file_preview_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathEscapesRootError):
        read_file_preview(tmp_path, "../../../etc/passwd", max_bytes=100)


def test_rename_entry_renames_file_in_place(tmp_path: Path) -> None:
    (tmp_path / "old.md").write_text("content")

    rename_entry(tmp_path, "old.md", "new.md")

    assert not (tmp_path / "old.md").exists()
    assert (tmp_path / "new.md").read_text() == "content"


def test_rename_entry_rejects_root(tmp_path: Path) -> None:
    with pytest.raises(RootEntryError):
        rename_entry(tmp_path, "", "renamed-root")


@pytest.mark.parametrize("root_equivalent", ["./", ".//", "././", "sub/..", "a/../."])
def test_rename_entry_rejects_forms_that_resolve_to_root(
    tmp_path: Path, root_equivalent: str
) -> None:
    with pytest.raises(RootEntryError):
        rename_entry(tmp_path, root_equivalent, "renamed-root")


def test_rename_entry_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathEscapesRootError):
        rename_entry(tmp_path, "../outside.md", "new.md")


def test_rename_entry_rejects_new_name_that_is_a_path(tmp_path: Path) -> None:
    (tmp_path / "old.md").write_text("content")

    with pytest.raises(PathEscapesRootError):
        rename_entry(tmp_path, "old.md", "../escaped.md")


def test_delete_entry_removes_file(tmp_path: Path) -> None:
    (tmp_path / "gone.md").write_text("bye")

    delete_entry(tmp_path, "gone.md")

    assert not (tmp_path / "gone.md").exists()


def test_delete_entry_removes_directory_recursively(tmp_path: Path) -> None:
    (tmp_path / "skills" / "deploy").mkdir(parents=True)
    (tmp_path / "skills" / "deploy" / "SKILL.md").write_text("x")

    delete_entry(tmp_path, "skills/deploy")

    assert not (tmp_path / "skills" / "deploy").exists()


def test_delete_entry_rejects_root(tmp_path: Path) -> None:
    with pytest.raises(RootEntryError):
        delete_entry(tmp_path, "")


@pytest.mark.parametrize("root_equivalent", ["./", ".//", "././", "sub/..", "a/../."])
def test_delete_entry_rejects_forms_that_resolve_to_root(
    tmp_path: Path, root_equivalent: str
) -> None:
    (tmp_path / "sub").mkdir(exist_ok=True)
    (tmp_path / "a").mkdir(exist_ok=True)
    (tmp_path / "keep.md").write_text("must survive")

    with pytest.raises(RootEntryError):
        delete_entry(tmp_path, root_equivalent)

    assert (tmp_path / "keep.md").exists()


def test_delete_entry_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathEscapesRootError):
        delete_entry(tmp_path, "../outside.md")


def test_move_entry_moves_file_to_new_parent(tmp_path: Path) -> None:
    (tmp_path / "loose.md").write_text("content")
    (tmp_path / "archive").mkdir()

    move_entry(tmp_path, "loose.md", "archive/loose.md")

    assert not (tmp_path / "loose.md").exists()
    assert (tmp_path / "archive" / "loose.md").read_text() == "content"


def test_move_entry_rejects_root(tmp_path: Path) -> None:
    with pytest.raises(RootEntryError):
        move_entry(tmp_path, "", "elsewhere")


def test_move_entry_rejects_destination_that_resolves_to_root(tmp_path: Path) -> None:
    (tmp_path / "loose.md").write_text("content")

    with pytest.raises(RootEntryError):
        move_entry(tmp_path, "loose.md", "./")


def test_move_entry_rejects_source_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathEscapesRootError):
        move_entry(tmp_path, "../outside.md", "inside.md")


def test_move_entry_rejects_destination_path_traversal(tmp_path: Path) -> None:
    (tmp_path / "inside.md").write_text("content")

    with pytest.raises(PathEscapesRootError):
        move_entry(tmp_path, "inside.md", "../outside.md")
