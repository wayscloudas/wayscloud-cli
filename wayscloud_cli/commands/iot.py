"""
cloud iot commands — IoT device provisioning and group management.
"""

import typer
from typing import Optional

from ..sdk import get_client, sdk_call
from ..output import print_table, print_object, print_json, is_json_mode

app = typer.Typer(help="IoT platform")


@app.command("devices")
def list_devices(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List IoT devices."""
    c = get_client(token)
    data = sdk_call(c.iot.devices)
    devices = data if isinstance(data, list) else data.get("devices", []) if isinstance(data, dict) else []

    if is_json_mode():
        print_json(devices)
        return

    if not devices:
        print("No devices found.")
        return

    rows = [{"device_id": d.get("device_id", ""), "name": d.get("name", ""),
             "is_active": str(d.get("is_active", "")), "device_type": d.get("device_type", ""),
             "created_at": d.get("created_at", "")} for d in devices]

    print_table(rows, [
        ("device_id", "Device ID", 20), ("name", "Name", 20), ("is_active", "Active", 8),
        ("device_type", "Type", 14), ("created_at", "Created", 20),
    ])


@app.command("devices-create")
def create_device(
    device_id: str = typer.Option(..., "--device-id", help="Device ID"),
    name: str = typer.Option(..., "--name", help="Device name"),
    device_type: Optional[str] = typer.Option(None, "--type", help="Device type"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Register a new IoT device."""
    c = get_client(token)
    data = sdk_call(c.iot.create_device, device_id, name, device_type=device_type)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Device registered: {device_id}")
        print_object(data, [("device_id", "Device ID"), ("name", "Name"),
                            ("device_type", "Type"), ("is_active", "Active")])


@app.command("devices-info")
def device_info(
    device_id: str = typer.Argument(..., help="Device ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show device details and MQTT credentials."""
    c = get_client(token)
    data = sdk_call(c.iot.get_device, device_id)

    # Merge credentials if available
    try:
        creds = c.iot.device_credentials(device_id)
        if isinstance(creds, dict):
            data.update(creds)
    except Exception as e:
        import sys
        print(f"Warning: could not fetch credentials: {e}", file=sys.stderr)

    print_object(data, [
        ("device_id", "Device ID"), ("name", "Name"), ("device_type", "Type"),
        ("is_active", "Active"), ("last_seen", "Last Seen"),
        ("username", "MQTT Username"), ("password", "MQTT Password"),
        ("client_id", "MQTT Client ID"), ("broker_url", "Broker URL"),
        ("port", "Broker Port"), ("created_at", "Created"),
    ])


@app.command("devices-delete")
def delete_device(
    device_id: str = typer.Argument(..., help="Device ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
):
    """Delete an IoT device."""
    if not confirm:
        print(f"This will delete device {device_id} and all its data.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.iot.delete_device, device_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Device {device_id}: deleted")


@app.command("groups")
def list_groups(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List device groups."""
    c = get_client(token)
    data = sdk_call(c.iot.groups)
    groups = data if isinstance(data, list) else data.get("groups", []) if isinstance(data, dict) else []

    if is_json_mode():
        print_json(groups)
        return

    if not groups:
        print("No groups found.")
        return

    rows = [{"id": str(g.get("id", "")), "name": g.get("name", ""),
             "description": g.get("description", ""), "devices": str(g.get("device_count", ""))}
            for g in groups]

    print_table(rows, [
        ("id", "ID", 14), ("name", "Name", 20),
        ("description", "Description", 30), ("devices", "Devices", 8),
    ])


@app.command("groups-create")
def create_group(
    name: str = typer.Option(..., "--name", help="Group name"),
    description: Optional[str] = typer.Option(None, "--description", help="Description"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create a device group."""
    c = get_client(token)
    data = sdk_call(c.iot.create_group, name, description=description)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Group created: {name}")


@app.command("groups-delete")
def delete_group(
    group_id: str = typer.Argument(..., help="Group ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
):
    """Delete a device group."""
    if not confirm:
        print(f"This will delete group {group_id}.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.iot.delete_group, group_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Group {group_id}: deleted")
