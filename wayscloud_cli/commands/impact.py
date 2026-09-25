"""
cloud impact commands — Customer-funded reforestation contributions.

Wording lock (anti-greenwashing, see WAYSCloud plan):
  - Pre-settlement: "Added to next bill", "Charged on next bill",
    "Planting is triggered after invoice settlement".
  - Post-settlement-pre-fulfilment: "Provider order placed", "Awaiting provider
    confirmation".
  - Post-fulfilment: "Planted" only when impact_items.status == 'planted' AFTER
    provider confirmation. For provider=='mock' the CLI always prints
    "This is demo data from the mock provider." next to the planted indicator.

Never used in this module: "carbon neutral", "offset", "net zero".
"""

import typer
from typing import Optional

from ..sdk import get_client, sdk_call
from ..output import print_table, print_object, print_json, is_json_mode


app = typer.Typer(help="Impact: forests, trees, contributions")

forest_app = typer.Typer(help="Forests — your customer-funded reforestation tracker")
tree_app = typer.Typer(help="Trees — grow seeds, inspect, water")
commitments_app = typer.Typer(help="Tree commitments — billable contributions")

app.add_typer(forest_app, name="forest")
app.add_typer(tree_app, name="tree")
app.add_typer(commitments_app, name="commitments")


# ─── helpers ────────────────────────────────────────────────────────

def _resolve_forest(client, forest: Optional[str]) -> str:
    """Return a forest id-or-name. If user omitted --forest and there's exactly
    one, use it. Otherwise error with a clear message."""
    if forest:
        return forest
    forests = sdk_call(client.impact.list_forests)
    if not forests:
        raise typer.BadParameter(
            "No forests yet. Create one first: cloud impact forest create \"<name>\""
        )
    if len(forests) == 1:
        return forests[0]["id"]
    names = ", ".join(f"{f.get('name')!r}" for f in forests[:5])
    raise typer.BadParameter(
        f"You have multiple forests ({names}...). Pass --forest <id|name>."
    )


def _demo_suffix(item: dict) -> str:
    if item and item.get("demo_data"):
        return "  [demo data — mock provider]"
    return ""


# ─── visualisations ─────────────────────────────────────────────────

STAGE_GLYPH = {
    "tree":       "🌳",
    "young_tree": "🌲",
    "sapling":    "🪴",
    "sprout":     "🌿",
    "seed":       "🌱",
}

# Ordered most-mature-first; reads left-to-right as "mature canopy → fresh seeds".
STAGE_ORDER_EMOJI = ["tree", "young_tree", "sapling", "sprout", "seed"]
STAGE_ORDER_BARS = ["seed", "sprout", "sapling", "young_tree", "tree"]


def _render_emoji_forest(stage_counts: dict) -> None:
    """One row of emoji per stage-group, wrapping at ~40 emoji/line. Caps the
    total at 200 emoji so a 1000-tree forest doesn't drown the terminal — shows
    a `(+N more)` tail instead."""
    cap = 200
    per_line = 40
    glyphs: list[str] = []
    for stage in STAGE_ORDER_EMOJI:
        glyphs.extend([STAGE_GLYPH[stage]] * int(stage_counts.get(stage, 0)))
    total = len(glyphs)
    tail = ""
    if total > cap:
        tail = f"  (+{total - cap} more)"
        glyphs = glyphs[:cap]

    if not glyphs:
        print("  (no trees yet — try `cloud impact tree grow --count 1`)")
        return
    # Wrap
    for i in range(0, len(glyphs), per_line):
        print("  " + "".join(glyphs[i : i + per_line]))
    # Legend line under the canvas
    legend = "  ".join(
        f"{STAGE_GLYPH[s]} {s}={int(stage_counts.get(s, 0))}"
        for s in STAGE_ORDER_EMOJI
        if int(stage_counts.get(s, 0)) > 0
    )
    if legend:
        print()
        print("  " + legend + tail)


def _render_bar_forest(stage_counts: dict) -> None:
    """Horizontal bar chart per stage, normalised to the max stage count."""
    counts = {s: int(stage_counts.get(s, 0)) for s in STAGE_ORDER_BARS}
    peak = max(counts.values()) if counts else 0
    if peak <= 0:
        print("  (no trees yet — try `cloud impact tree grow --count 1`)")
        return
    bar_width = 40
    for stage in STAGE_ORDER_BARS:
        n = counts[stage]
        fill = round(bar_width * (n / peak)) if peak else 0
        bar = "▓" * fill + " " * (bar_width - fill)
        print(f"  {stage:<11} │ {bar} │ {n:>4}")


