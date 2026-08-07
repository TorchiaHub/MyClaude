from dataclasses import dataclass
from pathlib import Path

from app.json_store import read_json


@dataclass(frozen=True)
class SandboxConfig:
    enabled: bool
    raw_config: dict
    auto_allow_bash_if_sandboxed: bool | None


def read_sandbox_config(settings_path: Path) -> SandboxConfig:
    """Read-only view of the OS-level sandboxing config (allowlist of
    filesystem/network access enforced on the Bash tool and its children —
    orthogonal to the allow/deny/ask permission rules).

    No exact `sandbox` key schema is verified against a real local
    settings.json on this machine (sandboxing isn't configured here), so
    this deliberately passes the raw object through rather than assuming
    a specific shape.
    """
    data = read_json(settings_path)
    raw_config = data.get("sandbox", {})
    return SandboxConfig(
        enabled=bool(raw_config),
        raw_config=raw_config,
        auto_allow_bash_if_sandboxed=data.get("autoAllowBashIfSandboxed"),
    )
