# QuickMCP

A lightweight, easy-to-use wrapper for creating MCP (Model Context Protocol) servers in Python, built on top of the **official MCP Python SDK**.

QuickMCP simplifies the process of building MCP servers by providing a decorator-based interface and reducing boilerplate code, while still maintaining full compatibility with the MCP protocol through the official SDK.

## Features

- 🚀 **Simple decorator-based API** for tools, resources, and prompts
- 📦 **Minimal boilerplate** - get started with just a few lines of code
- 🔄 **Full MCP compatibility** - works with any MCP client
- 🌐 **Multiple transport options** - stdio, SSE, and more coming soon
- 🛠️ **Type safety** with Pydantic models
- 📝 **Automatic schema generation** from function signatures
- 🔍 **Built-in logging and debugging**
- ⚡ **Async support** for high-performance operations

## Installation

QuickMCP is not yet available on PyPI. Install directly from GitHub:

### Prerequisites

QuickMCP requires the official MCP Python SDK:

```bash
# Install the official MCP SDK first
uv pip install mcp
# or
pip install mcp
```

### Using uv (recommended)

```bash
uv pip install git+https://github.com/leifmarkthaler/quickmcp.git
```

For SSE/HTTP transport support:
```bash
uv pip install "quickmcp[http] @ git+https://github.com/leifmarkthaler/quickmcp.git"
```

### Using pip

```bash
pip install git+https://github.com/leifmarkthaler/quickmcp.git
```

For SSE/HTTP transport support:
```bash
pip install "quickmcp[http] @ git+https://github.com/leifmarkthaler/quickmcp.git"
```

### Development Installation

Clone and install in editable mode:
```bash
git clone https://github.com/leifmarkthaler/quickmcp.git
cd quickmcp
uv pip install -e ".[dev]"
```

## Quick Start

Create a simple MCP server in just a few lines:

```python
from quickmcp import QuickMCPServer

# Create a server
server = QuickMCPServer("my-server")

# Add tools with decorators
@server.tool()
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

@server.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

# Add resources
@server.resource("config://{key}")
def get_config(key: str) -> str:
    """Get configuration value."""
    return f"Config value for {key}"

# Add prompts
@server.prompt()
def code_review(language: str, code: str) -> str:
    """Generate a code review prompt."""
    return f"Please review this {language} code:\n\n{code}"

# Run the server
if __name__ == "__main__":
    server.run()
```

## Usage Examples

### Basic Server with Tools

```python
from quickmcp import QuickMCPServer

server = QuickMCPServer("calculator")

@server.tool()
def calculate(operation: str, x: float, y: float) -> float:
    """Perform basic calculations."""
    operations = {
        "add": lambda a, b: a + b,
        "subtract": lambda a, b: a - b,
        "multiply": lambda a, b: a * b,
        "divide": lambda a, b: a / b if b != 0 else None,
    }
    
    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")
    
    return operations[operation](x, y)

server.run()
```

### Async Operations

```python
from quickmcp import QuickMCPServer
import asyncio

server = QuickMCPServer("async-example")

@server.tool()
async def fetch_data(url: str) -> dict:
    """Fetch data from a URL."""
    # Simulate async operation
    await asyncio.sleep(1)
    return {"url": url, "data": "example data"}

@server.tool()
async def process_data(data: dict) -> dict:
    """Process data asynchronously."""
    await asyncio.sleep(0.5)
    return {"processed": True, **data}

server.run()
```

### Resources and Prompts

```python
from quickmcp import QuickMCPServer
import json

server = QuickMCPServer("knowledge-base")

# In-memory knowledge base
knowledge = {}

@server.tool()
def store_knowledge(topic: str, content: str) -> dict:
    """Store knowledge about a topic."""
    knowledge[topic] = content
    return {"stored": topic}

@server.resource("knowledge://{topic}")
def get_knowledge(topic: str) -> str:
    """Retrieve knowledge about a topic."""
    return knowledge.get(topic, f"No knowledge found for {topic}")

@server.prompt()
def explain_topic(topic: str, level: str = "beginner") -> str:
    """Generate a prompt to explain a topic."""
    return f"""Explain {topic} at a {level} level.
    
Include:
- Clear definition
- Real-world examples
- Common misconceptions
- Related concepts
"""

server.run()
```

### SSE Transport for Network Access

