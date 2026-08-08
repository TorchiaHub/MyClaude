from app.comparator.models import PACKAGE_NODE_TYPES, NodeTypeDiff, StaticDiff
from app.package_registry.models import Package

__all__ = ["StaticDiff", "NodeTypeDiff", "compare_static"]


def _names_by_type(package: Package) -> dict[str, set[str]]:
    names: dict[str, set[str]] = {node_type: set() for node_type in PACKAGE_NODE_TYPES}
    nodes = package.canvas_layout.get("nodes", [])
    if not isinstance(nodes, list):
        return names

    for node in nodes:
        if not isinstance(node, dict):
            continue
        data = node.get("data", {})
        node_type = data.get("nodeType")
        name = data.get("name")
        if node_type in names and isinstance(name, str):
            names[node_type].add(name)

    return names


def compare_static(package_a: Package, package_b: Package) -> StaticDiff:
    names_a = _names_by_type(package_a)
    names_b = _names_by_type(package_b)

    by_type = {}
    is_identical = True
    for node_type in PACKAGE_NODE_TYPES:
        a_set = names_a[node_type]
        b_set = names_b[node_type]
        only_in_a = sorted(a_set - b_set)
        only_in_b = sorted(b_set - a_set)
        common = sorted(a_set & b_set)
        if only_in_a or only_in_b:
            is_identical = False
        by_type[node_type] = NodeTypeDiff(only_in_a=only_in_a, only_in_b=only_in_b, common=common)

    return StaticDiff(
        package_a_id=package_a.id,
        package_b_id=package_b.id,
        by_type=by_type,
        is_identical=is_identical,
    )
