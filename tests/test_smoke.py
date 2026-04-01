"""CLI smoke tests — verify app structure, command registration, flags, and token resolution."""

import json
import os
from unittest.mock import patch

from typer.testing import CliRunner

from wayscloud_cli.__main__ import app
from wayscloud_cli import __version__
from wayscloud_cli.config import resolve_token
from wayscloud_cli.output import set_json_mode, is_json_mode

runner = CliRunner()


# ── App structure ───────────────────────────────────────────────

def test_app_has_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "WAYSCloud CLI" in result.output


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


# ── Command groups registered ───────────────────────────────────

EXPECTED_GROUPS = ["auth", "vps", "dns", "storage", "db", "redis", "app", "iot", "shell"]


def test_all_command_groups_registered():
    result = runner.invoke(app, ["--help"])
    for group in EXPECTED_GROUPS:
        assert group in result.output, f"Command group '{group}' not in help output"


def test_each_group_has_help():
    for group in EXPECTED_GROUPS:
        result = runner.invoke(app, [group, "--help"])
        assert result.exit_code == 0, f"{group} --help failed with exit {result.exit_code}"


# ── Top-level shortcuts ─────────────────────────────────────────

def test_login_shortcut_exists():
    result = runner.invoke(app, ["login", "--help"])
    assert result.exit_code == 0
    assert "token" in result.output.lower()


def test_whoami_shortcut_exists():
    result = runner.invoke(app, ["whoami", "--help"])
    assert result.exit_code == 0


def test_logout_shortcut_exists():
    result = runner.invoke(app, ["logout", "--help"])
    assert result.exit_code == 0


# ── Token resolution ────────────────────────────────────────────

def test_explicit_token_wins(monkeypatch):
    monkeypatch.setenv("WAYSCLOUD_TOKEN", "env_token")
    assert resolve_token("explicit_token") == "explicit_token"


def test_env_var_used_when_no_explicit(monkeypatch):
    monkeypatch.setenv("WAYSCLOUD_TOKEN", "env_token")
    assert resolve_token(None) == "env_token"


def test_returns_none_when_nothing(monkeypatch, tmp_path):
    monkeypatch.delenv("WAYSCLOUD_TOKEN", raising=False)
    # Point credentials file to nonexistent path
    monkeypatch.setattr("wayscloud_cli.config.CREDENTIALS_FILE", tmp_path / "nope")
    assert resolve_token(None) is None


def test_reads_credentials_file(monkeypatch, tmp_path):
    monkeypatch.delenv("WAYSCLOUD_TOKEN", raising=False)
    cred_file = tmp_path / "credentials"
    cred_file.write_text(json.dumps({"version": 1, "token": "file_token"}))
    monkeypatch.setattr("wayscloud_cli.config.CREDENTIALS_FILE", cred_file)
    assert resolve_token(None) == "file_token"


# ── Output modes ────────────────────────────────────────────────

def test_json_mode_toggle():
    set_json_mode(False)
    assert not is_json_mode()
    set_json_mode(True)
    assert is_json_mode()
    set_json_mode(False)


def test_json_flag_accepted():
    result = runner.invoke(app, ["--json", "--help"])
    assert result.exit_code == 0


# ── VPS commands exist with correct args ────────────────────────

def test_vps_list_help():
    result = runner.invoke(app, ["vps", "list", "--help"])
    assert result.exit_code == 0
    assert "--token" in result.output


def test_vps_create_requires_flags():
    result = runner.invoke(app, ["vps", "create", "--help"])
    assert result.exit_code == 0
    for flag in ["--hostname", "--plan", "--region", "--os"]:
        assert flag in result.output, f"Missing {flag} in vps create"


# ── DNS commands ────────────────────────────────────────────────

def test_dns_records_create_has_type_flag():
    result = runner.invoke(app, ["dns", "records-create", "--help"])
    assert result.exit_code == 0
    assert "--type" in result.output
    assert "--value" in result.output


# ── DB commands ─────────────────────────────────────────────────

def test_db_create_has_type_flag():
    result = runner.invoke(app, ["db", "create", "--help"])
    assert result.exit_code == 0
    assert "--type" in result.output


# ── IoT commands ────────────────────────────────────────────────

def test_iot_devices_create_has_required_flags():
    result = runner.invoke(app, ["iot", "devices-create", "--help"])
    assert result.exit_code == 0
    assert "--device-id" in result.output
    assert "--name" in result.output