```python
from quickmcp import QuickMCPServer

server = QuickMCPServer("network-server")

@server.tool()
def echo(message: str) -> str:
    """Echo a message back."""
    return message

# Run as SSE server on port 8080
server.run(transport="sse", port=8080)
```

Connect with any MCP client:
```bash
mcp-client sse http://localhost:8080/sse
```

## Advanced Features

### Custom Tool Schemas

```python
@server.tool(
    description="Advanced calculation tool",
    schema={
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["add", "multiply"]},
            "values": {"type": "array", "items": {"type": "number"}}
        }
    }
)
def calculate_many(operation: str, values: list[float]) -> float:
    """Calculate with multiple values."""
    if operation == "add":
        return sum(values)
    elif operation == "multiply":
        import math
        return math.prod(values)
```

### Server Configuration

```python
from quickmcp import QuickMCPServer

server = QuickMCPServer(
    name="my-server",
    version="2.0.0",
    description="My advanced MCP server",
    log_level="DEBUG"  # Enable debug logging
)
```

### Standalone Decorators

You can also use decorators before creating the server:

```python
from quickmcp import tool, resource, prompt, QuickMCPServer

@tool()
def my_tool(arg: str) -> str:
    return f"Processed: {arg}"

@resource("data://{id}")
def my_resource(id: str) -> str:
    return f"Data for {id}"

# Later, create server and register
server = QuickMCPServer("my-server")
server.register_module(__main__)  # Coming soon
server.run()
```

## Running Your Server

### As stdio (default)

```bash
python your_server.py
```

### As SSE server

```bash
python your_server.py --transport sse --port 8080
```

### Testing with MCP Inspector

```bash
mcp-inspector stdio -- python your_server.py
```

## Discovery and Registration

QuickMCP provides comprehensive discovery mechanisms for both local and network-based MCP servers, making it easy to integrate with Gleitzeit and other MCP clients.

### Overview

QuickMCP supports two discovery approaches:
- **Registry-based discovery** for stdio servers (launched as child processes)
- **Network autodiscovery** for SSE/HTTP servers (running as network services)

### Server Registry (for stdio servers)

The server registry allows you to register QuickMCP servers that can be launched via stdio transport.

#### Registering Servers

```bash
# Register a server with the CLI
quickmcp register my-server "python my_server.py" \
    --description "My custom MCP server" \
    --tool-prefix "my."

# Or register programmatically
from quickmcp import register_server

register_server(
    name="my-server",
    command=["python", "my_server.py"],
    description="My custom MCP server",
    tool_prefix="my."
)
```

#### Listing Registered Servers

```bash
# List all registered servers
quickmcp list

# Or programmatically
from quickmcp import list_servers

for server in list_servers():
    print(f"{server.name}: {server.description}")
```

#### Auto-Discovery in Filesystem

QuickMCP can automatically discover servers in your filesystem:

```bash
# Discover servers in current directory and common locations
quickmcp discover --scan-filesystem

# Discover and auto-register found servers
quickmcp discover --scan-filesystem --auto-register

# Specify custom search paths
quickmcp discover --scan-filesystem --paths ./my-servers ~/mcp-servers
```

### Network Autodiscovery (for SSE/HTTP servers)

Network servers automatically broadcast their presence via UDP multicast when running with SSE or HTTP transport.

#### Server-Side (Automatic)

```python
from quickmcp import QuickMCPServer

# Network servers automatically broadcast when running
server = QuickMCPServer("my-server")

# Add discovery metadata
server = QuickMCPServer(
    "my-server",
    discovery_metadata={
        "author": "Your Name",
        "category": "utilities",
        "tags": ["ai", "tools"]
    }
)

# Run as SSE server (autodiscovery enabled automatically)
server.run(transport="sse", port=8080)
```

#### Client-Side Discovery

```bash
# Discover network servers
quickmcp discover --scan-network

# Discover with custom timeout
quickmcp discover --scan-network --timeout 10
```

Or programmatically:

```python
import asyncio
from quickmcp import discover_servers

async def find_network_servers():
    servers = await discover_servers(timeout=5.0)
    for server in servers:
        print(f"Found: {server.name} at {server.host}:{server.port}")

asyncio.run(find_network_servers())
```

### QuickMCP CLI

The QuickMCP CLI provides comprehensive server management:

