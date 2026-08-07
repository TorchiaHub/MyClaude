from dataclasses import dataclass, field
from typing import Literal

DiffAction = Literal["create", "overwrite_identical", "overwrite_conflict"]


@dataclass(frozen=True)
class FileDiff:
    relative_path: str
    action: DiffAction


@dataclass(frozen=True)
class DeactivationResult:
    removed: list[str] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
