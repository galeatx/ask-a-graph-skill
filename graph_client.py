"""Thin CLI client for the ask-a-graph MCP server.

Follows the Anthropic pattern of presenting MCP servers as code APIs.
The agent calls this via Bash rather than using MCP tools directly,
keeping the agent's context lean.

Usage:
    python -m ai_oncology.graph_client <tool_name> '<json_arguments>'

Examples:
    python -m ai_oncology.graph_client list_databases '{}'
    python -m ai_oncology.graph_client check_database_connection '{"database_name": "oncograph"}'
    python -m ai_oncology.graph_client user_query_annotation_and_expansion '{"query": "Find TP53 mutations in lung cancer"}'
"""

import asyncio
import json
import sys
import uuid
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.sse import sse_client


MCP_SERVER_URL = "http://localhost:8627/sse"


def _make_ids() -> dict[str, str]:
    """Generate task_id and message_id for tool calls."""
    return {
        "task_id": f"task_{uuid.uuid4().hex[:8]}",
        "message_id": f"msg_{uuid.uuid4().hex[:8]}",
    }


@asynccontextmanager
async def get_session():
    """Connect to the MCP server and yield a ready session."""
    async with sse_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def call_tool(tool_name: str, arguments: dict) -> dict:
    """Call a single MCP tool and return the result as a dict."""
    # Inject task_id and message_id if not provided
    ids = _make_ids()
    if "task_id" not in arguments:
        arguments["task_id"] = ids["task_id"]
    if "message_id" not in arguments:
        arguments["message_id"] = ids["message_id"]

    async with get_session() as session:
        result = await session.call_tool(tool_name, arguments)

        # Extract text content from MCP result
        if hasattr(result, "content") and result.content:
            for block in result.content:
                if hasattr(block, "text"):
                    try:
                        return json.loads(block.text)
                    except json.JSONDecodeError:
                        return {"raw_text": block.text}
        return {"status": "empty_response"}


async def list_tools() -> list[dict]:
    """List all available tools on the MCP server."""
    async with get_session() as session:
        tools = await session.list_tools()
        return [
            {
                "name": t.name,
                "description": (t.description or "")[:120],
            }
            for t in tools.tools
        ]


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m ai_oncology.graph_client <tool_name> [json_args]")
        print("       python -m ai_oncology.graph_client --list-tools")
        sys.exit(1)

    command = sys.argv[1]

    if command == "--list-tools":
        tools = await list_tools()
        print(json.dumps(tools, indent=2))
        return

    tool_name = command
    arguments = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    result = await call_tool(tool_name, arguments)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
