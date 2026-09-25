"""
cloud dns commands — DNS zone and record management.
"""

import typer
from typing import Optional

from ..sdk import get_client, sdk_call
from ..output import print_table, print_json, is_json_mode

app = typer.Typer(help="DNS zones and records")


@app.command("zones")
def list_zones(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List DNS zones."""
    c = get_client(token)
    data = sdk_call(c.dns.zones)
    zones = data if isinstance(data, list) else data.get("zones", []) if isinstance(data, dict) else []

    if is_json_mode():
        print_json(zones)
        return

    if not zones:
        print("No DNS zones found.")
        return

    rows = [{"name": z.get("name", ""), "status": z.get("status", ""),
             "records": z.get("record_count", ""), "dnssec": z.get("dnssec_enabled", "")}
            for z in zones]

    print_table(rows, [
        ("name", "Name", 24), ("status", "Status", 10),
        ("records", "Records", 8), ("dnssec", "DNSSEC", 8),
    ])


@app.command("zones-info")
def zone_info(
    zone_name: str = typer.Argument(..., help="Zone name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show details for a DNS zone."""
    c = get_client(token)
    data = sdk_call(c.dns.get, zone_name)
    if is_json_mode():
        print_json(data)
    else:
        from ..output import print_object
        print_object(data, [
            ("name", "Name"), ("status", "Status"), ("zone_type", "Type"),
            ("record_count", "Records"), ("dnssec_enabled", "DNSSEC"),
            ("created_at", "Created"),
        ])


@app.command("zones-create")
def create_zone(
    name: str = typer.Argument(..., help="Zone name"),
    zone_type: str = typer.Option("master", "--type", help="Zone type"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create a DNS zone."""
    c = get_client(token)
    data = sdk_call(c.dns.create_zone, name, zone_type=zone_type)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Zone {name} created.")


@app.command("zones-delete")
def delete_zone(
    name: str = typer.Argument(..., help="Zone name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
):
    """Delete a DNS zone (permanent)."""
    if not confirm:
        print(f"This will permanently delete zone {name} and all its records.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.dns.delete_zone, name)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Zone {name}: deleted")


@app.command("records")
def list_records(
    zone_name: str = typer.Argument(..., help="Zone name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List DNS records for a zone."""
    c = get_client(token)
    data = sdk_call(c.dns.records, zone_name)
    records = data if isinstance(data, list) else data.get("records", []) if isinstance(data, dict) else []

    if is_json_mode():
        print_json(records)
        return

    if not records:
        print("No records found.")
        return

    rows = [{"name": r.get("name", ""), "type": r.get("type", ""),
             "value": r.get("value", ""), "ttl": r.get("ttl", "")} for r in records]

    print_table(rows, [
        ("name", "Name", 20), ("type", "Type", 8),
        ("value", "Value", 30), ("ttl", "TTL", 8),
    ])


@app.command("records-create")
def create_record(
    zone_name: str = typer.Argument(..., help="Zone name"),
    record_type: str = typer.Option(..., "--type", help="Record type (A, AAAA, CNAME, MX, TXT, etc.)"),
    name: str = typer.Option("", "--name", help="Record name"),
    value: str = typer.Option(..., "--value", help="Record value"),
    ttl: int = typer.Option(3600, "--ttl", help="TTL in seconds"),
    priority: Optional[int] = typer.Option(None, "--priority", help="Priority (MX, SRV)"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create a DNS record."""
    c = get_client(token)
    data = sdk_call(c.dns.create_record, zone_name, record_type=record_type, value=value,
                    name=name, ttl=ttl, priority=priority)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Record created in {zone_name}.")


@app.command("records-update")
def update_record(
    zone_name: str = typer.Argument(..., help="Zone name"),
    record_id: str = typer.Argument(..., help="Record ID"),
    value: Optional[str] = typer.Option(None, "--value", help="New value"),
    ttl: Optional[int] = typer.Option(None, "--ttl", help="New TTL"),
    priority: Optional[int] = typer.Option(None, "--priority", help="New priority"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Update a DNS record."""
    kwargs = {}
    if value is not None:
        kwargs["value"] = value
    if ttl is not None:
        kwargs["ttl"] = ttl
    if priority is not None:
        kwargs["priority"] = priority

    if not kwargs:
        print("No fields to update. Use --value, --ttl, or --priority.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.dns.update_record, zone_name, record_id, **kwargs)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Record {record_id} updated.")


@app.command("records-delete")
def delete_record(
    zone_name: str = typer.Argument(..., help="Zone name"),
    record_id: str = typer.Argument(..., help="Record ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
):
    """Delete a DNS record (permanent)."""
    if not confirm:
        print(f"This will permanently delete record {record_id} from {zone_name}.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.dns.delete_record, zone_name, record_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Record {record_id}: deleted")


@app.command("dnssec-status")
def dnssec_status(
    zone_name: str = typer.Argument(..., help="Zone name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show DNSSEC status for a zone."""
    c = get_client(token)
    data = sdk_call(c.dns.dnssec_status, zone_name)
    if is_json_mode():
        print_json(data)
    else:
        from ..output import print_object
        print_object(data, [
            ("enabled", "Enabled"), ("ds_records", "DS Records"),
            ("algorithm", "Algorithm"), ("key_tag", "Key Tag"),
        ])


@app.command("dnssec-activate")
def dnssec_activate(
    zone_name: str = typer.Argument(..., help="Zone name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Activate DNSSEC for a zone."""
    c = get_client(token)
    data = sdk_call(c.dns.dnssec_activate, zone_name)
    if is_json_mode():
        print_json(data)
    else:
        print(f"DNSSEC activated for {zone_name}.")


@app.command("dnssec-deactivate")
def dnssec_deactivate(
    zone_name: str = typer.Argument(..., help="Zone name"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Deactivate DNSSEC for a zone."""
    if not confirm:
        print(f"This will deactivate DNSSEC for {zone_name}.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.dns.dnssec_deactivate, zone_name)
    if is_json_mode():
        print_json(data)
    else:
        print(f"DNSSEC deactivated for {zone_name}.")


@app.command("statistics")
def zone_statistics(
    zone_name: str = typer.Argument(..., help="Zone name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show zone statistics (query counts)."""
    c = get_client(token)
    data = sdk_call(c.dns.statistics, zone_name)
    if is_json_mode():
        print_json(data)
    else:
        from ..output import print_object
        print_object(data, [
            ("total_queries", "Total Queries"), ("queries_today", "Queries Today"),
            ("record_count", "Records"),
        ])
