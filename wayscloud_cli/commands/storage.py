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


@app.command("buckets-info")
def bucket_info(
    name: str = typer.Argument(..., help="Bucket name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show bucket details."""
    c = get_client(token)
    data = sdk_call(c.storage.get, name)
    if is_json_mode():
        print_json(data)
    else:
        print_object(data, [
            ("bucket_name", "Bucket"), ("tier", "Tier"), ("is_active", "Active"),
            ("is_public", "Public"), ("total_storage_gb", "Size (GB)"),
            ("total_objects", "Objects"), ("created_at", "Created"),
        ])


@app.command("keys")
def list_keys(
    bucket_name: str = typer.Argument(..., help="Bucket name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List API keys for a bucket."""
    c = get_client(token)
    data = sdk_call(c.storage.bucket_keys, bucket_name)
    keys = data if isinstance(data, list) else []
    if is_json_mode():
        print_json(keys)
        return
    if not keys:
        print("No keys found.")
        return
    rows = [{"id": str(k.get("id", ""))[:12], "name": k.get("name", ""),
             "access_key": k.get("access_key", ""), "created": k.get("created_at", "")}
            for k in keys]
    print_table(rows, [("id", "ID", 14), ("name", "Name", 20),
                       ("access_key", "Access Key", 24), ("created", "Created", 20)])


@app.command("keys-create")
def create_key(
    bucket_name: str = typer.Argument(..., help="Bucket name"),
    name: str = typer.Option(..., "--name", help="Key name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create an API key for a bucket. Shows secret key once."""
    c = get_client(token)
    data = sdk_call(c.storage.create_bucket_key, bucket_name, name)
    if is_json_mode():
        print_json(data)
    else:
        print_object(data, [("access_key", "Access Key"), ("secret_key", "Secret Key")])
        print("\n  Save the secret key now — it cannot be shown again.")


@app.command("keys-delete")
def delete_key(
    bucket_name: str = typer.Argument(..., help="Bucket name"),
    key_id: str = typer.Option(..., "--key-id", help="Key ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Delete a bucket API key (permanent)."""
    if not confirm:
        print(f"This will permanently revoke key {key_id}.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)
    c = get_client(token)
    data = sdk_call(c.storage.delete_bucket_key, bucket_name, key_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Key {key_id}: deleted")


@app.command("visibility")
def set_visibility(
    bucket_name: str = typer.Argument(..., help="Bucket name"),
    public: bool = typer.Option(False, "--public/--private", help="Set public or private"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Toggle bucket public/private access."""
    c = get_client(token)
    data = sdk_call(c.storage.set_visibility, bucket_name, public)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Bucket {bucket_name}: {'public' if public else 'private'}")


@app.command("tiers")
def list_tiers(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List available storage tiers."""
    c = get_client(token)
    data = sdk_call(c.storage.tiers)
    if is_json_mode():
        print_json(data)
        return
    tiers = data if isinstance(data, list) else []
    for t in tiers:
        name = t.get("name", t.get("tier", ""))
        desc = t.get("description", "")
        print(f"  {name:<16} {desc}")
