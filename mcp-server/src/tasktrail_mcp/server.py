"""TaskTrail MCP server entrypoint.

Wires up the shared MCPServer instance with tools, resources, and prompts,
and exposes `main()` as the `tasktrail-mcp` console script (see pyproject.toml).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.mcpserver import MCPServer

from . import __version__
from .client import client
from .prompts import register as register_prompts
from .resources import register as register_resources
from .tools import register_all as register_tools

INSTRUCTIONS = """\
TaskTrail is a task and project manager. Use the tasktrail_* tools for CRUD
operations (create/list/get/update/delete tasks and projects) — they're fast
and cheap. Reach for tasktrail_ask_agent only when a request needs real
planning or fuzzy interpretation that goes beyond direct CRUD (e.g. "plan my
week", "break this project into tasks"), since it runs a second LLM chain on
the backend. Resources under tasktrail:// (today, tasks, projects) give cheap
read-only snapshots without a tool call. Task status is one of
todo|in_progress|done|archived; priority is one of low|medium|high|urgent.
"""


@asynccontextmanager
async def lifespan(_server: MCPServer) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await client.aclose()


mcp = MCPServer(
    name="tasktrail",
    version=__version__,
    instructions=INSTRUCTIONS,
    lifespan=lifespan,
)

register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


def main() -> None:
    """Run the server over stdio (the only transport supported in v1)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
