import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.package_registry.models import Package

__all__ = ["sanitize_mcp_config", "sanitize_text", "build_export_bundle"]

REDACTED = "<REDACTED>"
HOME_PLACEHOLDER = "<HOME>"

_SENSITIVE_KEY_PATTERN = re.compile(r"(key|token|secret|password|credential|auth)", re.IGNORECASE)
_REDACTABLE_CONFIG_KEYS = ("env", "headers")


def _sanitize_arg(arg: str) -> str:
    if "=" not in arg:
        return arg
    flag, _, value = arg.partition("=")
    if _SENSITIVE_KEY_PATTERN.search(flag.lstrip("-")):
        return f"{flag}={REDACTED}"
    return arg


def _sanitize_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url
    sanitized_pairs = [
        (k, REDACTED if _SENSITIVE_KEY_PATTERN.search(k) else v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
    ]
    return urlunsplit(parts._replace(query=urlencode(sanitized_pairs)))


def sanitize_mcp_config(config: dict) -> dict:
    sanitized = json.loads(json.dumps(config))
    for key in _REDACTABLE_CONFIG_KEYS:
        values = sanitized.get(key)
        if isinstance(values, dict):
            sanitized[key] = {
                k: (REDACTED if _SENSITIVE_KEY_PATTERN.search(k) else v) for k, v in values.items()
            }

    args = sanitized.get("args")
    if isinstance(args, list):
        sanitized["args"] = [_sanitize_arg(a) if isinstance(a, str) else a for a in args]

    url = sanitized.get("url")
    if isinstance(url, str):
        sanitized["url"] = _sanitize_url(url)

    return sanitized


def sanitize_text(text: str, home: Path) -> str:
    return text.replace(str(home), HOME_PLACEHOLDER)


def _sanitize_file_content(relative_path: str, content: str, home: Path) -> str:
    if relative_path.endswith(".mcp.json"):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return sanitize_text(content, home)
        if not isinstance(data, dict) or not isinstance(data.get("mcpServers"), dict):
            return sanitize_text(content, home)
        sanitized_servers = {
            name: (sanitize_mcp_config(cfg) if isinstance(cfg, dict) else cfg)
            for name, cfg in data["mcpServers"].items()
        }
        serialized = json.dumps({**data, "mcpServers": sanitized_servers}, indent=2)
        return sanitize_text(serialized, home)
    return sanitize_text(content, home)


def build_export_bundle(content_path: Path, package: Package, home: Path) -> dict:
    files: dict[str, str] = {}
    for file_path in sorted(content_path.rglob("*")):
        if file_path.is_dir():
            continue
        relative = file_path.relative_to(content_path).as_posix()
        if relative == "package.json":
            continue
        try:
            content = file_path.read_text()
        except UnicodeDecodeError:
            continue
        files[relative] = _sanitize_file_content(relative, content, home)

    return {
        "id": package.id,
        "name": package.name,
        "version": package.version,
        "scope": package.scope,
        "description": package.description,
        "folder": package.folder,
        "canvas_layout": package.canvas_layout,
        "files": files,
    }
