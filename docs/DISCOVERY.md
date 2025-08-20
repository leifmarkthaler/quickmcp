# QuickMCP Discovery Guide

This guide explains how QuickMCP's discovery system works and how to use it effectively with Gleitzeit and other MCP clients.

## Overview

QuickMCP provides two complementary discovery mechanisms:

1. **Registry-based discovery** for stdio servers (launched as child processes)
2. **Network autodiscovery** for SSE/HTTP servers (network services)

## Understanding Transport Types

### stdio Transport
- Server runs as a child process
- Communication via stdin/stdout
- Used when the client launches the server
- Discovery via registry and filesystem scanning

### SSE/HTTP Transport
- Server runs as a network service
- Communication via HTTP/SSE
- Used when the server is already running
- Discovery via UDP multicast

## Registry-Based Discovery (stdio)

### The Server Registry

The server registry is a local database of QuickMCP servers that can be launched via stdio. It's stored in `~/.quickmcp/registry.json`.

### Registering Servers

#### Via CLI

```bash
# Basic registration
quickmcp register my-server "python my_server.py"

# With additional options
quickmcp register my-server "python my_server.py" \
    --description "My custom MCP server" \
    --working-dir "/path/to/server" \
    --tool-prefix "my."
```

#### Programmatically

```python
from quickmcp import register_server

register_server(
    name="my-server",
    command=["python", "my_server.py"],
    description="My custom MCP server",
    working_dir="/path/to/server",
    tool_prefix="my."
)
```

### Auto-Discovery in Filesystem

QuickMCP can automatically find servers in your filesystem:

```bash
# Scan default locations
quickmcp discover --scan-filesystem

# Scan specific directories
quickmcp discover --scan-filesystem --paths ./servers ~/mcp-servers

# Auto-register found servers
quickmcp discover --scan-filesystem --auto-register
```

The discovery process:
1. Scans for Python files containing `QuickMCPServer` or `from quickmcp import`
2. Attempts to run each file with `--info` flag
3. Parses the returned JSON metadata
4. Creates registry entries for valid servers

### Managing Registered Servers

```bash
# List all registered servers
quickmcp list

# Show detailed information
quickmcp info my-server

# Remove a server
quickmcp unregister my-server
```

### Exporting for Gleitzeit

```bash
# Export as YAML (recommended for Gleitzeit)
quickmcp export --format yaml > ~/.gleitzeit/mcp_servers.yaml

# Export as JSON
quickmcp export --format json > servers.json
```

The exported configuration is ready to use with Gleitzeit:

```yaml
mcp:
  auto_discover: true
  servers:
    - name: "my-server"
      connection_type: "stdio"
      command: ["python", "my_server.py"]
      working_dir: "/path/to/server"
      tool_prefix: "my."
      auto_start: true
```

## Network Autodiscovery (SSE/HTTP)

### How It Works

1. **Server broadcasts**: When running with SSE/HTTP transport, servers automatically broadcast their presence via UDP multicast
2. **Multicast group**: Uses `239.255.41.42:42424` (private multicast range)
3. **Heartbeat**: Servers send announcements every 5 seconds
4. **TTL**: Discovered servers are considered stale after 30 seconds without heartbeat

### Server-Side Setup

```python
from quickmcp import QuickMCPServer

# Create server with discovery metadata
server = QuickMCPServer(
    "my-server",
    version="1.0.0",
    description="My network server",
    discovery_metadata={
        "author": "Your Name",
        "category": "utilities",
        "tags": ["ai", "tools"]
    }
)

# Autodiscovery starts automatically for network transports
server.run(transport="sse", port=8080)
```

### Client-Side Discovery

#### Via CLI

```bash
# Discover network servers
quickmcp discover --scan-network

# With custom timeout
quickmcp discover --scan-network --timeout 10
```

#### Programmatically

```python
import asyncio
from quickmcp import discover_servers

async def find_servers():
    # Discover servers (5 second timeout)
    servers = await discover_servers(timeout=5.0)
    
    for server in servers:
        print(f"Found: {server.name}")
        print(f"  Version: {server.version}")
        print(f"  Transport: {server.transport}")
        print(f"  Location: {server.host}:{server.port}")
        print(f"  Description: {server.description}")
        
        # Access capabilities
        if server.capabilities:
            tools = server.capabilities.get("tools", [])
            print(f"  Tools: {', '.join(tools)}")

asyncio.run(find_servers())
```

### Disabling Autodiscovery

```python
# Disable for a specific server
server = QuickMCPServer("my-server", enable_autodiscovery=False)

# Or disable at runtime
server.enable_autodiscovery = False
```

## Server Metadata Protocol

QuickMCP servers support a metadata protocol for discovery:

### Implementing the Protocol

When a QuickMCP server receives the `--info` flag, it outputs JSON metadata and exits:

