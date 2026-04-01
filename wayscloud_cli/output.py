"""
Output formatting (C11, C12, C29).

--json is alias for --format json (C11).
list → array, info → object, error → {error, code, message} (C12).
"""

import json
import sys
from typing import Any, List, Optional

# Global state set by CLI flags
_json_mode = False
_no_color = False


def set_json_mode(enabled: bool) -> None:
    global _json_mode
    _json_mode = enabled


def set_no_color(enabled: bool) -> None:
    global _no_color
    _no_color = enabled


def is_json_mode() -> bool:
    return _json_mode


def print_json(data: Any) -> None:
    """Print data as JSON to stdout (C12)."""
    print(json.dumps(data, indent=2, default=str))


def print_table(rows: List[dict], columns: List[tuple]) -> None:
    """Print data as formatted table.

    Args:
        rows: List of dicts
        columns: List of (key, header, width) tuples
    """
    if _json_mode:
        print_json(rows)
        return

    if not rows:
        print("No results.")
        return

    try:
        from rich.console import Console
        from rich.table import Table

        console = Console(no_color=_no_color)
        table = Table(show_header=True, header_style="bold" if not _no_color else None)

        for key, header, _ in columns:
            table.add_column(header)

        for row in rows:
            table.add_row(*[str(row.get(key, "")) for key, _, _ in columns])

        console.print(table)

    except ImportError:
        # Fallback without rich
        header = "  ".join(h.ljust(w) for _, h, w in columns)
        print(header)
        print("-" * len(header))
        for row in rows:
            line = "  ".join(str(row.get(k, "")).ljust(w) for k, _, w in columns)
            print(line)


def print_object(data: dict, fields: Optional[List[tuple]] = None) -> None:
    """Print single object as key-value pairs.

    Args:
        data: Dict to display
        fields: Optional list of (key, label) tuples to control display order
    """
    if _json_mode:
        print_json(data)
        return

    if fields:
        for key, label in fields:
            val = data.get(key, "")
            print(f"  {label}: {val}")
    else:
        for key, val in data.items():
            print(f"  {key}: {val}")


def print_error(code: str, message: str, exit_code: int = 1) -> None:
    """Print error in consistent format (C29) and exit."""
    if _json_mode:
        err = {"error": code, "code": exit_code, "message": message}
        print(json.dumps(err), file=sys.stderr)
    else:
        print(f"Error: {message}", file=sys.stderr)

    sys.exit(exit_code)
