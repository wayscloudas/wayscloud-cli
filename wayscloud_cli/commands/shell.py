"""
cloud shell — interactive CloudShell via WebSocket (C14, C25, C30).

Connects to wss://shell.wayscloud.services/ws with Authorization header.
PAT must have shell:connect scope (C6).
"""

import sys
import json
import asyncio
from typing import Optional

import typer

from ..config import resolve_token, SHELL_WS
from ..output import print_error

app = typer.Typer(help="Interactive shell")


@app.command("connect")
def connect(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Connect to interactive CloudShell.

    Requires shell:connect scope on your CLI token.
    """
    resolved = resolve_token(token)
    if not resolved:
        print_error("not_authenticated", "Not logged in. Run: cloud login --token <pat>", exit_code=2)

    try:
        asyncio.run(_shell_session(resolved))
    except KeyboardInterrupt:
        print("\nSession ended.")


async def _shell_session(token: str) -> None:
    """Run interactive WebSocket shell session."""
    import websockets

    # Connect with Authorization header (C14, C30 — never query string)
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with websockets.connect(
            SHELL_WS,
            additional_headers=headers,
            open_timeout=10,
            close_timeout=5,
            ping_interval=30,
        ) as ws:
            print("WAYSCloud Shell v0.1.0")
            print("Type 'cloud help' for commands, 'exit' to quit.\n")

            # Start reader task
            reader_task = asyncio.create_task(_read_messages(ws))

            # Input loop
            try:
                await _input_loop(ws)
            finally:
                reader_task.cancel()
                try:
                    await reader_task
                except asyncio.CancelledError:
                    pass

    except Exception as e:
        err = str(e)
        # Map connection errors to exit codes (C13, C16)
        if "403" in err:
            print("Error: Authentication failed or missing shell:connect scope.", file=sys.stderr)
            sys.exit(2)
        elif "Connection refused" in err or "unreachable" in err.lower():
            print(f"Error: Cannot connect to shell service.", file=sys.stderr)
            sys.exit(3)
        else:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(3)


async def _read_messages(ws) -> None:
    """Read and display messages from WebSocket."""
    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
                msg_type = msg.get("type", "")
                data = msg.get("data", "")

                if msg_type == "output":
                    print(data, end="", flush=True)
                elif msg_type == "prompt":
                    print(data, end="", flush=True)
                elif msg_type == "error":
                    print(f"\nError: {data}", file=sys.stderr)
                elif msg_type == "history":
                    pass  # Could populate readline history
                elif msg_type == "ratelimit":
                    print(f"\nRate limited. Try again later.", file=sys.stderr)
                elif msg_type == "close":
                    print(f"\n{data}")
                    break

            except json.JSONDecodeError:
                print(raw, end="", flush=True)

    except asyncio.CancelledError:
        raise
    except Exception:
        pass


async def _input_loop(ws) -> None:
    """Read user input and send to WebSocket."""
    loop = asyncio.get_event_loop()

    while True:
        try:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            command = line.strip()
            if command.lower() in ("exit", "quit", "q"):
                break

            await ws.send(json.dumps({"type": "input", "data": command}))

        except (EOFError, KeyboardInterrupt):
            break

    try:
        await ws.close()
    except Exception:
        pass
