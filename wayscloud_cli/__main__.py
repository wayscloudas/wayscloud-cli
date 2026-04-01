"""
WAYSCloud CLI entry point.

Binary name: cloud (C21)
Package name: wayscloud-cli (C21)

Principle: CLI = provisioning + control, NOT observability.
"""

import typer

from . import __version__
from .output import set_json_mode, set_no_color
from .commands.login import app as login_app, login, logout, whoami
from .commands.vps import app as vps_app
from .commands.shell import app as shell_app
from .commands.dns import app as dns_app
from .commands.storage import app as storage_app
from .commands.db import app as db_app
from .commands.redis import app as redis_app
from .commands.app import app as app_platform_app
from .commands.iot import app as iot_app

app = typer.Typer(
    name="cloud",
    help="WAYSCloud CLI",
    no_args_is_help=True,
    add_completion=True,
)


# Global options callback
@app.callback(invoke_without_command=True)
def global_options(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output as JSON (C11)"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colors"),
    version: bool = typer.Option(False, "--version", help="Show version"),
):
    """WAYSCloud CLI"""
    if version:
        print(f"WAYSCloud CLI {__version__}")
        raise typer.Exit()

    set_json_mode(json_output)
    set_no_color(no_color)

    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
        raise typer.Exit()


# Register command groups
app.add_typer(login_app, name="auth", help="Authentication")
app.add_typer(vps_app, name="vps", help="Virtual Private Servers")
app.add_typer(dns_app, name="dns", help="DNS zones and records")
app.add_typer(storage_app, name="storage", help="Object storage (S3)")
app.add_typer(db_app, name="db", help="Managed databases")
app.add_typer(redis_app, name="redis", help="Managed Redis")
app.add_typer(app_platform_app, name="app", help="App platform")
app.add_typer(iot_app, name="iot", help="IoT platform")
app.add_typer(shell_app, name="shell", help="CloudShell")

# Top-level shortcuts for login/logout/whoami
app.command("login")(login)
app.command("logout")(logout)
app.command("whoami")(whoami)


def main():
    app()


if __name__ == "__main__":
    main()