```python
# This is handled automatically by QuickMCPServer
# But here's what happens internally:

if "--info" in sys.argv:
    info = {
        "name": server.name,
        "version": server.version,
        "description": server.description,
        "capabilities": {
            "tools": server.list_tools(),
            "resources": server.list_resources(),
            "prompts": server.list_prompts()
        },
        "metadata": server.discovery_metadata
    }
    print(json.dumps(info))
    sys.exit(0)
```

### Using the Protocol

```bash
# Get server information
python my_server.py --info

# Output:
{
  "name": "my-server",
  "version": "1.0.0",
  "description": "My custom server",
  "capabilities": {
    "tools": ["tool1", "tool2"],
    "resources": ["resource1"],
    "prompts": ["prompt1"]
  },
  "metadata": {
    "author": "Your Name"
  }
}
```

## Complete Example

Here's a complete workflow for setting up discovery:

### 1. Create a Server

```python
# my_server.py
from quickmcp import QuickMCPServer

server = QuickMCPServer(
    "data-processor",
    version="1.0.0",
    description="Process and analyze data",
    discovery_metadata={
        "author": "Data Team",
        "category": "analytics"
    }
)

@server.tool()
def process_data(data: list) -> dict:
    """Process a list of data points."""
    return {
        "count": len(data),
        "sum": sum(data),
        "average": sum(data) / len(data) if data else 0
    }

if __name__ == "__main__":
    server.run()
```

### 2. Register the Server

```bash
# Register for stdio usage
quickmcp register data-processor "python my_server.py" \
    --description "Process and analyze data" \
    --tool-prefix "data."
```

### 3. Export to Gleitzeit

```bash
# Export configuration
quickmcp export > ~/.gleitzeit/mcp_servers.yaml
```

### 4. Use in Gleitzeit Workflow

```yaml
# workflow.yaml
name: "Data Analysis"
tasks:
  - name: "Process data"
    type: mcp
    provider: data-processor
    tool: data.process_data
    arguments:
      data: [1, 2, 3, 4, 5]
```

### 5. Or Run as Network Server

```bash
# Run as SSE server (autodiscovery enabled)
python my_server.py --transport sse --port 8080

# Discover from another machine
quickmcp discover --scan-network
```

## Troubleshooting

### Registry Issues

```bash
# Check registry location
ls ~/.quickmcp/registry.json

# Reset registry
rm ~/.quickmcp/registry.json
quickmcp list  # Creates new empty registry

# Manually edit registry
vi ~/.quickmcp/registry.json
```

### Network Discovery Issues

1. **Firewall**: Ensure UDP port 42424 is open
2. **Multicast**: Some networks block multicast traffic
3. **Network interface**: Discovery uses the default network interface

```python
# Debug network discovery
import logging
logging.basicConfig(level=logging.DEBUG)

from quickmcp import discover_servers
import asyncio

async def debug_discovery():
    servers = await discover_servers(timeout=10.0)
    print(f"Found {len(servers)} servers")

asyncio.run(debug_discovery())
```

### Server Not Found

```bash
# Verify server supports --info
python my_server.py --info

# Check if server is registered
quickmcp list | grep my-server

# Re-register if needed
quickmcp unregister my-server
quickmcp register my-server "python my_server.py"
```

## Best Practices

1. **Use descriptive names**: Choose clear, unique names for your servers
2. **Add metadata**: Include author, category, and tags for better organization
3. **Use tool prefixes**: Prevent naming conflicts in Gleitzeit
4. **Document capabilities**: Provide clear descriptions for tools, resources, and prompts
5. **Test discovery**: Verify servers are discoverable before deployment

## Integration with CI/CD

```yaml
# .github/workflows/register-servers.yml
name: Register MCP Servers
on:
  push:
    paths:
      - 'servers/**/*.py'

jobs:
  register:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install QuickMCP
        run: pip install quickmcp
      
      - name: Discover and register servers
        run: |
          quickmcp discover --scan-filesystem --paths ./servers --auto-register
          quickmcp export --format yaml > mcp_servers.yaml
      
      - name: Upload configuration
        uses: actions/upload-artifact@v2
        with:
          name: mcp-config
          path: mcp_servers.yaml
```

## Security Considerations

1. **Command injection**: Be careful with command registration
   - Validate commands before registration
   - Use absolute paths when possible
   - Avoid shell expansion in commands

2. **Network discovery**: 
   - Only enabled on local network (multicast)
   - No authentication (trust local network)
   - Consider firewall rules for production

3. **Registry permissions**:
   - Registry file is user-readable/writable only
   - Located in user's home directory
   - No system-wide registry by design

## Further Reading

- [QuickMCP README](../README.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Gleitzeit Documentation](https://github.com/leifmarkthaler/gleitzeit)