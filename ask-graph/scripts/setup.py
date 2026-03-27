"""One-time setup for the ask-graph skill.

Verifies the MCP server is reachable, checks database connectivity,
and bootstraps schema caches for any database that doesn't have one.

Entity and relationship types are NOT fetched here — they are retrieved
dynamically per query via list_entity_types, following the orchestrator pattern.
"""

import json
import subprocess
import sys
from pathlib import Path
from setup_constants import DATABASES, MCP_HEALTH_URL


def _print(icon: str, msg: str) -> None:
    print(f"  {icon}  {msg}")


def _call(tool: str, args: dict) -> dict | None:
    """Call a graph_client tool. Returns parsed JSON or None on failure."""
    cmd = [
        "uv", "run", "python", "-m", "ai_oncology.graph_client",
        tool,
        json.dumps(args),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def check_server() -> bool:
    """Verify the MCP server is reachable via its health endpoint."""
    print("\n[1/3] MCP server health")
    try:
        import urllib.request
        with urllib.request.urlopen(MCP_HEALTH_URL, timeout=5) as resp:
            body = json.loads(resp.read())
            status = body.get("status", "unknown")
            _print("✓", f"Server is up  (status: {status})")
            return True
    except Exception as exc:
        _print("✗", f"Server unreachable at {MCP_HEALTH_URL}  ({exc})")
        _print("→", "Start the MCP server:  docker compose up  (in ask-a-graph-mcp/)")
        return False


def check_connections() -> list[str]:
    """Check connectivity for each database. Returns list of reachable DB names."""
    print("\n[2/3] Database connections")
    reachable = []
    for db in DATABASES:
        result = _call("check_database_connection", {"database_name": db})
        if result and result.get("status") == "connected":
            _print("✓", f"{db}  — connected")
            reachable.append(db)
        else:
            error = (result or {}).get("error_message", "no response")
            _print("✗", f"{db}  — unreachable  ({error})")
    return reachable


def ensure_schemas(reachable: list[str]) -> list[str]:
    """Check schema cache for each reachable DB; bootstrap if missing.

    Returns list of DBs where schema is confirmed ready.
    """
    print("\n[3/3] Schema cache")
    schema_ready = []
    for db in reachable:
        result = _call("check_schema_generation_status", {"database_name": db})
        if result and result.get("status") == "cached":
            _print("✓", f"{db}  — schema already cached, skipping")
            schema_ready.append(db)
            continue

        _print("…", f"{db}  — schema not cached, bootstrapping (may take a minute)")
        boot = _call("bootstrap_database_schema", {"database_name": db})
        if boot and boot.get("status") == "success":
            _print("✓", f"{db}  — schema bootstrapped successfully")
            schema_ready.append(db)
        else:
            error = (boot or {}).get("error_message", "no response")
            _print("✗", f"{db}  — bootstrap failed  ({error})")
    return schema_ready


def write_marker(output_dir: Path) -> None:
    """Write setup_complete.json into the output directory."""
    marker = {
        "setup_complete": True,
        "databases": DATABASES,
    }
    marker_path = output_dir / "setup_complete.json"
    marker_path.write_text(json.dumps(marker, indent=2))
    _print("✓", f"Marker written to {marker_path}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run python .claude/skills/ask-graph/scripts/setup.py <output_dir>")
        sys.exit(1)

    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)

    print("ask-graph skill setup")
    print("=" * 40)

    if not check_server():
        sys.exit(1)

    reachable = check_connections()

    if not reachable:
        print("\n  No databases reachable. Check your Neo4j credentials in ask-a-graph-mcp/.env")
        sys.exit(1)

    schema_ready = ensure_schemas(reachable)

    all_ready = set(schema_ready) == set(DATABASES)

    print("\n" + "=" * 40)
    if all_ready:
        write_marker(output_dir)
        print(f"  Done.  All {len(DATABASES)} databases ready.")
    else:
        not_ready = [db for db in DATABASES if db not in schema_ready]
        print(f"  Done.  {len(schema_ready)}/{len(DATABASES)} databases ready.  Not ready: {', '.join(not_ready)}")
        print("  Marker NOT written — re-run setup once all databases are reachable and cached.")


if __name__ == "__main__":
    main()
