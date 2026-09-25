"""
cloud iot commands — IoT device, group, rule, alarm, and notification management.
"""

import typer
from typing import Optional, List

from ..sdk import get_client, sdk_call
from ..output import print_table, print_object, print_json, is_json_mode

app = typer.Typer(help="IoT platform")

# ── Sub-groups ───────────────────────────────────────────────────
alarms_app = typer.Typer(help="Alarm management")
rules_app = typer.Typer(help="Alarm rules")
profiles_app = typer.Typer(help="Device profiles")
notifications_app = typer.Typer(help="Notification channels and policies")

app.add_typer(alarms_app, name="alarms")
app.add_typer(rules_app, name="rules")
app.add_typer(profiles_app, name="profiles")
app.add_typer(notifications_app, name="notifications")


# ══════════════════════════════════════════════════════════════════
# Devices
# ══════════════════════════════════════════════════════════════════

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
    """Show device details."""
    c = get_client(token)
    data = sdk_call(c.iot.get_device, device_id)
    print_object(data, [
        ("device_id", "Device ID"), ("name", "Name"), ("device_type", "Type"),
        ("is_active", "Active"), ("last_seen", "Last Seen"), ("created_at", "Created"),
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


@app.command("devices-health")
def device_health(
    device_id: str = typer.Argument(..., help="Device ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Get device health score and breakdown."""
    c = get_client(token)
    data = sdk_call(c.iot.device_health, device_id)
    if is_json_mode():
        print_json(data)
    else:
        print_object(data, [("score", "Health Score"), ("status", "Status")])


@app.command("devices-telemetry")
def device_telemetry(
    device_id: str = typer.Argument(..., help="Device ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Get latest telemetry for a device."""
    c = get_client(token)
    data = sdk_call(c.iot.device_telemetry, device_id)
    if is_json_mode():
        print_json(data)
    else:
        if isinstance(data, dict):
            for key, val in data.items():
                print(f"  {key}: {val}")
        else:
            print(data)


# ══════════════════════════════════════════════════════════════════
# Groups
# ══════════════════════════════════════════════════════════════════

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


@app.command("groups-add-device")
def group_add_device(
    group_id: str = typer.Argument(..., help="Group ID"),
    device_ids: List[str] = typer.Argument(..., help="Device IDs to add"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Add devices to a group."""
    c = get_client(token)
    data = sdk_call(c.iot.add_devices_to_group, group_id, device_ids)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Added {len(device_ids)} device(s) to group {group_id}")


@app.command("groups-remove-device")
def group_remove_device(
    group_id: str = typer.Argument(..., help="Group ID"),
    device_id: str = typer.Argument(..., help="Device ID to remove"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Remove a device from a group."""
    c = get_client(token)
    data = sdk_call(c.iot.remove_device_from_group, group_id, device_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Device {device_id} removed from group {group_id}")


# ══════════════════════════════════════════════════════════════════
# Profiles
# ══════════════════════════════════════════════════════════════════

@profiles_app.command("list")
def list_profiles(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List device profiles."""
    c = get_client(token)
    data = sdk_call(c.iot.profiles)
    if is_json_mode():
        print_json(data)
        return
    profiles = data if isinstance(data, list) else []
    if not profiles:
        print("No profiles found.")
        return
    rows = [{"id": str(p.get("id", ""))[:12], "name": p.get("name", ""),
             "desc": (p.get("description") or "")[:30]}
            for p in profiles]
    print_table(rows, [("id", "ID", 14), ("name", "Name", 20), ("desc", "Description", 32)])


@profiles_app.command("create")
def create_profile(
    name: str = typer.Option(..., "--name", help="Profile name"),
    description: Optional[str] = typer.Option(None, "--description", help="Description"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create a device profile."""
    c = get_client(token)
    data = sdk_call(c.iot.create_profile, name, description=description)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Profile created: {name}")


@profiles_app.command("delete")
def delete_profile(
    profile_id: str = typer.Argument(..., help="Profile ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Delete a device profile."""
    if not confirm:
        print(f"This will delete profile {profile_id}.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)
    c = get_client(token)
    data = sdk_call(c.iot.delete_profile, profile_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Profile {profile_id}: deleted")


@profiles_app.command("apply")
def apply_profile(
    profile_id: str = typer.Argument(..., help="Profile ID"),
    device_id: str = typer.Argument(..., help="Device ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Apply a profile to a device."""
    c = get_client(token)
    data = sdk_call(c.iot.apply_profile, profile_id, device_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Profile {profile_id} applied to device {device_id}")


# ══════════════════════════════════════════════════════════════════
# Rules
# ══════════════════════════════════════════════════════════════════

@rules_app.command("list")
def list_rules(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List alarm rules."""
    c = get_client(token)
    data = sdk_call(c.iot.rules)
    rules = data if isinstance(data, list) else []
    if is_json_mode():
        print_json(rules)
        return
    if not rules:
        print("No rules found.")
        return
    rows = [{"id": str(r.get("id", ""))[:12], "name": r.get("name", ""),
             "type": r.get("rule_type", ""), "severity": r.get("severity", ""),
             "enabled": str(r.get("is_enabled", ""))}
            for r in rules]
    print_table(rows, [("id", "ID", 14), ("name", "Name", 20), ("type", "Type", 14),
                       ("severity", "Severity", 10), ("enabled", "On", 5)])


@rules_app.command("create")
def create_rule(
    name: str = typer.Option(..., "--name", help="Rule name"),
    rule_type: str = typer.Option(..., "--type", help="Rule type (missing_data, offline, threshold, etc.)"),
    severity: str = typer.Option("warning", "--severity", help="Severity level"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create an alarm rule."""
    c = get_client(token)
    data = sdk_call(c.iot.create_rule, name, rule_type, severity=severity)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Rule created: {name}")


@rules_app.command("delete")
def delete_rule(
    rule_id: str = typer.Argument(..., help="Rule ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Delete an alarm rule."""
    if not confirm:
        print(f"This will delete rule {rule_id}.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)
    c = get_client(token)
    data = sdk_call(c.iot.delete_rule, rule_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Rule {rule_id}: deleted")


@rules_app.command("enable")
def enable_rule(
    rule_id: str = typer.Argument(..., help="Rule ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Enable an alarm rule."""
    c = get_client(token)
    data = sdk_call(c.iot.enable_rule, rule_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Rule {rule_id}: enabled")


@rules_app.command("disable")
def disable_rule(
    rule_id: str = typer.Argument(..., help="Rule ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Disable an alarm rule."""
    c = get_client(token)
    data = sdk_call(c.iot.disable_rule, rule_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Rule {rule_id}: disabled")


# ══════════════════════════════════════════════════════════════════
# Alarms
# ══════════════════════════════════════════════════════════════════

@alarms_app.command("list")
def list_alarms(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    severity: Optional[str] = typer.Option(None, "--severity", help="Filter by severity"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List alarms."""
    c = get_client(token)
    data = sdk_call(c.iot.alarms, status=status, severity=severity)
    alarms = data if isinstance(data, list) else []
    if is_json_mode():
        print_json(alarms)
        return
    if not alarms:
        print("No alarms.")
        return
    rows = [{"id": str(a.get("id", ""))[:12], "status": a.get("status", ""),
             "severity": a.get("severity", ""), "device": a.get("device_id", ""),
             "rule": a.get("rule_name", ""), "created": a.get("created_at", "")[:19]}
            for a in alarms]
    print_table(rows, [("id", "ID", 14), ("status", "Status", 12), ("severity", "Sev", 10),
                       ("device", "Device", 16), ("rule", "Rule", 20), ("created", "Created", 20)])


@alarms_app.command("summary")
def alarm_summary(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Get alarm counts by status and severity."""
    c = get_client(token)
    data = sdk_call(c.iot.alarm_summary)
    if is_json_mode():
        print_json(data)
    else:
        print_object(data, [("active", "Active"), ("acknowledged", "Acknowledged"),
                            ("resolved", "Resolved"), ("total", "Total")])


@alarms_app.command("acknowledge")
def ack_alarm(
    alarm_id: str = typer.Argument(..., help="Alarm ID"),
    note: Optional[str] = typer.Option(None, "--note", help="Note"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Acknowledge an alarm."""
    c = get_client(token)
    data = sdk_call(c.iot.acknowledge_alarm, alarm_id, note=note)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Alarm {alarm_id}: acknowledged")


@alarms_app.command("resolve")
def resolve_alarm(
    alarm_id: str = typer.Argument(..., help="Alarm ID"),
    note: Optional[str] = typer.Option(None, "--note", help="Note"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Resolve an alarm."""
    c = get_client(token)
    data = sdk_call(c.iot.resolve_alarm, alarm_id, note=note)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Alarm {alarm_id}: resolved")


# ══════════════════════════════════════════════════════════════════
# Notifications
# ══════════════════════════════════════════════════════════════════

@notifications_app.command("channels")
def list_channels(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List notification channels."""
    c = get_client(token)
    data = sdk_call(c.iot.notification_channels)
    channels = data if isinstance(data, list) else []
    if is_json_mode():
        print_json(channels)
        return
    if not channels:
        print("No notification channels.")
        return
    rows = [{"id": str(ch.get("id", ""))[:12], "name": ch.get("name", ""),
             "type": ch.get("channel_type", ""), "enabled": str(ch.get("is_enabled", ""))}
            for ch in channels]
    print_table(rows, [("id", "ID", 14), ("name", "Name", 20), ("type", "Type", 10), ("enabled", "On", 5)])


@notifications_app.command("channels-test")
def test_channel(
    channel_id: str = typer.Argument(..., help="Channel ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Send a test notification through a channel."""
    c = get_client(token)
    data = sdk_call(c.iot.test_notification_channel, channel_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Test notification sent via channel {channel_id}")


@notifications_app.command("policies")
def list_policies(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List notification policies."""
    c = get_client(token)
    data = sdk_call(c.iot.notification_policies)
    policies = data if isinstance(data, list) else []
    if is_json_mode():
        print_json(policies)
        return
    if not policies:
        print("No notification policies.")
        return
    rows = [{"id": str(p.get("id", ""))[:12], "name": p.get("name", ""),
             "enabled": str(p.get("is_enabled", ""))}
            for p in policies]
    print_table(rows, [("id", "ID", 14), ("name", "Name", 24), ("enabled", "On", 5)])


# ══════════════════════════════════════════════════════════════════
# MQTT & Subscription
# ══════════════════════════════════════════════════════════════════

@app.command("mqtt")
def mqtt_credentials(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Get MQTT broker connection details."""
    c = get_client(token)
    data = sdk_call(c.iot.mqtt_credentials)
    if is_json_mode():
        print_json(data)
    else:
        print_object(data, [("broker", "Broker"), ("port", "Port"),
                            ("username", "Username"), ("password", "Password"),
                            ("client_id", "Client ID")])


@app.command("subscription")
def subscription(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show current IoT plan and usage."""
    c = get_client(token)
    data = sdk_call(c.iot.subscription)
    if is_json_mode():
        print_json(data)
    else:
        print_object(data, [("plan", "Plan"), ("device_limit", "Device Limit"),
                            ("device_count", "Devices Used"), ("status", "Status")])
