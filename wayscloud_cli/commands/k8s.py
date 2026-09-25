"""
cloud k8s commands — Managed Kubernetes clusters.
"""

import sys
from typing import List, Optional

import typer

from ..sdk import get_client, sdk_call
from ..output import print_table, print_object, print_json, is_json_mode

app = typer.Typer(help="Managed Kubernetes")

CLUSTER_COLUMNS = [
    ("id", "ID", 38), ("name", "Name", 20), ("status", "Status", 13), ("version", "Version", 8),
    ("region", "Region", 7), ("nodes", "Nodes", 6), ("created_at", "Created", 20),
]


def _row(c: dict) -> dict:
    return {
        "id": c.get("id", ""), "name": c.get("name", ""), "status": c.get("status", ""), "version": c.get("version", ""),
        "region": c.get("region", ""), "nodes": sum(int(p.get("count", 0)) for p in c.get("node_pools", [])),
        "created_at": str(c.get("created_at", ""))[:19],
    }


def _parse_pool(spec: str) -> dict:
    """'name=default,plan=k8s-node-2c4g,count=2' or the shorthand 'k8s-node-2c4g:2'."""
    if "=" not in spec:
        plan, _, count = spec.partition(":")
        return {"name": "default", "plan_code": plan, "count": int(count or 1)}
    kv = dict(part.split("=", 1) for part in spec.split(","))
    return {"name": kv.get("name", "default"), "plan_code": kv["plan"], "count": int(kv.get("count", 1))}


TAINT_EFFECTS = ("NoSchedule", "PreferNoSchedule", "NoExecute")


def _parse_labels(pairs: List[str]) -> dict:
    """'key=value' pairs (repeatable) -> {key: value}."""
    labels = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            raise typer.BadParameter(f"label must be key=value, got {pair!r}")
        labels[key] = value
    return labels


def _parse_taints(items: List[str]) -> List[dict]:
    """'key=value:Effect' items (repeatable) -> [{'key','value','effect'}]."""
    taints = []
    for item in items:
        pair, sep, effect = item.rpartition(":")
        key, eq, value = pair.partition("=")
        if not sep or not eq or not key:
            raise typer.BadParameter(f"taint must be key=value:Effect, got {item!r}")
        if effect not in TAINT_EFFECTS:
            raise typer.BadParameter(f"taint effect must be one of {', '.join(TAINT_EFFECTS)}, got {effect!r}")
        taints.append({"key": key, "value": value, "effect": effect})
    return taints


@app.command("plans")
def plans(region: str = typer.Option("no", "--region"), kind: Optional[str] = typer.Option(None, "--kind", help="controlplane|node|ip|lb|storage|backup"),
          currency: str = typer.Option("NOK", "--currency"), token: Optional[str] = typer.Option(None, "--token")):
    """List cluster and node plans."""
    data = sdk_call(get_client(token).kubernetes.plans, region, kind)
    if is_json_mode():
        print_json(data); return
    rows = [{"plan_code": p["plan_code"], "kind": p["kind"], "name": p["name"],
             "spec": f"{p.get('cpu_cores') or '-'} vCPU / {int(p['ram_mb']) // 1024 if p.get('ram_mb') else '-'} GB / {p.get('disk_gb') or '-'} GB",
             "monthly": f"{p.get('prices', {}).get(currency, '')} {currency}"} for p in data]
    print_table(rows, [("plan_code", "Plan", 18), ("kind", "Kind", 13), ("name", "Name", 22), ("spec", "Spec", 24), ("monthly", "Monthly", 14)])


@app.command("list")
def list_clusters(token: Optional[str] = typer.Option(None, "--token")):
    """List clusters."""
    clusters = sdk_call(get_client(token).kubernetes.list)
    if is_json_mode():
        print_json(clusters); return
    if not clusters:
        print("No clusters found."); return
    print_table([_row(c) for c in clusters], CLUSTER_COLUMNS)


@app.command("create")
def create(
    name: str = typer.Argument(..., help="Cluster name (lowercase, digits, hyphens)"),
    pool: List[str] = typer.Option(["k8s-node-2c4g:2"], "--pool", help="Node pool: 'plan:count' or 'name=…,plan=…,count=…' (repeatable)"),
    plan: str = typer.Option("k8s-cluster-dev", "--plan", help="k8s-cluster-dev | k8s-cluster-prod"),
    region: str = typer.Option("no", "--region"),
    version: str = typer.Option("1.34", "--version"),
    allow: List[str] = typer.Option([], "--allow", help="CIDR allowed to reach the API (repeatable)"),
    wait: bool = typer.Option(False, "--wait", help="Block until the cluster is running"),
    token: Optional[str] = typer.Option(None, "--token"),
):
    """Create a cluster (asynchronous unless --wait)."""
    c = get_client(token)
    cluster = sdk_call(c.kubernetes.create, name, [_parse_pool(p) for p in pool], plan_code=plan, region=region, version=version, api_ip_filter=list(allow))
    if wait:
        cluster = sdk_call(c.kubernetes.wait, cluster["id"])
    if is_json_mode():
        print_json(cluster)
    else:
        print(f"Cluster {name} ({cluster['id']}) is {cluster['status']}.")
        if cluster.get("api_endpoint"):
            print(f"API: {cluster['api_endpoint']}")


