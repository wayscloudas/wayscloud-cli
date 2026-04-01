"""
cloud login / logout / whoami commands.

login validates token against API before saving.
"""

import typer

from wayscloud import WaysCloudClient, AuthenticationError, WaysCloudError

from ..config import resolve_token, save_token, delete_token, API_BASE
from ..output import print_object, print_error, is_json_mode, print_json

app = typer.Typer(help="Authentication")


@app.command()
def login(
    token: str = typer.Option(..., "--token", help="PAT token from portal"),
):
    """Login with a CLI token from the WAYSCloud portal."""
    if not token.startswith("wayscloud_pat_"):
        print_error("invalid_token", "Invalid token format. Expected: wayscloud_pat_...", exit_code=2)

    # Validate against API using SDK
    try:
        client = WaysCloudClient(token=token, base_url=API_BASE)
        profile = client.account.profile()
    except AuthenticationError:
        print_error("invalid_token", "Token is invalid or expired", exit_code=2)
    except WaysCloudError as e:
        print_error("api_error", str(e), exit_code=3)

    # Token is valid — save it
    save_token(token)

    if is_json_mode():
        print_json({"status": "ok", "message": "Login successful"})
    else:
        from .. import __version__
        print(f"WAYSCloud CLI v{__version__}")
        print(f"Logged in as: {profile.get('email', 'unknown')}")
        print(f"Customer: {profile.get('customer_id', 'unknown')}")
        print("Token saved to ~/.wayscloud/credentials")


@app.command()
def logout():
    """Remove saved credentials."""
    if delete_token():
        print("Logged out. Token removed.")
    else:
        print("No saved credentials found.")


@app.command()
def whoami(
    token: str = typer.Option(None, "--token", help="Override token"),
):
    """Show current authenticated identity."""
    resolved = resolve_token(token)
    if not resolved:
        print_error("not_authenticated", "Not logged in. Run: cloud login --token <pat>", exit_code=2)

    try:
        client = WaysCloudClient(token=resolved, base_url=API_BASE)
        profile = client.account.profile()
    except AuthenticationError:
        print_error("auth_error", "Token is invalid or expired", exit_code=2)
    except WaysCloudError as e:
        print_error("api_error", str(e), exit_code=3)

    print_object(profile, [
        ("customer_id", "Customer ID"),
        ("email", "Email"),
        ("name", "Name"),
        ("customer_type", "Type"),
    ])
