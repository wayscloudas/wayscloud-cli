"""
cloud vps commands — VPS provisioning, control, snapshots, and backups.
"""

import typer
from typing import Optional

from ..sdk import get_client, sdk_call
from ..output import print_table, print_object, print_json, is_json_mode

app = typer.Typer(help="Virtual Private Servers")

# ── Sub-apps for snapshots and backups ────────────────────────────
snapshots_app = typer.Typer(help="VPS snapshots (point-in-time disk copies)")
backups_app = typer.Typer(help="VPS backups (off-site cloud storage)")
backups_policy_app = typer.Typer(help="Backup policy management")

app.add_typer(snapshots_app, name="snapshots")
app.add_typer(backups_app, name="backups")
backups_app.add_typer(backups_policy_app, name="policy")


# ══════════════════════════════════════════════════════════════════
# VPS Instance Commands
# ══════════════════════════════════════════════════════════════════

@app.command("list")
def list_vps(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    status: Optional[str] = typer.Option(None, help="Filter by status"),
    region: Optional[str] = typer.Option(None, help="Filter by region"),
):
    """List your VPS instances."""
    c = get_client(token)
    data = sdk_call(c.vps.list, status=status, region=region)
    instances = data if isinstance(data, list) else data.get("instances", []) if isinstance(data, dict) else []

    if is_json_mode():
        print_json(instances)
        return

    if not instances:
        print("No VPS instances found.")
        return

    rows = []
    for v in instances:
        rows.append({
            "id": str(v.get("id", ""))[:12],
            "hostname": v.get("hostname", v.get("display_name", "")),
            "status": v.get("status", ""),
            "ip": v.get("ipv4_address", v.get("ip_address", "")),
            "plan": v.get("plan_code", ""),
            "region": v.get("region", ""),
            "snap": "yes" if v.get("snapshot_supported") else "no",
        })

    print_table(rows, [
        ("id", "ID", 14),
        ("hostname", "Hostname", 24),
        ("status", "Status", 12),
        ("ip", "IP", 16),
        ("plan", "Plan", 16),
        ("region", "Region", 8),
        ("snap", "Snap", 5),
    ])


