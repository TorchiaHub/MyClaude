import hashlib
import json
import sqlite3
import time
from pathlib import Path

from app.activation_engine.models import DeactivationResult, FileDiff
from app.json_store import read_json
from app.mcp_manager import add_server, remove_server
from app.package_registry import get_package
from app.package_registry.models import Package, Scope

__all__ = [
    "FileDiff",
    "DeactivationResult",
    "preview_activation",
    "activate_package",
    "deactivate_package",
    "list_active_package_ids",
]

FILE_UNIT_ROOTS = [
    Path(".claude/skills"),
    Path(".claude/agents"),
    Path(".claude/commands"),
    Path(".claude/rules"),
]

MCP_MANIFEST_PREFIX = ".mcp.json::"


def _collect_file_units(content_path: Path) -> list[tuple[str, Path]]:
    units = []
    for root in FILE_UNIT_ROOTS:
        source_root = content_path / root
        if not source_root.is_dir():
            continue
        for file in sorted(source_root.rglob("*")):
            if file.is_file():
                relative = file.relative_to(content_path)
                units.append((relative.as_posix(), file))

    claude_md = content_path / "CLAUDE.md"
    if claude_md.is_file():
        units.append(("CLAUDE.md", claude_md))

    return units


def _collect_mcp_servers(content_path: Path) -> dict[str, dict]:
    return read_json(content_path / ".mcp.json").get("mcpServers", {})


def _resolve_target_relative_path(content_relative_path: str, scope: Scope) -> str:
    """Map a package-content-relative path to its real Claude Code target path.

    Package content always mirrors the project-scope convention (files nested
    under a literal ".claude/" prefix, e.g. ".claude/skills/x/SKILL.md"). For
    project scope the real target IS "<project>/.claude/skills/x/SKILL.md", so
    the prefix is kept. For global scope there is no nested ".claude/" — the
    real target root (~/.claude) already *is* the ".claude" directory, so the
    prefix must be stripped or activation would write to ~/.claude/.claude/...
    """
    if scope == "global" and content_relative_path.startswith(".claude/"):
        return content_relative_path[len(".claude/") :]
    return content_relative_path


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_mcp_config(config: dict) -> str:
    return _hash_bytes(json.dumps(config, sort_keys=True).encode())


def preview_activation(package: Package, target_root: Path) -> list[FileDiff]:
    diffs = []
    for relative_path, source_path in _collect_file_units(package.content_path):
        target_path = target_root / _resolve_target_relative_path(relative_path, package.scope)
        new_bytes = source_path.read_bytes()
        if not target_path.is_file():
            diffs.append(FileDiff(relative_path, "create"))
        elif target_path.read_bytes() == new_bytes:
            diffs.append(FileDiff(relative_path, "overwrite_identical"))
        else:
            diffs.append(FileDiff(relative_path, "overwrite_conflict"))
    return diffs


def list_active_package_ids(conn: sqlite3.Connection, *, project_path: str | None) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT package_id FROM written_files WHERE project_path IS ?", (project_path,)
    ).fetchall()
    return [row["package_id"] for row in rows]


def activate_package(
    conn: sqlite3.Connection, package: Package, target_root: Path, mcp_target_path: Path
) -> None:
    if package.scope == "global":
        _deactivate_other_global_packages(conn, package.id, target_root, mcp_target_path)

    for relative_path, source_path in _collect_file_units(package.content_path):
        target_path = target_root / _resolve_target_relative_path(relative_path, package.scope)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        content = source_path.read_bytes()
        target_path.write_bytes(content)
        _record_written_file(conn, package, relative_path, _hash_bytes(content))

    for name, config in _collect_mcp_servers(package.content_path).items():
        add_server(mcp_target_path, name, config)
        _record_written_file(
            conn, package, f"{MCP_MANIFEST_PREFIX}{name}", _hash_mcp_config(config)
        )

    conn.execute(
        "INSERT INTO activation_log (package_id, project_path, action, occurred_at) "
        "VALUES (?, ?, 'activate', ?)",
        (package.id, package.project_path, int(time.time())),
    )
    conn.commit()


def deactivate_package(
    conn: sqlite3.Connection, package: Package, target_root: Path, mcp_target_path: Path
) -> DeactivationResult:
    rows = conn.execute(
        "SELECT file_path, content_hash FROM written_files WHERE package_id = ? AND project_path IS ?",
        (package.id, package.project_path),
    ).fetchall()

    result = DeactivationResult()
    for row in rows:
        file_path = row["file_path"]
        expected_hash = row["content_hash"]

        if file_path.startswith(MCP_MANIFEST_PREFIX):
            server_name = file_path[len(MCP_MANIFEST_PREFIX) :]
            _deactivate_mcp_server(mcp_target_path, server_name, expected_hash, file_path, result)
        else:
            target_relative = _resolve_target_relative_path(file_path, package.scope)
            _deactivate_file(target_root / target_relative, expected_hash, file_path, result)

        conn.execute(
            "DELETE FROM written_files WHERE package_id = ? AND project_path IS ? AND file_path = ?",
            (package.id, package.project_path, file_path),
        )

    conn.execute(
        "INSERT INTO activation_log (package_id, project_path, action, occurred_at) "
        "VALUES (?, ?, 'deactivate', ?)",
        (package.id, package.project_path, int(time.time())),
    )
    conn.commit()
    return result


def _deactivate_file(
    target_path: Path, expected_hash: str, file_path: str, result: DeactivationResult
) -> None:
    if not target_path.is_file():
        return
    if _hash_bytes(target_path.read_bytes()) == expected_hash:
        target_path.unlink()
        result.removed.append(file_path)
    else:
        result.preserved.append(file_path)


def _deactivate_mcp_server(
    mcp_target_path: Path,
    server_name: str,
    expected_hash: str,
    file_path: str,
    result: DeactivationResult,
) -> None:
    current = read_json(mcp_target_path).get("mcpServers", {}).get(server_name)
    if current is None:
        return
    if _hash_mcp_config(current) == expected_hash:
        remove_server(mcp_target_path, server_name)
        result.removed.append(file_path)
    else:
        result.preserved.append(file_path)


def _record_written_file(
    conn: sqlite3.Connection, package: Package, file_path: str, content_hash: str
) -> None:
    conn.execute(
        """
        INSERT INTO written_files (package_id, project_path, file_path, content_hash)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(package_id, project_path, file_path)
        DO UPDATE SET content_hash = excluded.content_hash
        """,
        (package.id, package.project_path, file_path, content_hash),
    )


def _deactivate_other_global_packages(
    conn: sqlite3.Connection, current_package_id: str, target_root: Path, mcp_target_path: Path
) -> None:
    other_ids = [
        pid for pid in list_active_package_ids(conn, project_path=None) if pid != current_package_id
    ]
    for other_id in other_ids:
        other_package = get_package(conn, other_id)
        if other_package is not None:
            deactivate_package(conn, other_package, target_root, mcp_target_path)