@app.command("info")
def info(cluster_id: str = typer.Argument(...), token: Optional[str] = typer.Option(None, "--token")):
    """Show a cluster."""
    c = sdk_call(get_client(token).kubernetes.get, cluster_id)
    if is_json_mode():
        print_json(c); return
    print_object(c, [("id", "ID"), ("name", "Name"), ("status", "Status"), ("provisioning_step", "Step"), ("version", "Version"),
                     ("region_city", "Region"), ("plan_code", "Plan"), ("api_endpoint", "API endpoint"), ("network_cidr", "Network"),
                     ("created_at", "Created"), ("running_since", "Running since"), ("trial_ends_at", "Trial ends")])
    pools = c.get("node_pools", [])
    if pools:
        print("\nNode pools:")
        print_table([{"name": p["name"], "plan": p["plan_code"], "count": p["count"], "status": p.get("status", "")} for p in pools],
                    [("name", "Name", 16), ("plan", "Plan", 18), ("count", "Count", 6), ("status", "Status", 12)])
    ips = c.get("public_ips", [])
    if ips:
        print("\nPublic IPs:")
        print_table([{"address": i["address"], "kind": i["kind"], "ptr": i.get("ptr_record") or ""} for i in ips],
                    [("address", "Address", 16), ("kind", "Kind", 9), ("ptr", "PTR", 40)])


@app.command("kubeconfig")
def kubeconfig(cluster_id: str = typer.Argument(...), output: Optional[str] = typer.Option(None, "--output", "-o", help="Write to file (0600) instead of stdout"),
               token: Optional[str] = typer.Option(None, "--token")):
    """Download the admin kubeconfig (secret)."""
    text = sdk_call(get_client(token).kubernetes.kubeconfig, cluster_id)
    if output:
        import os
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, "w") as f:
                f.write(text)
        finally:
            os.chmod(output, 0o600)
        print(f"Wrote {output} (mode 0600). Use: export KUBECONFIG={output}", file=sys.stderr)
    else:
        sys.stdout.write(text)


@app.command("scale")
def scale(cluster_id: str = typer.Argument(...), pool: str = typer.Argument(..., help="Node pool name"),
          count: int = typer.Argument(..., min=1, max=16, help="New node count (1–16)"),
          token: Optional[str] = typer.Option(None, "--token")):
    """Scale a node pool."""
    c = sdk_call(get_client(token).kubernetes.scale_node_pool, cluster_id, pool, count)
    print_json(c) if is_json_mode() else print(f"Pool {pool} scaling to {count}.")


@app.command("add-pool")
def add_pool(cluster_id: str = typer.Argument(...), name: str = typer.Argument(...), plan: str = typer.Option(..., "--plan"),
             count: int = typer.Option(1, "--count", min=1, max=16, help="Node count (1–16)"),
             label: List[str] = typer.Option([], "--label", help="Node label key=value (repeatable)"),
             taint: List[str] = typer.Option([], "--taint", help="Node taint key=value:Effect (repeatable)"),
             ssh_key_id: List[str] = typer.Option([], "--ssh-key-id", help="SSH key id to install on the pool's nodes (repeatable)"),
             token: Optional[str] = typer.Option(None, "--token")):
    """Add a node pool."""
    c = sdk_call(get_client(token).kubernetes.add_node_pool, cluster_id, name, plan, count,
                 labels=_parse_labels(label), taints=_parse_taints(taint), ssh_key_ids=list(ssh_key_id))
    print_json(c) if is_json_mode() else print(f"Pool {name} added.")


@app.command("delete-pool")
def delete_pool(cluster_id: str = typer.Argument(...), name: str = typer.Argument(...), token: Optional[str] = typer.Option(None, "--token")):
    """Delete a node pool."""
    c = sdk_call(get_client(token).kubernetes.delete_node_pool, cluster_id, name)
    print_json(c) if is_json_mode() else print(f"Pool {name} deleted.")


