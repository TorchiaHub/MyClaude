from dataclasses import dataclass, field
from typing import Literal

ResourceType = Literal["skill", "agent", "command", "output_style"]
Scope = Literal["user", "project"]


@dataclass(frozen=True)
class LibraryItem:
    id: str
    resource_type: ResourceType
    scope: Scope
    name: str
    description: str
    folder: str
    path: str
    tags: list[str] = field(default_factory=list)
