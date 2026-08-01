"""Tool registration for the TaskTrail MCP server.

Each submodule exposes a `register(mcp)` function that attaches its tools to
the shared `MCPServer` instance. Keeping registration explicit (rather than
import-time side effects) makes it obvious what's wired up from `server.py`.
"""

from mcp.server.mcpserver import MCPServer

from . import agent, projects, tasks


def register_all(mcp: MCPServer) -> None:
    tasks.register(mcp)
    projects.register(mcp)
    agent.register(mcp)