# ─── forest ─────────────────────────────────────────────────────────

@forest_app.command("create")
def forest_create(
    name: str = typer.Argument(..., help="Forest display name"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Create a new forest."""
    c = get_client(token)
    data = sdk_call(c.impact.create_forest, name)
    if is_json_mode():
        print_json(data)
    else:
        print(f"Forest created: {data.get('name', name)} (id={data.get('id')})")


@forest_app.command("list")
def forest_list(
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List your forests."""
    c = get_client(token)
    data = sdk_call(c.impact.list_forests)
    if is_json_mode():
        print_json(data)
        return
    if not data:
        print("No forests yet. Create one: cloud impact forest create \"<name>\"")
        return
    rows = [{"id": f["id"][:8], "name": f["name"], "created_at": str(f["created_at"])[:19]} for f in data]
    print_table(rows, [("id", "ID", 10), ("name", "Name", 30), ("created_at", "Created", 22)])


@forest_app.command("status")
def forest_status(
    forest: Optional[str] = typer.Option(None, "--forest", help="Forest UUID or name"),
    visualize: Optional[str] = typer.Option(
        None,
        "--visualize",
        "-v",
        help="Render a forest picture: 'emoji' (🌳🌿🌱) or 'bars' (horizontal bar chart).",
        case_sensitive=False,
    ),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show counts of seeds awaiting settlement, planted, and per-stage."""
    c = get_client(token)
    target = _resolve_forest(c, forest)
    data = sdk_call(c.impact.forest_status, target)
    if is_json_mode():
        print_json(data)
        return
    f = data["forest"]
    sc = data["stage_counts"]
    print(f"Forest: {f['name']}  (id={f['id'][:8]})")
    print()
    print(f"Seeds awaiting invoice settlement: {data['seeds_awaiting_settlement']}")
    print(f"Planted trees:                     {data['planted_count']}")
    print(f"Mature trees:                      {sc.get('tree', 0)}")
    print()

    if visualize:
        features = data.get("features") or {}
        if not features.get("visualize"):
            print(
                "  --visualize is a preview surface and is not enabled for your "
                "account yet. Showing text breakdown instead."
            )
            print()
            visualize = None  # fall through to text view below

    if visualize:
        mode = visualize.lower()
        if mode == "emoji":
            _render_emoji_forest(sc)
        elif mode == "bars":
            _render_bar_forest(sc)
        else:
            raise typer.BadParameter(
                f"--visualize must be 'emoji' or 'bars', got {visualize!r}"
            )
        print()
    else:
        print("By stage:")
        for stage in ("seed", "sprout", "sapling", "young_tree", "tree"):
            print(f"  {stage:<12} {sc.get(stage, 0)}")
        print()

    print(f"Estimated impact (provider-reported only): {data['estimated_co2_kg_provider_reported']} kg CO₂")
    print(f"  {data['wording_note']}")


@forest_app.command("feed")
def forest_feed(
    forest: Optional[str] = typer.Option(None, "--forest", help="Forest UUID or name"),
    limit: int = typer.Option(20, "--limit", min=1, max=200),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Forest activity feed (newest first)."""
    c = get_client(token)
    target = _resolve_forest(c, forest)
    feed = sdk_call(c.impact.forest_feed, target, limit=limit)
    if is_json_mode():
        print_json(feed)
        return
    if not feed:
        print("(no activity yet)")
        return
    for item in feed:
        ts = str(item.get("published_at", ""))[:19]
        title = item.get("title", "")
        body = item.get("body", "") or ""
        prefix = "(demo) " if item.get("demo_data") else ""
        print(f"[{ts}] {prefix}{title}")
        if body:
            print(f"           {body}")


# ─── tree ───────────────────────────────────────────────────────────

@tree_app.command("grow")
def tree_grow(
    count: int = typer.Option(..., "--count", "-n", min=1, max=1000),
    forest: Optional[str] = typer.Option(None, "--forest", help="Forest UUID or name"),
    idempotency_key: Optional[str] = typer.Option(
        None,
        "--idempotency-key",
        help="Optional client-supplied key to make retries safe (no double-charge).",
    ),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Commit N trees to a forest. Charged on your next bill."""
    c = get_client(token)
    target = _resolve_forest(c, forest)
    data = sdk_call(c.impact.commit_trees, target, count, idempotency_key=idempotency_key)
    if is_json_mode():
        print_json(data)
        return
    print(data.get("message") or f"{count} seeds added to your forest.")
    print("Planting will be triggered after invoice settlement.")
    print()
    items = data.get("items") or []
    if items:
        print("Seeds:")
        for it in items[:10]:
            print(f"  {it.get('external_short_id'):<20} stage={it.get('stage'):<6} status={it.get('status')}")
        if len(items) > 10:
            print(f"  ...and {len(items) - 10} more.")


@tree_app.command("inspect")
def tree_inspect(
    item_id: str = typer.Argument(..., help="Seed/tree id (UUID or seed_xxx short id)"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Inspect a single seed or tree."""
    c = get_client(token)
    data = sdk_call(c.impact.get_tree, item_id)
    if is_json_mode():
        print_json(data)
        return
    print_object(data, [
        ("external_short_id", "ID"),
        ("stage", "Stage"),
        ("status", "Status"),
        ("provider", "Provider"),
        ("project_name", "Project"),
        ("country", "Country"),
        ("species", "Species"),
        ("planted_at", "Planted at"),
        ("co2_estimate_kg", "CO₂ estimate (kg, provider-reported)"),
        ("evidence_url", "Evidence"),
        ("created_at", "Created"),
    ])
    suffix = _demo_suffix(data)
    if suffix:
        print()
        print(data.get("demo_label") or "This is demo data from the mock provider.")


@tree_app.command("water")
def tree_water(
    item_id: str = typer.Argument(..., help="Seed/tree id (UUID or seed_xxx short id)"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Water a seed or tree (cosmetic, once per 24h)."""
    c = get_client(token)
    data = sdk_call(c.impact.water_tree, item_id)
    if is_json_mode():
        print_json(data)
        return
    print(f"You watered your {data.get('stage', 'seed')}. It looks slightly happier.{_demo_suffix(data)}")


# ─── commitments ────────────────────────────────────────────────────

@commitments_app.command("list")
def commitments_list(
    limit: int = typer.Option(50, "--limit", min=1, max=500),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """List your past tree commitments."""
    c = get_client(token)
    data = sdk_call(c.impact.list_commitments, limit=limit)
    if is_json_mode():
        print_json(data)
        return
    if not data:
        print("No commitments yet.")
        return
    rows = []
    for r in data:
        rows.append({
            "id": r["id"][:8],
            "qty": r["quantity"],
            "amount": f"{r['total_amount']} {r['currency']}",
            "status": r["status"] + ("  [demo]" if r.get("demo_data") else ""),
            "invoice": (r.get("invoice_id") or "-")[:20],
            "created": str(r["created_at"])[:19],
        })
    print_table(rows, [
        ("id", "ID", 10),
        ("qty", "Qty", 5),
        ("amount", "Amount", 14),
        ("status", "Status", 28),
        ("invoice", "Invoice", 22),
        ("created", "Created", 22),
    ])


@commitments_app.command("show")
def commitments_show(
    commitment_id: str = typer.Argument(..., help="Commitment UUID"),
    token: Optional[str] = typer.Option(None, "--token", help="Override token"),
):
    """Show a single commitment with its items."""
    c = get_client(token)
    data = sdk_call(c.impact.get_commitment, commitment_id)
    if is_json_mode():
        print_json(data)
        return
    print_object(data, [
        ("id", "ID"),
        ("forest_id", "Forest"),
        ("quantity", "Quantity"),
        ("total_amount", "Total"),
        ("currency", "Currency"),
        ("status", "Status"),
        ("provider", "Provider"),
        ("provider_order_id", "Provider order"),
        ("invoice_id", "Invoice"),
        ("invoiced_at", "Invoiced at"),
        ("invoice_settled_at", "Invoice settled at"),
        ("fulfilled_at", "Fulfilled at"),
    ])
    suffix = _demo_suffix(data)
    if suffix:
        print()
        print(data.get("demo_label") or "This is demo data from the mock provider.")
    items = data.get("items") or []
    if items:
        print()
        print(f"Items ({len(items)}):")
        for it in items[:20]:
            extra = _demo_suffix(it)
            print(
                f"  {it.get('external_short_id'):<20} stage={it.get('stage'):<10} "
                f"status={it.get('status')}{extra}"
            )
        if len(items) > 20:
            print(f"  ...and {len(items) - 20} more.")
