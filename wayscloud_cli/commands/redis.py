"""
cloud redis commands — Redis-as-a-Service management.
"""

import typer
from typing import Optional

from ..sdk import get_client, sdk_call
from ..output import print_table, print_object, print_json, is_json_mode

app = typer.Typer(help="Managed Redis")


@app.command("list")
def list_instances(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List Redis instances."""
    c = get_client(token)
    data = sdk_call(c.redis.list)
    instances = data if isinstance(data, list) else data.get("instances", []) if isinstance(data, dict) else []

    if is_json_mode():
        print_json(instances)
        return

    if not instances:
        print("No Redis instances found.")
        return

    rows = [{"id": str(i.get("id", ""))[:12], "name": i.get("name", ""), "plan": i.get("plan", ""),
             "status": i.get("status", ""), "endpoint": i.get("endpoint", ""),
             "created_at": i.get("created_at", "")} for i in instances]

    print_table(rows, [
        ("id", "ID", 14), ("name", "Name", 20), ("plan", "Plan", 16),
        ("status", "Status", 10), ("endpoint", "Endpoint", 24), ("created_at", "Created", 20),
    ])


@app.command("create")
def create_instance(
    name: str = typer.Argument(..., help="Instance name"),
    plan: str = typer.Option("redis-starter", "--plan", help="Redis plan"),
    region: str = typer.Option("no", "--region", help="Region"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create a Redis instance."""
    c = get_client(token)
    data = sdk_call(c.redis.create, name, plan=plan, region=region)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Redis instance {name} created.")


@app.command("info")
def instance_info(
    instance_id: str = typer.Argument(..., help="Instance ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show Redis instance details and credentials."""
    c = get_client(token)
    data = sdk_call(c.redis.get, instance_id)

    # Merge credentials if available
    try:
        creds = c.redis.credentials(instance_id)
        if isinstance(creds, dict):
            data.update(creds)
    except Exception as e:
        import sys
        print(f"Warning: could not fetch credentials: {e}", file=sys.stderr)

    print_object(data, [
        ("id", "ID"), ("name", "Name"), ("plan", "Plan"), ("status", "Status"),
        ("endpoint", "Endpoint"), ("port", "Port"), ("region", "Region"),
        ("memory_mb", "Memory (MB)"), ("host", "Host"), ("password", "Password"),
        ("connection_string", "Connection String"), ("created_at", "Created"),
    ])


@app.command("delete")
def delete_instance(
    instance_id: str = typer.Argument(..., help="Instance ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
):
    """Delete a Redis instance (permanent)."""
    if not confirm:
        print(f"This will permanently delete Redis instance {instance_id} and all its data.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.redis.delete, instance_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Redis instance {instance_id}: deleted")


@app.command("plans")
def list_plans(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List available Redis plans."""
    c = get_client(token)
    data = sdk_call(c.redis.plans)
    plans = data if isinstance(data, list) else data.get("plans", []) if isinstance(data, dict) else []

    if is_json_mode():
        print_json(plans)
        return

    if not plans:
        print("No plans found.")
        return

    rows = [{"code": p.get("plan_code", p.get("code", "")), "memory": p.get("memory_mb", ""),
             "connections": p.get("max_connections", ""), "price": p.get("monthly_price", "")}
            for p in plans]

    print_table(rows, [
        ("code", "Plan", 20), ("memory", "Memory (MB)", 12),
        ("connections", "Max Conn", 10), ("price", "Price/mo", 12),
    ])
