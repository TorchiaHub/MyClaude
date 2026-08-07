import json
from pathlib import Path

from app.sandbox_config import read_sandbox_config


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_read_sandbox_config_returns_sandbox_key_when_present(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(
        settings_path,
        {
            "sandbox": {
                "filesystem": {"allowManagedReadPathsOnly": False},
                "network": {"allowManagedDomainsOnly": True},
            },
            "autoAllowBashIfSandboxed": True,
        },
    )

    result = read_sandbox_config(settings_path)

    assert result.enabled is True
    assert result.raw_config == {
        "filesystem": {"allowManagedReadPathsOnly": False},
        "network": {"allowManagedDomainsOnly": True},
    }
    assert result.auto_allow_bash_if_sandboxed is True


def test_read_sandbox_config_returns_disabled_when_no_sandbox_key(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    write_json(settings_path, {})

    result = read_sandbox_config(settings_path)

    assert result.enabled is False
    assert result.raw_config == {}
    assert result.auto_allow_bash_if_sandboxed is None


def test_read_sandbox_config_handles_missing_settings_file(tmp_path: Path) -> None:
    result = read_sandbox_config(tmp_path / "does-not-exist.json")

    assert result.enabled is False
    assert result.raw_config == {}
