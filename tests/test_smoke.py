"""CLI smoke tests — verify app structure, command registration, flags, and token resolution."""

import json
import os
import re
from unittest.mock import patch

from typer.testing import CliRunner

from wayscloud_cli.__main__ import app
from wayscloud_cli import __version__
from wayscloud_cli.config import resolve_token
from wayscloud_cli.output import set_json_mode, is_json_mode

runner = CliRunner()

# Rich styles option names with ANSI codes when color is forced (CI sets
# FORCE_COLOR-like variables), splitting e.g. '--token' across sequences.
# Assertions read the plain text so they are environment-independent.
_ANSI = re.compile(r'\x1b\[[0-9;]*m')


def plain(text):
    return _ANSI.sub('', text)


# ── App structure ───────────────────────────────────────────────

def test_app_has_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "WAYSCloud CLI" in plain(result.output)


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in plain(result.output)


# ── Command groups registered ───────────────────────────────────

EXPECTED_GROUPS = ["auth", "vps", "dns", "storage", "db", "redis", "app", "iot", "shell", "impact"]


def test_all_command_groups_registered():
    result = runner.invoke(app, ["--help"])
    for group in EXPECTED_GROUPS:
        assert group in plain(result.output), f"Command group '{group}' not in help output"


def test_each_group_has_help():
    for group in EXPECTED_GROUPS:
        result = runner.invoke(app, [group, "--help"])
        assert result.exit_code == 0, f"{group} --help failed with exit {result.exit_code}"


# ── Top-level shortcuts ─────────────────────────────────────────

def test_login_shortcut_exists():
    result = runner.invoke(app, ["login", "--help"])
    assert result.exit_code == 0
    assert "token" in plain(result.output).lower()


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
    assert "--token" in plain(result.output)


def test_vps_create_requires_flags():
    result = runner.invoke(app, ["vps", "create", "--help"])
    assert result.exit_code == 0
    for flag in ["--hostname", "--plan", "--region", "--os"]:
        assert flag in plain(result.output), f"Missing {flag} in vps create"


# ── DNS commands ────────────────────────────────────────────────

def test_dns_records_create_has_type_flag():
    result = runner.invoke(app, ["dns", "records-create", "--help"])
    assert result.exit_code == 0
    assert "--type" in plain(result.output)
    assert "--value" in plain(result.output)


# ── DB commands ─────────────────────────────────────────────────

def test_db_create_has_type_flag():
    result = runner.invoke(app, ["db", "create", "--help"])
    assert result.exit_code == 0
    assert "--type" in plain(result.output)


# ── IoT commands ────────────────────────────────────────────────

def test_iot_devices_create_has_required_flags():
    result = runner.invoke(app, ["iot", "devices-create", "--help"])
    assert result.exit_code == 0
    assert "--device-id" in plain(result.output)
    assert "--name" in plain(result.output)


# ── Impact commands ─────────────────────────────────────────────

def test_impact_subgroups_registered():
    """cloud impact has forest / tree / commitments subgroups."""
    result = runner.invoke(app, ["impact", "--help"])
    assert result.exit_code == 0
    for sub in ("forest", "tree", "commitments"):
        assert sub in plain(result.output), f"Missing impact subgroup: {sub}"


def test_impact_tree_grow_has_count_flag():
    result = runner.invoke(app, ["impact", "tree", "grow", "--help"])
    assert result.exit_code == 0
    assert "--count" in plain(result.output)
    assert "--idempotency-key" in plain(result.output)


def test_impact_forest_create_help():
    result = runner.invoke(app, ["impact", "forest", "create", "--help"])
    assert result.exit_code == 0
    # Argument should be the forest name; --token override always accepted.
    assert "--token" in plain(result.output)


def test_impact_forest_status_has_visualize():
    result = runner.invoke(app, ["impact", "forest", "status", "--help"])
    assert result.exit_code == 0
    assert "--visualize" in plain(result.output)


def test_impact_forbidden_strings_not_in_help():
    """Anti-greenwashing wording lock: these strings must NEVER appear
    anywhere in the impact CLI surface, not even in help text."""
    forbidden = ["carbon neutral", "offset", "net zero", "Carbon Neutral", "Net Zero"]
    for sub_path in (
        ["impact", "--help"],
        ["impact", "forest", "--help"],
        ["impact", "tree", "--help"],
        ["impact", "tree", "grow", "--help"],
        ["impact", "tree", "inspect", "--help"],
        ["impact", "tree", "water", "--help"],
        ["impact", "commitments", "--help"],
        ["impact", "forest", "status", "--help"],
        ["impact", "forest", "feed", "--help"],
    ):
        result = runner.invoke(app, sub_path)
        assert result.exit_code == 0, f"help failed for {sub_path}"
        for s in forbidden:
            assert s not in plain(result.output), (
                f"Forbidden string {s!r} appeared in help for {sub_path}"
            )