@app.command("api-access")
def api_access(cluster_id: str = typer.Argument(...), cidr: List[str] = typer.Option([], "--cidr", help="Allowed CIDR (repeatable); an empty list allows only WAYSCloud access"),
               token: Optional[str] = typer.Option(None, "--token")):
    """Set which sources may reach the Kubernetes API."""
    c = sdk_call(get_client(token).kubernetes.set_api_access, cluster_id, list(cidr))
    print_json(c) if is_json_mode() else print("API allow-list: " + (", ".join(c.get("api_ip_filter", [])) or "only WAYSCloud (no external access)"))


@app.command("ip-allocate")
def ip_allocate(cluster_id: str = typer.Argument(...), token: Optional[str] = typer.Option(None, "--token")):
    """Allocate an additional public IPv4."""
    c = sdk_call(get_client(token).kubernetes.allocate_ip, cluster_id)
    print_json(c) if is_json_mode() else print("Public IPs: " + ", ".join(i["address"] for i in c.get("public_ips", [])))


@app.command("ip-release")
def ip_release(cluster_id: str = typer.Argument(...), address: str = typer.Argument(...), token: Optional[str] = typer.Option(None, "--token")):
    """Release an additional public IPv4."""
    sdk_call(get_client(token).kubernetes.release_ip, cluster_id, address)
    print(f"Released {address}.")


@app.command("ptr")
def ptr(cluster_id: str = typer.Argument(...), address: str = typer.Argument(...), name: str = typer.Argument(..., help="FQDN that already resolves to the address"),
        token: Optional[str] = typer.Option(None, "--token")):
    """Set reverse DNS on a cluster IP."""
    sdk_call(get_client(token).kubernetes.set_ptr, cluster_id, address, name)
    print(f"PTR for {address} set to {name}.")


@app.command("backups")
def backups(cluster_id: str = typer.Argument(...), token: Optional[str] = typer.Option(None, "--token")):
    """List backups."""
    data = sdk_call(get_client(token).kubernetes.backups, cluster_id)
    if is_json_mode():
        print_json(data); return
    print_table([{"id": b["id"], "name": b["name"], "kind": b["kind"], "status": b["status"], "completed": str(b.get("completed_at") or "")[:19], "expires": str(b.get("expires_at") or "")[:10]} for b in data],
                [("id", "ID", 38), ("name", "Name", 26), ("kind", "Kind", 10), ("status", "Status", 16), ("completed", "Completed", 20), ("expires", "Expires", 11)])


@app.command("backup")
def backup(cluster_id: str = typer.Argument(...), namespace: List[str] = typer.Option([], "--namespace", "-n"), token: Optional[str] = typer.Option(None, "--token")):
    """Start a backup now."""
    b = sdk_call(get_client(token).kubernetes.backup_now, cluster_id, list(namespace) or None)
    print_json(b) if is_json_mode() else print(f"Backup {b['name']} started.")


@app.command("restore")
def restore(cluster_id: str = typer.Argument(...), backup_id: str = typer.Argument(...), namespace: List[str] = typer.Option([], "--namespace", "-n"),
            token: Optional[str] = typer.Option(None, "--token")):
    """Restore a backup into the cluster."""
    r = sdk_call(get_client(token).kubernetes.restore, cluster_id, backup_id, list(namespace) or None)
    print_json(r) if is_json_mode() else print(f"Restore {r['restore']} started.")


@app.command("upgrade")
def upgrade(cluster_id: str = typer.Argument(...), version: Optional[str] = typer.Argument(None, help="Target version; omit to list"),
            token: Optional[str] = typer.Option(None, "--token")):
    """List available upgrades or upgrade to a version."""
    c = get_client(token)
    if not version:
        v = sdk_call(c.kubernetes.available_upgrades, cluster_id)
        print_json(v) if is_json_mode() else print("Available: " + (", ".join(v) or "none"))
        return
    r = sdk_call(c.kubernetes.upgrade, cluster_id, version)
    print_json(r) if is_json_mode() else print(f"Upgrading to {version}. No backup is taken automatically; create one first if needed.")


@app.command("delete")
def delete(cluster_id: str = typer.Argument(...), confirm_name: str = typer.Option(..., "--confirm-name", help="Type the cluster name to confirm"),
           wait: bool = typer.Option(False, "--wait"), token: Optional[str] = typer.Option(None, "--token")):
    """Delete a cluster (asynchronous unless --wait)."""
    c = get_client(token)
    r = sdk_call(c.kubernetes.delete, cluster_id, confirm_name)
    if wait:
        r = sdk_call(c.kubernetes.wait, cluster_id)
    print_json(r) if is_json_mode() else print(f"Cluster {cluster_id} is {r.get('status')}.")
