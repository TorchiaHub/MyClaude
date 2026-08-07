import re
import shutil
import sqlite3
import time
from pathlib import Path

from app.json_store import read_json, write_json
from app.package_registry.models import Package, PackageNode, Scope

__all__ = [
    "Package",
    "PackageNode",
    "InvalidPackageIdentifierError",
    "resolve_content_path",
    "create_package",
    "import_package",
    "get_package",
    "list_packages",
    "delete_package",
]

# A single safe path segment: no "/", no leading "." (blocks ".", "..", and
# hidden-file tricks), alphanumeric plus a conservative punctuation set.
_SAFE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

# Node types whose `name` is used to build a filesystem path during
# materialization and therefore must be validated the same way as package ids.
_PATH_DERIVED_NODE_TYPES = {"skill", "agent", "command", "rule"}


class InvalidPackageIdentifierError(ValueError):
    pass


def _validate_safe_identifier(value: str, *, label: str) -> None:
    if not _SAFE_IDENTIFIER_PATTERN.match(value):
        raise InvalidPackageIdentifierError(
            f"{label} '{value}' is not a safe identifier: only letters, digits, '.', '_', '-' "
            "are allowed, and it cannot start with '.'"
        )


def resolve_content_path(
    control_plane_home: Path, *, scope: Scope, project_path: str | None, package_id: str
) -> Path:
    _validate_safe_identifier(package_id, label="package id")
    if scope == "global":
        return control_plane_home / "global-packages" / package_id

    if not project_path or not Path(project_path).is_absolute():
        raise InvalidPackageIdentifierError(
            f"project_path '{project_path}' must be an absolute path for scope='project'"
        )
    return Path(project_path) / ".claude-control-plane" / "packages" / package_id


def create_package(
    control_plane_home: Path,
    conn: sqlite3.Connection,
    *,
    id: str,
    name: str,
    version: str,
    scope: Scope,
    project_path: str | None,
    folder: str | None,
    description: str,
    nodes: list[PackageNode],
    canvas_layout: dict,
) -> Package:
    content_path = resolve_content_path(
        control_plane_home, scope=scope, project_path=project_path, package_id=id
    )
    content_path.mkdir(parents=True, exist_ok=True)

    for node in nodes:
        _materialize_node(content_path, node)

    updated_at = int(time.time())
    write_json(
        content_path / "package.json",
        {
            "id": id,
            "name": name,
            "version": version,
            "scope": scope,
            "description": description,
            "folder": folder,
            "canvas_layout": canvas_layout,
        },
    )

    _upsert_package_row(
        conn,
        id=id,
        name=name,
        version=version,
        scope=scope,
        project_path=project_path,
        content_path=content_path,
        folder=folder,
        updated_at=updated_at,
    )

    return Package(
        id=id,
        name=name,
        version=version,
        scope=scope,
        project_path=project_path,
        content_path=content_path,
        folder=folder,
        description=description,
        updated_at=updated_at,
        canvas_layout=canvas_layout,
    )


def import_package(
    control_plane_home: Path,
    conn: sqlite3.Connection,
    *,
    bundle: dict,
    id: str,
    scope: Scope,
    project_path: str | None,
    folder: str | None = None,
) -> Package:
    content_path = resolve_content_path(
        control_plane_home, scope=scope, project_path=project_path, package_id=id
    )
    content_path.mkdir(parents=True, exist_ok=True)

    for relative_path, content in bundle.get("files", {}).items():
        _write_bundle_file(content_path, relative_path, content)

    name = bundle.get("name", id)
    version = bundle.get("version", "0.0.0")
    description = bundle.get("description", "")
    canvas_layout = bundle.get("canvas_layout", {})
    resolved_folder = folder if folder is not None else bundle.get("folder")
    updated_at = int(time.time())

    write_json(
        content_path / "package.json",
        {
            "id": id,
            "name": name,
            "version": version,
            "scope": scope,
            "description": description,
            "folder": resolved_folder,
            "canvas_layout": canvas_layout,
        },
    )

    _upsert_package_row(
        conn,
        id=id,
        name=name,
        version=version,
        scope=scope,
        project_path=project_path,
        content_path=content_path,
        folder=resolved_folder,
        updated_at=updated_at,
    )

    return Package(
        id=id,
        name=name,
        version=version,
        scope=scope,
        project_path=project_path,
        content_path=content_path,
        folder=resolved_folder,
        description=description,
        updated_at=updated_at,
        canvas_layout=canvas_layout,
    )


