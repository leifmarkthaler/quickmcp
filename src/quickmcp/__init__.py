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
from quickmcp.autodiscovery import (
    AutoDiscovery,
    DiscoveryListener,
    DiscoveryBroadcaster,
    discover_servers,
    ServerInfo,
)
from quickmcp.registry import (
    ServerRegistry,
    ServerRegistration,
    register_server,
    list_servers,
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
    "AutoDiscovery",
    "DiscoveryListener",
    "DiscoveryBroadcaster",
    "discover_servers",
    "ServerInfo",
    "ServerRegistry",
    "ServerRegistration",
    "register_server",
    "list_servers",
]