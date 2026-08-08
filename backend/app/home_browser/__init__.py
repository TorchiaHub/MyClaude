import shutil
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "PathEscapesRootError",
    "RootEntryError",
    "FileEntry",
    "list_directory",
    "read_file_preview",
    "rename_entry",
    "delete_entry",
    "move_entry",
]


class PathEscapesRootError(ValueError):
    pass


class RootEntryError(ValueError):
    pass


@dataclass(frozen=True)
class FileEntry:
    name: str
    is_dir: bool
    size: int


def _resolve_safe_path(root: Path, relative_path: str) -> Path:
    resolved_root = root.resolve()
    candidate = (resolved_root / relative_path).resolve() if relative_path else resolved_root
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise PathEscapesRootError(f"Path '{relative_path}' resolves outside the browsing root")
    return candidate


def _require_not_root(resolved_root: Path, candidate: Path) -> None:
    if candidate == resolved_root:
        raise RootEntryError("This operation cannot target the browsing root itself")


def _points_outside_root(resolved_root: Path, path: Path) -> bool:
    resolved = path.resolve()
    return resolved != resolved_root and resolved_root not in resolved.parents


def list_directory(root: Path, relative_path: str) -> list[FileEntry]:
    directory = _resolve_safe_path(root, relative_path)
    resolved_root = root.resolve()
    entries = []
    for child in sorted(directory.iterdir(), key=lambda p: p.name):
        if child.is_symlink() and _points_outside_root(resolved_root, child):
            entries.append(FileEntry(name=child.name, is_dir=False, size=child.lstat().st_size))
        else:
            entries.append(
                FileEntry(name=child.name, is_dir=child.is_dir(), size=child.stat().st_size)
            )
    return entries


def read_file_preview(root: Path, relative_path: str, max_bytes: int) -> str:
    target = _resolve_safe_path(root, relative_path)
    return target.read_text(errors="replace")[:max_bytes]


def rename_entry(root: Path, relative_path: str, new_name: str) -> Path:
    resolved_root = root.resolve()
    source = _resolve_safe_path(root, relative_path)
    _require_not_root(resolved_root, source)
    destination = _resolve_safe_path(root, str(Path(relative_path).parent / new_name))
    source.rename(destination)
    return destination


def delete_entry(root: Path, relative_path: str) -> None:
    resolved_root = root.resolve()
    target = _resolve_safe_path(root, relative_path)
    _require_not_root(resolved_root, target)
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()


def move_entry(root: Path, relative_path: str, new_relative_path: str) -> Path:
    resolved_root = root.resolve()
    source = _resolve_safe_path(root, relative_path)
    _require_not_root(resolved_root, source)
    destination = _resolve_safe_path(root, new_relative_path)
    _require_not_root(resolved_root, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.rename(destination)
    return destination
