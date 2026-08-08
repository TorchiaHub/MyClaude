from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

NodeType = Literal["skill", "agent", "command", "mcp", "rule", "prompt"]
Scope = Literal["global", "project"]


@dataclass(frozen=True)
class PackageNode:
    type: NodeType
    name: str
    source_path: str | None = None
    config: dict | None = None
    content: str | None = None


@dataclass(frozen=True)
class Package:
    id: str
    name: str
    version: str
    scope: Scope
    project_path: str | None
    content_path: Path
    folder: str | None
    description: str
    updated_at: int
    canvas_layout: dict = field(default_factory=dict)
