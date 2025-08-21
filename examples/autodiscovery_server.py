#!/usr/bin/env python
"""
Example of a QuickMCP server with autodiscovery enabled.

This server will broadcast its presence on the local network,
allowing Gleitzeit and other MCP clients to discover it automatically.
"""

from mcplite import QuickMCPServer
import asyncio
import time


# Create server with autodiscovery enabled (default)
server = QuickMCPServer(
    name="autodiscovery-example",
    version="1.0.0",
    description="Example server with network autodiscovery",
    enable_autodiscovery=True,  # This is True by default
    discovery_metadata={
        "author": "QuickMCP",
        "category": "example",
        "tags": ["demo", "autodiscovery"]
    }
)


# Add some example tools
@server.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! I'm discoverable on the network!"


@server.tool()
def get_time() -> str:
    """Get the current time."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


@server.tool()
async def async_calculate(x: float, y: float, operation: str = "add") -> float:
    """Perform async calculation."""
    await asyncio.sleep(0.1)  # Simulate async work
    
    operations = {
        "add": lambda a, b: a + b,
        "subtract": lambda a, b: a - b,
        "multiply": lambda a, b: a * b,
        "divide": lambda a, b: a / b if b != 0 else float('inf')
    }
    
    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")
    
    return operations[operation](x, y)


# Add resources
@server.resource("config://{section}")
def get_config(section: str) -> str:
    """Get configuration section."""
    configs = {
        "network": "autodiscovery: enabled\nport: 42424\nmulticast: 239.255.41.42",
        "server": "name: autodiscovery-example\nversion: 1.0.0",
        "features": "tools: 3\nresources: 1\nprompts: 1"
    }
    return configs.get(section, f"No configuration for section: {section}")


# Add prompts
@server.prompt()
def analyze_discovery(topic: str) -> str:
    """Generate a prompt about network discovery."""
    return f"""Explain how {topic} works in the context of network service discovery.

Consider:
- UDP broadcast vs multicast
- Service announcement protocols
- Discovery timeouts and heartbeats
- Security considerations
- Integration with {topic}
"""


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="QuickMCP Server with Autodiscovery")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], 
                       help="Transport type")
    parser.add_argument("--port", type=int, default=8080, 
                       help="Port for SSE transport")
    parser.add_argument("--no-discovery", action="store_true",
                       help="Disable autodiscovery")
    
    args = parser.parse_args()
    
    # Update autodiscovery setting if disabled
    if args.no_discovery:
        server.enable_autodiscovery = False
        print("Autodiscovery disabled")
    else:
        print(f"Autodiscovery enabled - broadcasting as '{server.name}'")
        print(f"Other MCP clients can discover this server on the network")
    
    # Run the server
    if args.transport == "sse":
        print(f"Starting SSE server on port {args.port}")
        print(f"Connect with: mcp-client sse http://localhost:{args.port}/sse")
        server.run(transport="sse", port=args.port)
    else:
        print("Starting stdio server")
        print("Autodiscovery will broadcast this server's availability")
        server.run(transport="stdio")