```bash
# Register a server
quickmcp register <name> <command> [options]

# Unregister a server
quickmcp unregister <name>

# List registered servers
quickmcp list

# Show server information
quickmcp info <name>

# Discover servers (filesystem and/or network)
quickmcp discover [--scan-filesystem] [--scan-network]

# Export configuration for Gleitzeit
quickmcp export --format yaml > ~/.gleitzeit/mcp_servers.yaml
```

### Server Metadata

QuickMCP servers can provide metadata via the `--info` flag:

```bash
# Get server information
python my_server.py --info
```

This returns JSON with server details:
```json
{
  "name": "my-server",
  "version": "1.0.0",
  "description": "My custom server",
  "capabilities": {
    "tools": ["tool1", "tool2"],
    "resources": ["resource1"],
    "prompts": ["prompt1"]
  }
}
```

## Integration with Gleitzeit

QuickMCP servers work seamlessly with [Gleitzeit](https://github.com/leifmarkthaler/gleitzeit):

### Automatic Configuration Export

QuickMCP can export your registered servers directly to Gleitzeit configuration:

```bash
# Export all registered servers to Gleitzeit config
quickmcp export --format yaml > ~/.gleitzeit/mcp_servers.yaml

# The generated config will look like:
```
```yaml
mcp:
  auto_discover: true
  servers:
    - name: "my-server"
      connection_type: "stdio"
      command: ["python", "my_server.py"]
      tool_prefix: "my."
      auto_start: true
```

### Manual Configuration

You can also manually configure QuickMCP servers in Gleitzeit:

```yaml
# ~/.gleitzeit/config.yaml
mcp:
  servers:
    # Stdio server (launched as child process)
    - name: "my-quickmcp-server"
      connection_type: "stdio"
      command: ["python", "path/to/my_server.py"]
      working_dir: "${HOME}/my-servers"
      tool_prefix: "my."
      auto_start: true
    
    # SSE server (network connection)
    - name: "my-sse-server"
      connection_type: "sse"
      url: "http://localhost:8080/sse"
      tool_prefix: "sse."
      auto_start: false  # Don't launch, just connect
```

### Discovery Workflow

1. **Register your servers** with QuickMCP:
   ```bash
   quickmcp register my-server "python my_server.py" --tool-prefix "my."
   ```

2. **Export to Gleitzeit**:
   ```bash
   quickmcp export > ~/.gleitzeit/mcp_servers.yaml
   ```

3. **Use in Gleitzeit workflows**:
   ```yaml
   tasks:
     - name: "Use MCP tool"
       type: mcp
       provider: my-server
       tool: my.some_tool
       arguments:
         param: value
   ```

### Network Server Discovery

For SSE/HTTP servers, Gleitzeit can discover them automatically via UDP multicast:

```python
# Your QuickMCP server broadcasts automatically
server = QuickMCPServer("my-server")
server.run(transport="sse", port=8080)  # Broadcasts on network

# Gleitzeit can discover it
# (when auto_discover: true in config)
```

## API Reference

### QuickMCPServer

Main server class for creating MCP servers.

**Methods:**
- `tool(name=None, description=None, schema=None)` - Decorator for tools
- `resource(uri_template, name=None, description=None, mime_type="text/plain")` - Decorator for resources  
- `prompt(name=None, description=None, arguments=None)` - Decorator for prompts
- `run(transport="stdio", host="localhost", port=8000)` - Run the server
- `list_tools()` - Get list of registered tools
- `list_resources()` - Get list of registered resources
- `list_prompts()` - Get list of registered prompts

### Types

QuickMCP provides several helpful type definitions:

- `ToolResult` - Standard result format for tools
- `ResourceContent` - Content returned by resources
- `PromptMessage` - Message in a prompt template
- `Context` - Execution context for tools
- `ServerConfig` - Server configuration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Links

- [MCP Specification](https://modelcontextprotocol.io)
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Gleitzeit Integration](https://github.com/leifmarkthaler/gleitzeit)

## Important Notes

### Official MCP SDK Compatibility

QuickMCP is specifically designed to work with the **official MCP Python SDK** (`mcp` package). It is **not** compatible with:
- FastMCP or other third-party implementations
- Older or experimental MCP libraries

The official SDK uses a handler-based approach for registering tools, resources, and prompts. QuickMCP provides a decorator-based interface that internally manages these handlers for you.

## Acknowledgments

QuickMCP is built on top of the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) and aims to make MCP server development more accessible and enjoyable.