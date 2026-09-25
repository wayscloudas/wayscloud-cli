"""
cloud app commands — App Platform provisioning and control.
"""

import typer
from typing import Optional, List

from ..sdk import get_client, sdk_call
from ..output import print_table, print_object, print_json, is_json_mode

app = typer.Typer(help="App platform")

# ── Env sub-group ────────────────────────────────────────────────
env_app = typer.Typer(help="Environment variables")
app.add_typer(env_app, name="env")


@env_app.command("list")
def env_list(
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List environment variable keys for an app."""
    c = get_client(token)
    env = sdk_call(c.apps.env_vars, app_id)

    if is_json_mode():
        print_json(env)
        return

    if not env:
        print("No environment variables set.")
        return

    print(f"Environment variables ({len(env)}):\n")
    for key in sorted(env.keys()):
        print(f"  {key}=***")


@env_app.command("set")
def env_set(
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
    pairs: List[str] = typer.Argument(..., help="KEY=value pairs"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Set one or more environment variables."""
    c = get_client(token)

    for pair in pairs:
        if "=" not in pair:
            print(f"Error: Invalid format '{pair}'. Use KEY=value", err=True)
            raise typer.Exit(code=1)
        key, _, value = pair.partition("=")
        sdk_call(c.apps.set_env, app_id, key.strip(), value)
        print(f"  Set: {key.strip()}")

    print(f"\n{len(pairs)} variable(s) updated.")


@env_app.command("unset")
def env_unset(
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
    keys: List[str] = typer.Argument(..., help="Variable names to remove"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Remove one or more environment variables."""
    c = get_client(token)

    for key in keys:
        sdk_call(c.apps.unset_env, app_id, key)
        print(f"  Removed: {key}")

    print(f"\n{len(keys)} variable(s) removed.")


# ── Core commands ────────────────────────────────────────────────

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

    rows = [{"id": str(a.get("id", "")), "short_id": a.get("short_id", ""),
             "name": a.get("name", ""),
             "status": a.get("status", ""), "plan": a.get("plan", a.get("plan_code", "")),
             "url": a.get("default_url", ""), "created_at": a.get("created_at", "")}
            for a in apps_list]

    print_table(rows, [
        ("id", "ID", 30), ("short_id", "Short", 10), ("name", "Name", 20),
        ("status", "Status", 10), ("plan", "Plan", 16),
        ("url", "URL", 30), ("created_at", "Created", 20),
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
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
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
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
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
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
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
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
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
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Stop an app."""
    c = get_client(token)
    data = sdk_call(c.apps.stop, app_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"App {app_id}: {data.get('message', 'stopping')}")


@app.command("restart")
def restart_app(
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Restart an app."""
    c = get_client(token)
    data = sdk_call(c.apps.restart, app_id)
    if is_json_mode():
        print_json(data)
    else:
        print(f"App {app_id}: {data.get('message', 'restarting')}")


@app.command("logs")
def logs_app(
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
    lines: int = typer.Option(100, "--lines", "-n", help="Number of lines"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show app logs."""
    c = get_client(token)
    data = sdk_call(c.apps.logs, app_id, lines=lines)

    if is_json_mode():
        print_json(data)
        return

    log_lines = data if isinstance(data, list) else []
    if not log_lines:
        print("No logs available.")
        return

    for line in log_lines:
        if isinstance(line, dict):
            ts = line.get("timestamp", "")
            msg = line.get("message", line.get("log", str(line)))
            print(f"{ts}  {msg}")
        else:
            print(line)


@app.command("plans")
def list_plans(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List available app plans."""
    c = get_client(token)
    data = sdk_call(c.apps.plans)
    plans_list = data if isinstance(data, list) else []

    if is_json_mode():
        print_json(plans_list)
        return

    if not plans_list:
        print("No plans available.")
        return

    rows = [{"code": p.get("code", p.get("plan_code", "")),
             "name": p.get("name", ""),
             "cpu": str(p.get("cpu", "")),
             "memory": str(p.get("memory_mb", p.get("memory", ""))),
             "price": str(p.get("price_monthly", p.get("price", "")))}
            for p in plans_list]

    print_table(rows, [
        ("code", "Code", 20), ("name", "Name", 20), ("cpu", "CPU", 6),
        ("memory", "Memory MB", 10), ("price", "Price/mo", 10),
    ])


# ── GitHub auto-deploy sub-group ────────────────────────────────
auto_deploy_app = typer.Typer(help="GitHub auto-deploy")
app.add_typer(auto_deploy_app, name="auto-deploy")


def _print_secret_once(secret: str, webhook_url: str) -> None:
    """Format the one-time secret reveal for terminal output."""
    print()
    print("=" * 72)
    print("  This is the only time this secret is shown. Copy it now.")
    print("=" * 72)
    print(f"  Webhook URL:  {webhook_url}")
    print(f"  Secret:       {secret}")
    print( "  Content type: application/json")
    print( "  Events:       Just the push event")
    print("=" * 72)
    print()


@auto_deploy_app.command("status")
def auto_deploy_status(
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show GitHub auto-deploy configuration for an app."""
    c = get_client(token)
    data = sdk_call(c.apps.auto_deploy_get, app_id)

    if is_json_mode():
        print_json(data)
        return

    if not data.get("configured"):
        print("Auto-deploy: not configured.")
        print(f"Webhook URL: {data.get('webhook_url', '')}")
        return

    print_object(data, [
        ("provider", "Provider"),
        ("repo_url", "Repository"),
        ("branch", "Branch"),
        ("auto_deploy_enabled", "Enabled"),
        ("secret_configured", "Per-app secret"),
        ("credential_linked", "Credential linked"),
        ("webhook_url", "Webhook URL"),
        ("last_push_event_at", "Last push"),
        ("last_auto_deploy_at", "Last deploy"),
        ("last_auto_deploy_commit", "Last commit"),
    ])
    if not data.get("secret_configured"):
        print()
        print("  [!] This app is using the legacy shared webhook secret.")
        print("      Run `cloud app auto-deploy rotate-secret <app>` to")
        print("      get a per-app secret only GitHub and this app know.")


@auto_deploy_app.command("enable")
def auto_deploy_enable(
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
    repo_url: str = typer.Option(..., "--repo", help="GitHub repository URL"),
    branch: str = typer.Option("main", "--branch", help="Branch to auto-deploy"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Enable GitHub auto-deploy for an app.

    First invocation generates a per-app webhook secret and prints it
    once. Re-invoking with new repo/branch keeps the existing secret.
    """
    c = get_client(token)
    data = sdk_call(
        c.apps.auto_deploy_configure,
        app_id, repo_url, branch=branch, auto_deploy_enabled=True,
    )

    if is_json_mode():
        print_json(data)
        return

    print(f"Auto-deploy enabled: {data.get('repo_url')}:{data.get('branch')}")
    secret = data.get("webhook_secret")
    if secret:
        _print_secret_once(secret, data.get("webhook_url", ""))
    else:
        print("Per-app webhook secret already configured — reusing existing.")


@auto_deploy_app.command("disable")
def auto_deploy_disable(
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Pause auto-deploy without clearing the repo configuration.

    Webhook secret is kept so re-enabling does not require updating
    GitHub. To delete the config entirely, use `cloud app auto-deploy
    remove` (not yet implemented — reconfigure with a new repo_url
    instead).
    """
    c = get_client(token)
    # Re-PUT with auto_deploy_enabled=false; backend preserves secret.
    current = sdk_call(c.apps.auto_deploy_get, app_id)
    if not current.get("configured"):
        print("Auto-deploy is not configured for this app.")
        raise typer.Exit(code=1)
    data = sdk_call(
        c.apps.auto_deploy_configure,
        app_id,
        repo_url=current["repo_url"],
        branch=current["branch"],
        auto_deploy_enabled=False,
    )
    if is_json_mode():
        print_json(data)
    else:
        print(f"Auto-deploy paused for {app_id}.")


@auto_deploy_app.command("rotate-secret")
def auto_deploy_rotate(
    app_id: str = typer.Argument(..., help="App ID, short ID, or name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
    confirm: bool = typer.Option(False, "--confirm",
                                 help="Skip interactive confirmation"),
):
    """Generate a new webhook secret. The previous one stops working."""
    if not confirm:
        print("This rotates the webhook secret immediately. Pushes from")
        print("GitHub will fail until you update the secret in the repo")
        print("webhook settings. Re-run with --confirm to proceed.")
        raise typer.Exit(code=1)

    c = get_client(token)
    data = sdk_call(c.apps.auto_deploy_rotate_secret, app_id)

    if is_json_mode():
        print_json(data)
        return

    secret = data.get("webhook_secret")
    if not secret:
        print("Error: response did not include a new secret.", err=True)
        raise typer.Exit(code=1)
    _print_secret_once(secret, data.get("webhook_url", ""))


@app.command("regions")
def list_regions(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List available app regions."""
    c = get_client(token)
    data = sdk_call(c.apps.regions)

    if is_json_mode():
        print_json(data)
        return

    regions_list = data if isinstance(data, list) else []
    if not regions_list:
        print("No regions available.")
        return

    for r in regions_list:
        code = r.get("code", r.get("region", ""))
        name = r.get("name", r.get("label", ""))
        print(f"  {code:<10} {name}")
