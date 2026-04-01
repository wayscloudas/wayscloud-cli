"""
cloud app commands — App Platform provisioning and control.
"""

import typer
from typing import Optional

from ..sdk import get_client, sdk_call
from ..output import print_table, print_object, print_json, is_json_mode

app = typer.Typer(help="App platform")


@app.command("list")
def list_apps(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List your apps."""
    c = get_client(token)
    data = sdk_call(c.apps.list)
    apps_list = data if isinstance(data, list) else data.get("apps", []) if isinstance(data, dict) else []

    if is_json_mode():
        print_json(apps_list)
        return

    if not apps_list:
        print("No apps found.")
        return

    rows = [{"id": str(a.get("id", ""))[:14], "name": a.get("name", ""),
             "status": a.get("status", ""), "plan": a.get("plan", a.get("plan_code", "")),
             "url": a.get("default_url", ""), "created_at": a.get("created_at", "")}
            for a in apps_list]

    print_table(rows, [
        ("id", "ID", 14), ("name", "Name", 20), ("status", "Status", 10),
        ("plan", "Plan", 16), ("url", "URL", 30), ("created_at", "Created", 20),
    ])


@app.command("create")
def create_app(
    name: str = typer.Argument(..., help="App name"),
    plan: str = typer.Option("app-basic", "--plan", help="Plan code"),
    region: str = typer.Option("no", "--region", help="Region"),
    port: int = typer.Option(8080, "--port", help="Application port"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create a new app."""
    c = get_client(token)
    data = sdk_call(c.apps.create, name, plan=plan, region=region, port=port)
    if is_json_mode():
        print_json(data)
    else:
        print(f"App created: {data.get('name', name)}")
        print_object(data, [("id", "ID"), ("name", "Name"), ("status", "Status"),
                            ("plan", "Plan"), ("default_url", "URL")])


@app.command("info")
def info_app(
    app_id: str = typer.Argument(..., help="App ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show app details."""
    c = get_client(token)
    data = sdk_call(c.apps.get, app_id)
    print_object(data, [
        ("id", "ID"), ("name", "Name"), ("status", "Status"), ("plan", "Plan"),
        ("region", "Region"), ("port", "Port"), ("default_url", "URL"),
        ("image_uri", "Image"), ("created_at", "Created"),
    ])


@app.command("delete")
def delete_app(
    app_id: str = typer.Argument(..., help="App ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation"),
):
    """Delete an app (permanent)."""
    if not confirm:
        print(f"This will permanently delete app {app_id} and all its data.")
        print("Use --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.apps.delete, app_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"App {app_id}: deleted")


@app.command("deploy")
def deploy_app(
    app_id: str = typer.Argument(..., help="App ID"),
    image: str = typer.Option(..., "--image", help="Container image URI"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Deploy an app from a container image."""
    c = get_client(token)
    data = sdk_call(c.apps.deploy, app_id, image)
    if is_json_mode():
        print_json(data)
    else:
        print(f"App {app_id}: deploying image {image}")


@app.command("start")
def start_app(
    app_id: str = typer.Argument(..., help="App ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Start an app."""
    c = get_client(token)
    data = sdk_call(c.apps.start, app_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"App {app_id}: {data.get('message', 'starting')}")


@app.command("stop")
def stop_app(
    app_id: str = typer.Argument(..., help="App ID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Stop an app."""
    c = get_client(token)
    data = sdk_call(c.apps.stop, app_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"App {app_id}: {data.get('message', 'stopping')}")
