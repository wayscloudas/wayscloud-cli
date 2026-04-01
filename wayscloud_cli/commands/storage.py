"""
cloud storage commands — S3-compatible object storage.
"""

import typer
from typing import Optional

from ..sdk import get_client, sdk_call
from ..output import print_table, print_object, print_json, is_json_mode

app = typer.Typer(help="Object storage (S3)")


@app.command("buckets")
def list_buckets(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List storage buckets."""
    c = get_client(token)
    data = sdk_call(c.storage.buckets)
    buckets = data if isinstance(data, list) else data.get("buckets", []) if isinstance(data, dict) else []

    if is_json_mode():
        print_json(buckets)
        return

    if not buckets:
        print("No storage buckets found.")
        return

    rows = [{"bucket_name": b.get("bucket_name", ""), "tier": b.get("tier", ""),
             "is_active": b.get("is_active", ""), "size": b.get("total_storage_gb", ""),
             "objects": b.get("total_objects", ""), "created_at": b.get("created_at", "")}
            for b in buckets]

    print_table(rows, [
        ("bucket_name", "Bucket", 24), ("tier", "Tier", 12), ("is_active", "Active", 8),
        ("size", "Size (GB)", 12), ("objects", "Objects", 10), ("created_at", "Created", 20),
    ])


@app.command("buckets-create")
def create_bucket(
    name: str = typer.Argument(..., help="Bucket name"),
    tier: str = typer.Option("standard", "--tier", help="Storage tier"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create a storage bucket."""
    c = get_client(token)
    data = sdk_call(c.storage.create_bucket, name, tier=tier)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Bucket {name} created.")


@app.command("buckets-delete")
def delete_bucket(
    name: str = typer.Argument(..., help="Bucket name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
):
    """Delete a storage bucket (permanent)."""
    if not confirm:
        print(f"This will permanently delete bucket {name} and all its contents.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.storage.delete_bucket, name)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Bucket {name}: deleted")


@app.command("credentials")
def show_credentials(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show S3 credentials."""
    c = get_client(token)
    data = sdk_call(c.storage.credentials)
    print_object(data, [
        ("access_key", "Access Key"), ("secret_key", "Secret Key"),
        ("endpoint", "Endpoint"), ("region", "Region"),
    ])
