from pathlib import Path

from app.comparator import compare_static
from app.package_registry.models import Package


def make_package(package_id: str, canvas_nodes: list[dict]) -> Package:
    return Package(
        id=package_id,
        name=package_id,
        version="1.0.0",
        scope="global",
        project_path=None,
        content_path=Path(f"/fake/{package_id}"),
        folder=None,
        description="",
        updated_at=0,
        canvas_layout={"nodes": canvas_nodes, "edges": []},
    )


def node(node_type: str, name: str) -> dict:
    return {
        "id": f"{node_type}-{name}",
        "type": "packageNode",
        "data": {"nodeType": node_type, "name": name},
    }


def test_compare_static_reports_nodes_only_in_a() -> None:
    package_a = make_package("pkg-a", [node("skill", "deploy"), node("skill", "review")])
    package_b = make_package("pkg-b", [node("skill", "deploy")])

    diff = compare_static(package_a, package_b)

    assert diff.by_type["skill"].only_in_a == ["review"]
    assert diff.by_type["skill"].only_in_b == []
    assert diff.by_type["skill"].common == ["deploy"]


def test_compare_static_reports_nodes_only_in_b() -> None:
    package_a = make_package("pkg-a", [node("mcp", "ollama")])
    package_b = make_package("pkg-b", [node("mcp", "ollama"), node("mcp", "db")])

    diff = compare_static(package_a, package_b)

    assert diff.by_type["mcp"].only_in_b == ["db"]


def test_compare_static_covers_all_node_types_even_when_empty() -> None:
    package_a = make_package("pkg-a", [])
    package_b = make_package("pkg-b", [])

    diff = compare_static(package_a, package_b)

    assert set(diff.by_type.keys()) == {"skill", "agent", "command", "mcp", "rule", "prompt"}
    for type_diff in diff.by_type.values():
        assert type_diff.only_in_a == []
        assert type_diff.only_in_b == []
        assert type_diff.common == []


def test_compare_static_identical_packages_have_no_differences() -> None:
    nodes = [node("skill", "deploy"), node("agent", "reviewer")]
    package_a = make_package("pkg-a", nodes)
    package_b = make_package("pkg-b", nodes)

    diff = compare_static(package_a, package_b)

    assert diff.is_identical is True


def test_compare_static_different_packages_are_not_identical() -> None:
    package_a = make_package("pkg-a", [node("skill", "deploy")])
    package_b = make_package("pkg-b", [node("skill", "other")])

    diff = compare_static(package_a, package_b)

    assert diff.is_identical is False


def test_compare_static_handles_malformed_canvas_layout_gracefully() -> None:
    package_a = make_package("pkg-a", [{"id": "weird", "data": {}}])
    package_b = make_package("pkg-b", [])

    diff = compare_static(package_a, package_b)

    assert diff.is_identical is True
