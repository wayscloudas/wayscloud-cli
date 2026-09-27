"""k8s command tests -- option parsing, payloads and file handling."""

import os
import stat

from typer.testing import CliRunner

from wayscloud_cli.__main__ import app
from wayscloud_cli.commands import k8s as k8s_cmd

runner = CliRunner()


class FakeKubernetes:
    def __init__(self):
        self.calls = []
        self.window = {}
        self.jobs = []
        self.upgrade_response = None
        self.preflight_response = None

    def add_node_pool(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"id": "c1"}

    def kubeconfig(self, cluster_id):
        return "apiVersion: v1\nkind: Config\n"

    def delete_node_pool(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"id": "c1"}

    def upgrade_node_pool(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"id": "c1"}

    def versions(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"default": "1.35", "versions": [
            {"version": "1.35", "status": "default", "create_allowed": True, "create_until": None,
             "support_ends_at": "2027-02-28", "upgrade_required_by": None, "recommended_upgrade": None},
            {"version": "1.34", "status": "transition", "create_allowed": True, "create_until": "2026-10-15",
             "support_ends_at": "2026-10-27", "upgrade_required_by": "2026-10-20", "recommended_upgrade": "1.35"}]}

    def upgrade(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.upgrade_response or {"id": "c1", "status": "upgrading"}

    def upgrade_preflight(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.preflight_response or {"ok": True, "errors": [], "warnings": []}

    def upgrade_jobs(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.jobs

    def upgrade_job(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.jobs[0] if self.jobs else {}

    def cancel_upgrade_job(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"id": "j1", "status": "cancelled"}

    def set_maintenance_window(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"enabled": kwargs.get("enabled", True), "timezone": kwargs.get("timezone"), "days": kwargs.get("days"),
                "start": kwargs.get("start"), "duration_minutes": kwargs.get("duration_minutes"),
                "next_window_start": "2026-10-24T02:00:00+02:00", "next_window_end": "2026-10-24T04:00:00+02:00"}

    def get_maintenance_window(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.window

    def delete_maintenance_window(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"enabled": False, "timezone": None, "days": [], "start": None, "duration_minutes": None,
                "next_window_start": None, "next_window_end": None}


class FakeClient:
    def __init__(self, kubernetes):
        self.kubernetes = kubernetes


def patch_client(monkeypatch, kubernetes):
    monkeypatch.setattr(k8s_cmd, "get_client", lambda token=None: FakeClient(kubernetes))


def test_parse_labels_and_taints():
    assert k8s_cmd._parse_labels([]) == {}
    assert k8s_cmd._parse_labels(["role=worker", "zone=a=b"]) == {"role": "worker", "zone": "a=b"}
    assert k8s_cmd._parse_taints([]) == []
    assert k8s_cmd._parse_taints(["dedicated=gpu:NoSchedule", "spot=:PreferNoSchedule"]) == [
        {"key": "dedicated", "value": "gpu", "effect": "NoSchedule"},
        {"key": "spot", "value": "", "effect": "PreferNoSchedule"},
    ]


def test_add_pool_passes_labels_taints_and_ssh_keys(monkeypatch):
    kube = FakeKubernetes()
    patch_client(monkeypatch, kube)

    result = runner.invoke(app, [
        "k8s", "add-pool", "c1", "workers", "--plan", "k8s-node-2c4g", "--count", "3",
        "--label", "role=worker", "--label", "tier=compute",
        "--taint", "dedicated=gpu:NoExecute",
        "--ssh-key-id", "11111111-1111-1111-1111-111111111111",
    ])

    assert result.exit_code == 0, result.output
    (args, kwargs), = kube.calls
    assert args == ("c1", "workers", "k8s-node-2c4g", 3)
    assert kwargs["labels"] == {"role": "worker", "tier": "compute"}
    assert kwargs["taints"] == [{"key": "dedicated", "value": "gpu", "effect": "NoExecute"}]
    assert kwargs["ssh_key_ids"] == ["11111111-1111-1111-1111-111111111111"]


def test_add_pool_defaults_to_no_labels_taints_or_keys(monkeypatch):
    kube = FakeKubernetes()
    patch_client(monkeypatch, kube)

    result = runner.invoke(app, ["k8s", "add-pool", "c1", "workers", "--plan", "k8s-node-2c4g"])

    assert result.exit_code == 0, result.output
    (args, kwargs), = kube.calls
    assert args == ("c1", "workers", "k8s-node-2c4g", 1)
    assert kwargs == {"labels": {}, "taints": [], "ssh_key_ids": []}


def test_add_pool_rejects_malformed_label_and_taint(monkeypatch):
    patch_client(monkeypatch, FakeKubernetes())

    for value in ("novalue", "=noKey"):
        result = runner.invoke(app, ["k8s", "add-pool", "c1", "workers", "--plan", "k8s-node-2c4g", "--label", value])
        assert result.exit_code != 0
        assert "key=value" in result.output

    for value in ("novalue", "key:NoSchedule", "key=value:Sometimes"):
        result = runner.invoke(app, ["k8s", "add-pool", "c1", "workers", "--plan", "k8s-node-2c4g", "--taint", value])
        assert result.exit_code != 0
        assert "key=value:Effect" in result.output or "taint effect" in result.output


def test_kubeconfig_output_file_is_0600_for_new_and_existing_files(monkeypatch, tmp_path):
    patch_client(monkeypatch, FakeKubernetes())

    existing = tmp_path / "kubeconfig-existing.yaml"
    existing.write_text("stale-content")
    os.chmod(existing, 0o644)

    for target in (existing, tmp_path / "kubeconfig-new.yaml"):
        result = runner.invoke(app, ["k8s", "kubeconfig", "c1", "-o", str(target)])
        assert result.exit_code == 0, result.output
        assert stat.S_IMODE(target.stat().st_mode) == 0o600
        assert target.read_text() == "apiVersion: v1\nkind: Config\n"


def test_maintenance_window_set_passes_all_options(monkeypatch):
    kube = FakeKubernetes()
    patch_client(monkeypatch, kube)

    result = runner.invoke(app, ["k8s", "maintenance-window", "set", "c1",
                                 "--timezone", "Europe/Oslo", "--day", "SAT", "--day", "SUN",
                                 "--start", "02:00", "--duration", "120"])

    assert result.exit_code == 0, result.output
    (args, kwargs), = kube.calls
    assert args == ("c1",)
    assert kwargs == {"timezone": "Europe/Oslo", "days": ["SAT", "SUN"], "start": "02:00",
                      "duration_minutes": 120, "enabled": True}
    assert "2026-10-24T02:00:00+02:00" in result.output


def test_maintenance_window_set_disabled_and_get(monkeypatch):
    kube = FakeKubernetes()
    patch_client(monkeypatch, kube)

    result = runner.invoke(app, ["k8s", "maintenance-window", "set", "c1", "--timezone", "UTC",
                                 "--day", "MON", "--start", "03:00", "--disabled"])
    assert result.exit_code == 0, result.output
    assert kube.calls[0][1]["enabled"] is False
    assert kube.calls[0][1]["duration_minutes"] == 120  # default

    kube.window = {"enabled": True, "timezone": "Europe/Oslo", "days": ["SAT"], "start": "02:00",
                   "duration_minutes": 120, "next_window_start": "2026-10-24T02:00:00+02:00",
                   "next_window_end": "2026-10-24T04:00:00+02:00"}
    result = runner.invoke(app, ["k8s", "maintenance-window", "get", "c1"])
    assert result.exit_code == 0, result.output
    assert "Europe/Oslo" in result.output
    assert "SAT" in result.output


def test_maintenance_window_delete(monkeypatch):
    kube = FakeKubernetes()
    patch_client(monkeypatch, kube)
    result = runner.invoke(app, ["k8s", "maintenance-window", "delete", "c1"])
    assert result.exit_code == 0, result.output
    assert "removed" in result.output.lower()
    assert kube.calls[0][0] == ("c1",)


def test_upgrade_mode_options_and_queued_output(monkeypatch):
    kube = FakeKubernetes()
    kube.upgrade_response = {"job": {"id": "j1", "target_version": "1.35", "mode": "next_maintenance_window",
                                     "status": "queued", "execute_after": "2026-10-03T00:00:00+00:00"}}
    patch_client(monkeypatch, kube)

    result = runner.invoke(app, ["k8s", "upgrade", "c1", "1.35", "--mode", "next-maintenance-window",
                                 "--strategy", "rolling-update", "--backup-first"])

    assert result.exit_code == 0, result.output
    (args, kwargs), = kube.calls
    assert args == ("c1", "1.35")
    assert kwargs == {"mode": "next_maintenance_window", "scheduled_at": None,
                      "strategy": "rolling-update", "backup_before_upgrade": True}
    assert "queued" in result.output


def test_upgrade_defaults_to_rolling_after_qualification(monkeypatch):
    kube = FakeKubernetes()
    patch_client(monkeypatch, kube)

    result = runner.invoke(app, ["k8s", "upgrade", "c1", "1.35"])

    assert result.exit_code == 0, result.output
    (args, kwargs), = kube.calls
    assert kwargs == {"mode": "immediate", "scheduled_at": None, "strategy": "rolling-update", "backup_before_upgrade": False}
    assert "Upgrading to 1.35" in result.output


def test_upgrade_pool_command(monkeypatch):
    kube = FakeKubernetes()
    patch_client(monkeypatch, kube)

    result = runner.invoke(app, ["k8s", "upgrade-pool", "c1", "default"])

    assert result.exit_code == 0, result.output
    assert kube.calls[0][0] == ("c1", "default")
    assert "convergence started" in result.output


def test_versions_command_shows_lifecycle(monkeypatch):
    kube = FakeKubernetes()
    patch_client(monkeypatch, kube)

    result = runner.invoke(app, ["k8s", "versions"])

    assert result.exit_code == 0, result.output
    assert "1.34" in result.output and "transition" in result.output
    assert "2026-10-15" in result.output
    assert "Default for new clusters: 1.35" in result.output


def test_upgrade_jobs_list_and_cancel(monkeypatch):
    kube = FakeKubernetes()
    kube.jobs = [{"id": "j1", "target_version": "1.35", "mode": "scheduled", "status": "queued",
                  "execute_after": "2026-10-03T00:30:00+00:00", "window_end": "2026-10-03T02:00:00+00:00"}]
    patch_client(monkeypatch, kube)

    result = runner.invoke(app, ["k8s", "upgrade-jobs", "list", "c1"])
    assert result.exit_code == 0, result.output
    assert "queued" in result.output

    result = runner.invoke(app, ["k8s", "upgrade-jobs", "cancel", "c1", "j1"])
    assert result.exit_code == 0, result.output
    assert "cancelled" in result.output.lower()
    assert kube.calls[-1][0] == ("c1", "j1")


def test_preflight_passes_options_and_reports_warnings(monkeypatch):
    kube = FakeKubernetes()
    kube.preflight_response = {"ok": True, "errors": [],
                               "warnings": [{"code": "no_recent_backup", "message": "backup is old"}]}
    patch_client(monkeypatch, kube)

    result = runner.invoke(app, ["k8s", "preflight", "c1", "1.35", "--mode", "next-maintenance-window",
                                 "--strategy", "rolling-update", "--backup-first"])

    assert result.exit_code == 0, result.output
    (args, kwargs), = kube.calls
    assert args == ("c1", "1.35")
    assert kwargs == {"mode": "next_maintenance_window", "scheduled_at": None,
                      "strategy": "rolling-update", "backup_before_upgrade": True}
    assert "WARNING  [no_recent_backup]" in result.output
    assert "Preflight OK" in result.output


def test_preflight_blockers_exit_nonzero(monkeypatch):
    kube = FakeKubernetes()
    kube.preflight_response = {"ok": False, "errors": [{"code": "node_pool_not_ready", "message": "pool not ready"}],
                               "warnings": []}
    patch_client(monkeypatch, kube)

    result = runner.invoke(app, ["k8s", "preflight", "c1", "1.35"])

    assert result.exit_code == 1, result.output
    assert "BLOCKER  [node_pool_not_ready]" in result.output
    assert "Preflight BLOCKED" in result.output


def test_preflight_json_mode_prints_full_response_and_still_fails(monkeypatch):
    import json as json_mod
    from wayscloud_cli.output import set_json_mode

    kube = FakeKubernetes()
    kube.preflight_response = {"ok": False, "errors": [{"code": "target_not_available", "message": "nope"}],
                               "warnings": [], "backup": {"latest_completed_at": None, "age_hours": None}}
    patch_client(monkeypatch, kube)
    try:
        result = runner.invoke(app, ["--json", "k8s", "preflight", "c1", "1.35"])
    finally:
        set_json_mode(False)

    assert result.exit_code == 1
    parsed = json_mod.loads(result.output)
    assert parsed["errors"][0]["code"] == "target_not_available"
    assert parsed["backup"] == {"latest_completed_at": None, "age_hours": None}