@app.command("create")
def create_vps(
    hostname: str = typer.Option(..., "--hostname", help="VPS hostname"),
    plan: str = typer.Option(..., "--plan", help="Plan code"),
    region: str = typer.Option(..., "--region", help="Region code"),
    os: str = typer.Option(..., "--os", help="OS template"),
    ssh_key: Optional[list[str]] = typer.Option(None, "--ssh-key", help="SSH key (repeatable)"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create a new VPS."""
    c = get_client(token)
    data = sdk_call(c.vps.create, hostname=hostname, plan=plan, region=region,
                    os_template=os, ssh_keys=ssh_key or [])
    if is_json_mode():
        print_json(data)
    else:
        print(f"VPS created: {data.get('id', 'unknown')}")
        print_object(data, [("id", "ID"), ("hostname", "Hostname"), ("status", "Status"),
                            ("plan_code", "Plan"), ("region", "Region")])


@app.command("info")
def info_vps(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show VPS details (status, IPs, plan — all in one)."""
    c = get_client(token)
    data = sdk_call(c.vps.get, vps_id)

    if is_json_mode():
        print_json(data)
        return

    print_object(data, [
        ("id", "ID"), ("hostname", "Hostname"), ("status", "Status"),
        ("power_state", "Power"), ("ipv4_address", "IPv4"), ("ipv6_address", "IPv6"),
        ("os_template", "OS"), ("plan_code", "Plan"), ("region", "Region"),
        ("disk_format", "Disk Format"), ("snapshot_supported", "Snapshots"),
        ("created_at", "Created"),
    ])


@app.command("delete")
def delete_vps(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
):
    """Delete a VPS (permanent)."""
    if not confirm:
        print(f"This will permanently delete VPS {vps_id} and all its data.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.vps.delete, vps_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"VPS {vps_id}: deleted")


@app.command("start")
def start_vps(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Start a VPS."""
    c = get_client(token)
    data = sdk_call(c.vps.start, vps_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"VPS {vps_id}: {data.get('message', 'starting')}")


@app.command("stop")
def stop_vps(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Stop a VPS."""
    c = get_client(token)
    data = sdk_call(c.vps.stop, vps_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"VPS {vps_id}: {data.get('message', 'stopping')}")


@app.command("reboot")
def reboot_vps(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Reboot a VPS."""
    c = get_client(token)
    data = sdk_call(c.vps.reboot, vps_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"VPS {vps_id}: {data.get('message', 'rebooting')}")


@app.command("plans")
def list_plans(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    region: Optional[str] = typer.Option(None, help="Filter by region"),
):
    """List available VPS plans."""
    c = get_client(token)
    plans = sdk_call(c.vps.plans, region=region)
    plans = plans if isinstance(plans, list) else []

    if is_json_mode():
        print_json(plans)
        return

    rows = []
    for p in plans:
        rows.append({
            "code": p.get("plan_code", ""),
            "vcpu": p.get("vcpu", ""),
            "ram": f"{p.get('ram_mb', 0) // 1024}GB",
            "disk": f"{p.get('disk_gb', 0)}GB",
            "price": f"{p.get('monthly_price', '')} {p.get('currency', '')}",
        })

    print_table(rows, [
        ("code", "Plan", 24), ("vcpu", "vCPU", 6), ("ram", "RAM", 8),
        ("disk", "Disk", 8), ("price", "Price/mo", 14),
    ])


@app.command("os-templates")
def vps_os_templates(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List available OS templates."""
    c = get_client(token)
    data = sdk_call(c.vps.os_templates)
    templates = data if isinstance(data, list) else data.get("templates", []) if isinstance(data, dict) else []

    if is_json_mode():
        print_json(templates)
        return

    rows = []
    for tpl in templates:
        rows.append({
            "id": tpl.get("id", tpl.get("template_id", "")),
            "name": tpl.get("name", ""),
            "os_family": tpl.get("os_family", ""),
        })

    print_table(rows, [
        ("id", "Template ID", 24), ("name", "Name", 30), ("os_family", "OS Family", 14),
    ])


# ══════════════════════════════════════════════════════════════════
# Snapshot Commands (cloud vps snapshots ...)
# ══════════════════════════════════════════════════════════════════

@snapshots_app.command("list")
def snapshots_list(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List snapshots for a VPS."""
    c = get_client(token)
    snaps = sdk_call(c.vps.snapshots, vps_id)

    if is_json_mode():
        print_json(snaps)
        return

    if not snaps:
        print("No snapshots.")
        return

    rows = []
    for s in snaps:
        rows.append({
            "name": s.get("snapshot_name", ""),
            "status": s.get("status", ""),
            "created": s.get("created_at", "")[:19],
            "desc": (s.get("description") or "")[:30],
        })

    print_table(rows, [
        ("name", "Name", 24), ("status", "Status", 12),
        ("created", "Created", 20), ("desc", "Description", 32),
    ])


@snapshots_app.command("create")
def snapshots_create(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    name: str = typer.Option(..., "--name", help="Snapshot name"),
    description: Optional[str] = typer.Option(None, "--description", help="Description"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create a point-in-time snapshot. Not a backup — stored on same server."""
    c = get_client(token)
    data = sdk_call(c.vps.create_snapshot, vps_id, name=name, description=description)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Snapshot created: {data.get('snapshot_name', name)} (status: {data.get('status', '?')})")


@snapshots_app.command("delete")
def snapshots_delete(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    name: str = typer.Option(..., "--name", help="Snapshot name"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Delete a snapshot."""
    if not confirm:
        print(f"This will permanently delete snapshot '{name}' from VPS {vps_id}.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.vps.delete_snapshot, vps_id, name)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Snapshot '{name}' deleted.")


@snapshots_app.command("rollback")
def snapshots_rollback(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    name: str = typer.Option(..., "--name", help="Snapshot name to rollback to"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Rollback VPS to a snapshot. DESTRUCTIVE — data after snapshot is lost. VPS must be stopped."""
    if not confirm:
        print(f"WARNING: This will rollback VPS {vps_id} to snapshot '{name}'.")
        print("All data written after the snapshot will be PERMANENTLY LOST.")
        print("The VPS must be stopped before rollback.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.vps.rollback_snapshot, vps_id, name)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Rollback complete. Start the VPS to resume.")


# ══════════════════════════════════════════════════════════════════
# Backup Commands (cloud vps backups ...)
# ══════════════════════════════════════════════════════════════════

@backups_app.command("list")
def backups_list(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List off-site backups for a VPS."""
    c = get_client(token)
    data = sdk_call(c.vps.backups, vps_id)

    if is_json_mode():
        print_json(data)
        return

    if not data:
        print("No backups.")
        return

    rows = []
    for b in data:
        rows.append({
            "id": str(b.get("backup_id", ""))[:12],
            "type": b.get("backup_type", ""),
            "size": f"{b.get('size_gb', 0) or 0:.2f} GB",
            "status": b.get("status", ""),
            "created": b.get("started_at", "")[:19],
            "expires": (b.get("expires_at") or "")[:10],
        })

    print_table(rows, [
        ("id", "ID", 14), ("type", "Type", 10), ("size", "Size", 10),
        ("status", "Status", 12), ("created", "Created", 20), ("expires", "Expires", 12),
    ])


@backups_app.command("create")
def backups_create(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Trigger a manual off-site backup. Runs asynchronously."""
    c = get_client(token)
    data = sdk_call(c.vps.create_backup, vps_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Backup queued: {data.get('backup_id', '?')} (status: {data.get('status', 'creating')})")
        print("Use 'cloud vps backups list' to check progress.")


@backups_app.command("delete")
def backups_delete(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    backup_id: str = typer.Option(..., "--backup-id", help="Backup ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Delete a backup from off-site storage (permanent)."""
    if not confirm:
        print(f"This will permanently delete backup {backup_id}.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.vps.delete_backup, vps_id, backup_id)
    if is_json_mode():
        print_json(data)
    else:
        print("Backup deleted.")


@backups_app.command("restore")
def backups_restore(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    backup_id: str = typer.Option(..., "--backup-id", help="Backup ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Restore VPS from backup. DESTRUCTIVE — replaces current disk. VPS must be stopped."""
    if not confirm:
        print(f"WARNING: This will replace VPS {vps_id} disk with backup {backup_id}.")
        print("All current data will be PERMANENTLY LOST.")
        print("The VPS must be stopped before restore.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    # Note: restore currently returns 501 until restore worker is built.
    data = sdk_call(c.vps.restore_backup, vps_id, backup_id)
    if is_json_mode():
        print_json(data)
    else:
        print(data.get("message", "Restore queued."))


@backups_app.command("usage")
def backups_usage(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show backup storage usage for a VPS."""
    c = get_client(token)
    data = sdk_call(c.vps.backup_usage, vps_id)
    if is_json_mode():
        print_json(data)
    else:
        print_object(data, [
            ("total_backups", "Backups"), ("total_size_gb", "Total Size (GB)"),
        ])


# ── Backup Policy (cloud vps backups policy ...) ─────────────────

@backups_policy_app.command("get")
def policy_get(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Get backup policy for a VPS."""
    c = get_client(token)
    data = sdk_call(c.vps.backup_policy, vps_id)
    policy = data.get("policy") if isinstance(data, dict) else data

    if is_json_mode():
        print_json(policy)
        return

    if not policy:
        print("No backup policy configured.")
        return

    print_object(policy, [
        ("enabled", "Enabled"), ("frequency", "Frequency"),
        ("time_of_day", "Time (UTC)"), ("day_of_week", "Day of Week"),
        ("retention_days", "Retention (days)"),
        ("next_backup_at", "Next Backup"), ("last_backup_at", "Last Backup"),
    ])


@backups_policy_app.command("set")
def policy_set(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    frequency: str = typer.Option("daily", "--frequency", help="daily or weekly"),
    time: str = typer.Option("03:00", "--time", help="Time of day (UTC, HH:MM)"),
    retention: int = typer.Option(7, "--retention", help="Days to keep backups (1-90)"),
    day: Optional[int] = typer.Option(None, "--day", help="Day of week (0=Mon, for weekly)"),
    enabled: bool = typer.Option(True, "--enabled/--disabled", help="Enable/disable"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Set or update backup policy for a VPS."""
    c = get_client(token)
    data = sdk_call(c.vps.set_backup_policy, vps_id,
                    enabled=enabled, frequency=frequency,
                    time_of_day=time, day_of_week=day,
                    retention_days=retention)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Backup policy saved. Next backup: {data.get('next_backup_at', '?')}")


@backups_policy_app.command("remove")
def policy_remove(
    vps_id: str = typer.Argument(..., help="VPS ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Remove backup policy (stops automatic backups)."""
    if not confirm:
        print("This will remove the backup policy and stop automatic backups.")
        print("Existing backups will not be deleted.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.vps.delete_backup_policy, vps_id)
    if is_json_mode():
        print_json(data)
    else:
        print("Backup policy removed.")
