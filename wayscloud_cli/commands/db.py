"""
cloud db commands — Database-as-a-Service management.
"""

import typer
from typing import Optional

from ..sdk import get_client, sdk_call
from ..output import print_table, print_object, print_json, is_json_mode

app = typer.Typer(help="Managed databases")


@app.command("list")
def list_databases(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List your databases."""
    c = get_client(token)
    data = sdk_call(c.database.list)
    databases = data if isinstance(data, list) else data.get("databases", []) if isinstance(data, dict) else []

    if is_json_mode():
        print_json(databases)
        return

    if not databases:
        print("No databases found.")
        return

    rows = [{"name": d.get("name", ""), "type": d.get("type", ""), "tier": d.get("tier", ""),
             "status": d.get("status", ""), "size_mb": d.get("size_mb", ""),
             "created_at": d.get("created_at", "")} for d in databases]

    print_table(rows, [
        ("name", "Name", 20), ("type", "Type", 12), ("tier", "Tier", 10),
        ("status", "Status", 10), ("size_mb", "Size (MB)", 10), ("created_at", "Created", 20),
    ])


@app.command("create")
def create_database(
    name: str = typer.Argument(..., help="Database name"),
    db_type: str = typer.Option(..., "--type", help="Database type (postgresql/mariadb)"),
    tier: str = typer.Option("standard", "--tier", help="Database tier"),
    description: Optional[str] = typer.Option(None, "--description", help="Description"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create a database."""
    c = get_client(token)
    data = sdk_call(c.database.create, name, db_type=db_type, tier=tier, description=description)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Database {name} ({db_type}) created.")


@app.command("info")
def database_info(
    db_type: str = typer.Argument(..., help="Database type (postgresql/mariadb)"),
    name: str = typer.Argument(..., help="Database name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show database details and credentials."""
    c = get_client(token)
    data = sdk_call(c.database.get, db_type, name)

    # Merge credentials if available
    try:
        creds = c.database.credentials(db_type, name)
        if isinstance(creds, dict):
            data.update(creds)
    except Exception as e:
        import sys
        print(f"Warning: could not fetch credentials: {e}", file=sys.stderr)

    print_object(data, [
        ("name", "Name"), ("type", "Type"), ("tier", "Tier"), ("status", "Status"),
        ("size_mb", "Size (MB)"), ("host", "Host"), ("port", "Port"),
        ("username", "Username"), ("password", "Password"), ("database", "Database"),
        ("connection_string", "Connection String"), ("created_at", "Created"),
    ])


@app.command("delete")
def delete_database(
    db_type: str = typer.Argument(..., help="Database type (postgresql/mariadb)"),
    name: str = typer.Argument(..., help="Database name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
):
    """Delete a database (permanent)."""
    if not confirm:
        print(f"This will permanently delete database {name} ({db_type}) and all its data.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.database.delete, db_type, name)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Database {name}: deleted")
