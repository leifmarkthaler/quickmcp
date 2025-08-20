"""
QuickMCP - A simplified wrapper for creating MCP servers in Python

QuickMCP makes it easy to create Model Context Protocol (MCP) servers
with minimal boilerplate code.
"""

from quickmcp.server import QuickMCPServer
from quickmcp.decorators import tool, resource, prompt
from quickmcp.types import (
    ToolResult,
    ResourceContent,
    PromptMessage,
    Context,
)

__version__ = "0.1.0"

__all__ = [
    "QuickMCPServer",
    "tool",
    "resource",
    "prompt",
    "ToolResult",
    "ResourceContent",
    "PromptMessage",
    "Context",
]