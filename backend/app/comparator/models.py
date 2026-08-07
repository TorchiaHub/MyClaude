from dataclasses import dataclass, field

PACKAGE_NODE_TYPES = ("skill", "agent", "command", "mcp", "rule", "prompt")


@dataclass(frozen=True)
class NodeTypeDiff:
    only_in_a: list[str] = field(default_factory=list)
    only_in_b: list[str] = field(default_factory=list)
    common: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StaticDiff:
    package_a_id: str
    package_b_id: str
    by_type: dict[str, NodeTypeDiff]
    is_identical: bool
