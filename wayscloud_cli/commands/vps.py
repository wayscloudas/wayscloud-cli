"""
cloud vps commands — VPS provisioning and control.
"""

import typer
from typing import Optional

from ..sdk import get_client, sdk_call
from ..output import print_table, print_object, print_json, is_json_mode

app = typer.Typer(help="Virtual Private Servers")


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
        })

    print_table(rows, [
        ("id", "ID", 14),
        ("hostname", "Hostname", 24),
        ("status", "Status", 12),
        ("ip", "IP", 16),
        ("plan", "Plan", 16),
        ("region", "Region", 8),
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
    print_object(data, [
        ("id", "ID"), ("hostname", "Hostname"), ("status", "Status"),
        ("power_state", "Power"), ("ipv4_address", "IPv4"), ("ipv6_address", "IPv6"),
        ("os_template", "OS"), ("plan_code", "Plan"), ("region", "Region"),
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
