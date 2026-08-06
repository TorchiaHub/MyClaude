import json
from pathlib import Path

from app.mcp_manager import (
    McpServerEntry,
    add_server,
    check_reachability,
    list_servers,
    remove_server,
)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_list_servers_combines_global_and_project_scope(tmp_path: Path) -> None:
    global_path = tmp_path / ".claude.json"
    project_path = tmp_path / ".mcp.json"
    write_json(global_path, {"mcpServers": {"ollama": {"command": "ollama"}}})
    write_json(project_path, {"mcpServers": {"db": {"type": "stdio", "command": "dbhub"}}})

    result = list_servers(global_path, project_path)

    assert McpServerEntry(name="ollama", scope="global", config={"command": "ollama"}) in result
    assert (
        McpServerEntry(name="db", scope="project", config={"type": "stdio", "command": "dbhub"})
        in result
    )


def test_list_servers_returns_empty_when_no_files(tmp_path: Path) -> None:
    result = list_servers(tmp_path / "missing.json", tmp_path / "missing-mcp.json")

    assert result == []


def test_list_servers_without_project_path_returns_only_global(tmp_path: Path) -> None:
    global_path = tmp_path / ".claude.json"
    write_json(global_path, {"mcpServers": {"ollama": {"command": "ollama"}}})

    result = list_servers(global_path, None)

    assert result == [McpServerEntry(name="ollama", scope="global", config={"command": "ollama"})]


def test_add_server_creates_file_with_entry(tmp_path: Path) -> None:
    config_path = tmp_path / ".mcp.json"

    add_server(config_path, "db", {"type": "stdio", "command": "dbhub"})

    data = json.loads(config_path.read_text())
    assert data["mcpServers"]["db"] == {"type": "stdio", "command": "dbhub"}


def test_add_server_preserves_other_top_level_keys(tmp_path: Path) -> None:
    config_path = tmp_path / ".claude.json"
    write_json(config_path, {"projects": {"/some/path": {}}})

    add_server(config_path, "ollama", {"command": "ollama"})

    data = json.loads(config_path.read_text())
    assert data["projects"] == {"/some/path": {}}
    assert data["mcpServers"]["ollama"] == {"command": "ollama"}


def test_remove_server_removes_entry_and_returns_true(tmp_path: Path) -> None:
    config_path = tmp_path / ".mcp.json"
    write_json(config_path, {"mcpServers": {"db": {"command": "dbhub"}}})

    removed = remove_server(config_path, "db")

    assert removed is True
    assert json.loads(config_path.read_text())["mcpServers"] == {}


def test_remove_server_returns_false_when_absent(tmp_path: Path) -> None:
    config_path = tmp_path / ".mcp.json"
    write_json(config_path, {"mcpServers": {}})

    removed = remove_server(config_path, "missing")

    assert removed is False


def test_check_reachability_stdio_command_found() -> None:
    result = check_reachability({"command": "ollama"}, which=lambda cmd: "/usr/bin/ollama")

    assert result.reachable is True


def test_check_reachability_stdio_command_missing() -> None:
    result = check_reachability({"command": "ghost-cli"}, which=lambda cmd: None)

    assert result.reachable is False


def test_check_reachability_http_success() -> None:
    result = check_reachability(
        {"type": "http", "url": "https://mcp.example.com"},
        http_get=lambda url, timeout: object(),
    )

    assert result.reachable is True


def test_check_reachability_http_failure() -> None:
    def failing_get(url: str, timeout: float):
        raise ConnectionError("refused")

    result = check_reachability(
        {"type": "http", "url": "https://mcp.example.com"}, http_get=failing_get
    )

    assert result.reachable is False
    assert "refused" in result.detail


def test_check_reachability_url_without_type_is_invalid_config() -> None:
    result = check_reachability({"url": "https://mcp.example.com"})

    assert result.reachable is False


def test_check_reachability_unsupported_type_returns_not_reachable() -> None:
    result = check_reachability({"type": "ws", "url": "wss://mcp.example.com"})

    assert result.reachable is False
