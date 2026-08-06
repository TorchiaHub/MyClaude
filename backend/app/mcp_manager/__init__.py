import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.json_store import read_json, write_json

Scope = Literal["global", "project"]


@dataclass(frozen=True)
class McpServerEntry:
    name: str
    scope: Scope
    config: dict


@dataclass(frozen=True)
class ReachabilityResult:
    reachable: bool
    detail: str


def list_servers(global_config_path: Path, project_mcp_path: Path | None) -> list[McpServerEntry]:
    entries = [
        McpServerEntry(name=name, scope="global", config=config)
        for name, config in read_json(global_config_path).get("mcpServers", {}).items()
    ]

    if project_mcp_path is not None:
        entries += [
            McpServerEntry(name=name, scope="project", config=config)
            for name, config in read_json(project_mcp_path).get("mcpServers", {}).items()
        ]

    return entries


def add_server(config_path: Path, name: str, config: dict) -> None:
    data = read_json(config_path)
    data.setdefault("mcpServers", {})[name] = config
    write_json(config_path, data)


def remove_server(config_path: Path, name: str) -> bool:
    data = read_json(config_path)
    servers = data.get("mcpServers", {})
    if name not in servers:
        return False
    del servers[name]
    write_json(config_path, data)
    return True


def check_reachability(
    config: dict,
    *,
    http_get: Callable[[str, float], object] | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> ReachabilityResult:
    server_type = config.get("type")
    has_url = "url" in config

    if server_type is None:
        if has_url:
            return ReachabilityResult(
                False, 'Config con "url" ma senza "type": configurazione non valida.'
            )
        server_type = "stdio"

    if server_type == "stdio":
        return _check_stdio_reachability(config, which)

    if server_type in ("http", "sse"):
        return _check_http_reachability(config, http_get or _default_http_get)

    return ReachabilityResult(
        False, f"Test di raggiungibilità non supportato per il tipo '{server_type}'."
    )


def _check_stdio_reachability(
    config: dict, which: Callable[[str], str | None]
) -> ReachabilityResult:
    command = config.get("command")
    if not command:
        return ReachabilityResult(False, "Nessun comando stdio configurato.")

    command_path = Path(command)
    resolved = command if command_path.is_absolute() and command_path.exists() else which(command)
    if resolved:
        return ReachabilityResult(True, f"Comando trovato: {resolved}")
    return ReachabilityResult(False, f"Comando '{command}' non trovato nel PATH.")


def _check_http_reachability(
    config: dict, http_get: Callable[[str, float], object]
) -> ReachabilityResult:
    url = config.get("url")
    if not url:
        return ReachabilityResult(False, "Nessun url configurato.")

    try:
        http_get(url, 3.0)
    except Exception as exc:
        return ReachabilityResult(False, f"Connessione fallita: {exc}")
    return ReachabilityResult(True, "Connessione riuscita.")


def _default_http_get(url: str, timeout: float) -> object:
    import httpx

    return httpx.get(url, timeout=timeout)
