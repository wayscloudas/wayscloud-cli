"""
SDK integration layer.

Provides get_client() to create a WaysCloudClient from resolved token.
All CLI commands use this instead of raw HTTP calls.
"""

import sys
from typing import Optional

from wayscloud import WaysCloudClient, WaysCloudError, AuthenticationError, NotFoundError

from .config import resolve_token, API_BASE
from .output import is_json_mode

import json as json_mod


def get_client(token: Optional[str] = None) -> WaysCloudClient:
    """Resolve token and return SDK client. Exits on auth failure."""
    resolved = resolve_token(token)
    if not resolved:
        _exit_error("not_authenticated", "Not logged in. Run: cloud login --token <pat>", 2)

    return WaysCloudClient(token=resolved, base_url=API_BASE)


def sdk_call(fn, *args, **kwargs):
    """Execute an SDK method with consistent error handling.

    Catches WaysCloudError and maps to CLI exit codes:
      AuthenticationError → exit 2
      NotFoundError → exit 1
      Other → exit 3
    """
    try:
        return fn(*args, **kwargs)
    except AuthenticationError as e:
        _exit_error("auth_error", e.message, 2)
    except NotFoundError as e:
        _exit_error("not_found", e.message, 1)
    except WaysCloudError as e:
        _exit_error("api_error", e.message, 3)


def _exit_error(code: str, message: str, exit_code: int):
    if is_json_mode():
        err = {"error": code, "code": exit_code, "message": message}
        print(json_mod.dumps(err), file=sys.stderr)
    else:
        print(f"Error: {message}", file=sys.stderr)
    sys.exit(exit_code)
