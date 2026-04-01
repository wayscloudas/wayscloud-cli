"""
Configuration and token resolution (C2, C3, C22, C24).

Token priority:
  1. --token flag
  2. WAYSCLOUD_TOKEN env var
  3. ~/.wayscloud/credentials file
"""

import json
import os
import stat
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".wayscloud"
CREDENTIALS_FILE = CONFIG_DIR / "credentials"
ENV_VAR = "WAYSCLOUD_TOKEN"

# API base URL (C25 — public endpoint)
API_BASE = os.environ.get("WAYSCLOUD_API_URL", "https://api.wayscloud.services")
SHELL_WS = "wss://shell.wayscloud.services/ws"


def resolve_token(explicit_token: Optional[str] = None) -> Optional[str]:
    """Resolve token using priority order (C3):
    1. Explicit --token flag
    2. WAYSCLOUD_TOKEN env var
    3. ~/.wayscloud/credentials file
    """
    # 1. Explicit flag
    if explicit_token:
        return explicit_token

    # 2. Environment variable
    env_token = os.environ.get(ENV_VAR)
    if env_token:
        return env_token

    # 3. Credentials file
    if CREDENTIALS_FILE.exists():
        try:
            data = json.loads(CREDENTIALS_FILE.read_text())
            return data.get("token")
        except (json.JSONDecodeError, OSError):
            return None

    return None


def save_token(token: str) -> None:
    """Save token to credentials file (C2, C24)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "version": 1,
        "token": token,
        "created_at": _now_iso(),
    }

    CREDENTIALS_FILE.write_text(json.dumps(data, indent=2))

    # chmod 600 (C24)
    CREDENTIALS_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)


def delete_token() -> bool:
    """Delete saved credentials. Returns True if file existed."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
        return True
    return False


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
