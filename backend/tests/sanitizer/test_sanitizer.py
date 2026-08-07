import json
from pathlib import Path

from app.package_registry.models import Package
from app.sanitizer import build_export_bundle, sanitize_mcp_config, sanitize_text


def _make_package(content_path: Path) -> Package:
    return Package(
        id="demo-package",
        name="Demo Package",
        version="1.0.0",
        scope="project",
        project_path="/home/dev/secret-project",
        content_path=content_path,
        folder="Frontend",
        description="Un pacchetto di prova.",
        updated_at=1234567890,
        canvas_layout={"nodes": [], "edges": []},
    )


def test_sanitize_mcp_config_redacts_sensitive_env_keys():
    config = {
        "command": "npx",
        "env": {"API_KEY": "sk-super-secret", "LOG_LEVEL": "debug"},
    }

    sanitized = sanitize_mcp_config(config)

    assert sanitized["env"]["API_KEY"] == "<REDACTED>"
    assert sanitized["env"]["LOG_LEVEL"] == "debug"


def test_sanitize_mcp_config_redacts_sensitive_headers():
    config = {
        "type": "http",
        "url": "https://example.com",
        "headers": {"Authorization": "Bearer xyz"},
    }

    sanitized = sanitize_mcp_config(config)

    assert sanitized["headers"]["Authorization"] == "<REDACTED>"


def test_sanitize_mcp_config_redacts_sensitive_flag_in_args():
    config = {"command": "npx", "args": ["-y", "@x/mcp", "--api-key=sk-real-secret-abc"]}

    sanitized = sanitize_mcp_config(config)

    assert sanitized["args"] == ["-y", "@x/mcp", "--api-key=<REDACTED>"]


def test_sanitize_mcp_config_leaves_non_sensitive_args_untouched():
    config = {"args": ["-y", "@x/mcp", "--port=8080"]}

    sanitized = sanitize_mcp_config(config)

    assert sanitized["args"] == ["-y", "@x/mcp", "--port=8080"]


def test_sanitize_mcp_config_redacts_sensitive_query_param_in_url():
    config = {"type": "http", "url": "https://example.com/mcp?api_key=sk-real-secret-xyz&x=1"}

    sanitized = sanitize_mcp_config(config)

    assert "sk-real-secret-xyz" not in sanitized["url"]
    assert "x=1" in sanitized["url"]


def test_sanitize_mcp_config_does_not_mutate_input():
    config = {"env": {"API_KEY": "sk-super-secret"}}

    sanitize_mcp_config(config)

    assert config["env"]["API_KEY"] == "sk-super-secret"


def test_sanitize_text_replaces_home_path():
    text = "Vedi /home/dev/secret-project/notes.md per i dettagli."

    sanitized = sanitize_text(text, Path("/home/dev/secret-project"))

    assert "/home/dev/secret-project" not in sanitized
    assert "<HOME>" in sanitized


def test_build_export_bundle_excludes_package_json(tmp_path):
    content_path = tmp_path / "demo-package"
    content_path.mkdir()
    (content_path / "package.json").write_text(json.dumps({"id": "demo-package"}))
    (content_path / ".claude" / "rules").mkdir(parents=True)
    (content_path / ".claude" / "rules" / "style.md").write_text("Usa 4 spazi.")

    bundle = build_export_bundle(content_path, _make_package(content_path), Path("/home/dev"))

    assert "package.json" not in bundle["files"]
    assert bundle["files"][".claude/rules/style.md"] == "Usa 4 spazi."


def test_build_export_bundle_never_includes_project_path(tmp_path):
    content_path = tmp_path / "demo-package"
    content_path.mkdir()
    package = _make_package(content_path)

    bundle = build_export_bundle(content_path, package, Path("/home/dev"))

    assert "project_path" not in bundle
    assert "content_path" not in bundle


def test_build_export_bundle_sanitizes_mcp_json_file(tmp_path):
    content_path = tmp_path / "demo-package"
    content_path.mkdir()
    (content_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"obsidian": {"env": {"API_KEY": "sk-123"}}}})
    )

    bundle = build_export_bundle(content_path, _make_package(content_path), Path("/home/dev"))

    exported = json.loads(bundle["files"][".mcp.json"])
    assert exported["mcpServers"]["obsidian"]["env"]["API_KEY"] == "<REDACTED>"


def test_build_export_bundle_sanitizes_absolute_home_paths_in_mcp_json_command(tmp_path):
    content_path = tmp_path / "demo-package"
    content_path.mkdir()
    home = Path("/home/dev")
    (content_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"obsidian": {"command": f"{home}/bin/obsidian-mcp"}}})
    )

    bundle = build_export_bundle(content_path, _make_package(content_path), home)

    assert str(home) not in bundle["files"][".mcp.json"]


def test_build_export_bundle_sanitizes_absolute_home_paths_in_text_files(tmp_path):
    content_path = tmp_path / "demo-package"
    (content_path / ".claude" / "agents").mkdir(parents=True)
    agent_file = content_path / ".claude" / "agents" / "helper.md"
    home = Path("/home/dev")
    agent_file.write_text(f"Leggi i file in {home}/secret-project/data.")

    bundle = build_export_bundle(content_path, _make_package(content_path), home)

    assert str(home) not in bundle["files"][".claude/agents/helper.md"]


def test_build_export_bundle_falls_back_to_text_sanitization_for_malformed_mcp_json(tmp_path):
    content_path = tmp_path / "demo-package"
    content_path.mkdir()
    home = Path("/home/dev")
    (content_path / ".mcp.json").write_text(f"not valid json, path {home}/secret")

    bundle = build_export_bundle(content_path, _make_package(content_path), home)

    assert str(home) not in bundle["files"][".mcp.json"]


def test_build_export_bundle_handles_mcp_json_with_non_dict_mcp_servers(tmp_path):
    content_path = tmp_path / "demo-package"
    content_path.mkdir()
    (content_path / ".mcp.json").write_text(json.dumps({"mcpServers": ["not", "a", "dict"]}))

    bundle = build_export_bundle(content_path, _make_package(content_path), Path("/home/dev"))

    assert ".mcp.json" in bundle["files"]


def test_build_export_bundle_handles_mcp_json_that_is_not_an_object(tmp_path):
    content_path = tmp_path / "demo-package"
    content_path.mkdir()
    (content_path / ".mcp.json").write_text(json.dumps([1, 2, 3]))

    bundle = build_export_bundle(content_path, _make_package(content_path), Path("/home/dev"))

    assert ".mcp.json" in bundle["files"]


def test_build_export_bundle_skips_files_that_are_not_valid_utf8(tmp_path):
    content_path = tmp_path / "demo-package"
    (content_path / ".claude" / "skills" / "binary-skill").mkdir(parents=True)
    binary_file = content_path / ".claude" / "skills" / "binary-skill" / "asset.bin"
    binary_file.write_bytes(b"\xff\xfe\x00\x01")

    bundle = build_export_bundle(content_path, _make_package(content_path), Path("/home/dev"))

    assert ".claude/skills/binary-skill/asset.bin" not in bundle["files"]