def _upsert_package_row(
    conn: sqlite3.Connection,
    *,
    id: str,
    name: str,
    version: str,
    scope: Scope,
    project_path: str | None,
    content_path: Path,
    folder: str | None,
    updated_at: int,
) -> None:
    conn.execute(
        """
        INSERT INTO packages (id, name, version, scope, project_path, content_path, folder, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name, version=excluded.version, scope=excluded.scope,
            project_path=excluded.project_path, content_path=excluded.content_path,
            folder=excluded.folder, updated_at=excluded.updated_at
        """,
        (id, name, version, scope, project_path, str(content_path), folder, updated_at),
    )
    conn.commit()


def _write_bundle_file(content_path: Path, relative_path: str, content: str) -> None:
    if Path(relative_path).is_absolute():
        raise InvalidPackageIdentifierError(f"Bundle file path '{relative_path}' must be relative")

    target = (content_path / relative_path).resolve()
    if not target.is_relative_to(content_path.resolve()):
        raise InvalidPackageIdentifierError(
            f"Bundle file path '{relative_path}' escapes the package content directory"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def get_package(conn: sqlite3.Connection, package_id: str) -> Package | None:
    row = conn.execute("SELECT * FROM packages WHERE id = ?", (package_id,)).fetchone()
    if row is None:
        return None
    return _package_from_row(row)


def list_packages(conn: sqlite3.Connection) -> list[Package]:
    rows = conn.execute("SELECT * FROM packages ORDER BY updated_at DESC").fetchall()
    return [_package_from_row(row) for row in rows]


def delete_package(conn: sqlite3.Connection, package_id: str) -> None:
    row = conn.execute("SELECT content_path FROM packages WHERE id = ?", (package_id,)).fetchone()
    if row is not None:
        shutil.rmtree(Path(row["content_path"]), ignore_errors=True)
    conn.execute("DELETE FROM packages WHERE id = ?", (package_id,))
    conn.commit()


def _package_from_row(row: sqlite3.Row) -> Package:
    content_path = Path(row["content_path"])
    manifest = read_json(content_path / "package.json")
    return Package(
        id=row["id"],
        name=row["name"],
        version=row["version"],
        scope=row["scope"],
        project_path=row["project_path"],
        content_path=content_path,
        folder=row["folder"],
        description=manifest.get("description", ""),
        updated_at=row["updated_at"],
        canvas_layout=manifest.get("canvas_layout", {}),
    )


def _materialize_node(content_path: Path, node: PackageNode) -> None:
    if node.type in _PATH_DERIVED_NODE_TYPES:
        _validate_safe_identifier(node.name, label=f"{node.type} node name")

    if node.type == "skill":
        _copy_tree(Path(node.source_path), content_path / ".claude" / "skills" / node.name)
    elif node.type == "agent":
        _copy_file(Path(node.source_path), content_path / ".claude" / "agents" / f"{node.name}.md")
    elif node.type == "command":
        _copy_file(
            Path(node.source_path), content_path / ".claude" / "commands" / f"{node.name}.md"
        )
    elif node.type == "mcp":
        _merge_mcp_server(content_path / ".mcp.json", node.name, node.config or {})
    elif node.type == "rule":
        _write_text(content_path / ".claude" / "rules" / f"{node.name}.md", node.content or "")
    elif node.type == "prompt":
        _append_text(content_path / "CLAUDE.md", node.content or "")


def _copy_tree(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _merge_mcp_server(mcp_json_path: Path, name: str, config: dict) -> None:
    data = read_json(mcp_json_path)
    data.setdefault("mcpServers", {})[name] = config
    write_json(mcp_json_path, data)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(content + "\n")
