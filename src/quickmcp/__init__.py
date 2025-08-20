"""
QuickMCP - The easiest way to create MCP servers in Python

Zero boilerplate. Just decorators. Built on the official MCP SDK.

Quick start:
    from quickmcp.quick import tool, run
    
    @tool
    def hello(name: str) -> str:
        return f"Hello, {name}!"
    
    run()
"""

# The simplest API - import this for zero-config usage
from quickmcp.quick import server, from_file, from_object, run, tool as quick_tool

# Traditional API - for more control
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
from quickmcp.factory import (
    MCPFactory,
    create_mcp_from_module,
    create_mcp_from_object,
    mcp_tool,
)

__version__ = "0.1.0"

__all__ = [
    # Super simple API (new!)
    "server",
    "from_file", 
    "from_object",
    "run",
    "quick_tool",
    
    # Traditional API
    "QuickMCPServer",
    "tool",
    "resource",
    "prompt",
    "ToolResult",
    "ResourceContent",
    "PromptMessage",
    "Context",
    
    # Factory
    "MCPFactory",
    "create_mcp_from_module",
    "create_mcp_from_object",
    "mcp_tool",
    
    # Discovery
    "AutoDiscovery",
    "DiscoveryListener",
    "DiscoveryBroadcaster",
    "discover_servers",
    "ServerInfo",
    
    # Registry
    "ServerRegistry",
    "ServerRegistration",
    "register_server",
    "list_servers",
]