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

    def add_node_pool(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"id": "c1"}

    def kubeconfig(self, cluster_id):
        return "apiVersion: v1\nkind: Config\n"


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
