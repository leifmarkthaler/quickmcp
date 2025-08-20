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

## Network Autodiscovery

QuickMCP includes built-in network autodiscovery, allowing servers to be automatically discovered by Gleitzeit and other MCP clients on the local network.

### Autodiscovery Features

- 🔍 **Automatic broadcasting** - Servers announce themselves via UDP multicast
- 🌐 **Zero configuration** - Works out of the box on local networks
- 📡 **Multiple transports** - Supports stdio, SSE, and HTTP servers
- 🔄 **Heartbeat mechanism** - Servers send periodic announcements
- 📊 **Capability broadcasting** - Advertises available tools, resources, and prompts

### Enabling Autodiscovery

Autodiscovery is enabled by default. Servers automatically broadcast their presence:

```python
from quickmcp import QuickMCPServer

# Autodiscovery is enabled by default
server = QuickMCPServer("my-server")

# Disable if needed
server = QuickMCPServer("my-server", enable_autodiscovery=False)

# Add discovery metadata
server = QuickMCPServer(
    "my-server",
    discovery_metadata={
        "author": "Your Name",
        "category": "utilities",
        "tags": ["ai", "tools"]
    }
)
```

### Discovering Servers

Use the discovery client to find QuickMCP servers:

```bash
# Discover servers once
python -m quickmcp.autodiscovery listen

# Continuously monitor for servers
python examples/discover_servers.py continuous

# Export discovered servers to JSON
python examples/discover_servers.py export --output servers.json
```

### Programmatic Discovery

```python
import asyncio
from quickmcp import discover_servers

async def find_servers():
    servers = await discover_servers(timeout=5.0)
    for server in servers:
        print(f"Found: {server.name} ({server.transport})")
        if server.transport == "sse":
            print(f"  URL: http://{server.host}:{server.port}")

asyncio.run(find_servers())
```

## Integration with Gleitzeit

QuickMCP servers work seamlessly with [Gleitzeit](https://github.com/leifmarkthaler/gleitzeit):

### Manual Configuration

```yaml
# ~/.gleitzeit/config.yaml
mcp:
  servers:
    - name: "my-quickmcp-server"
      connection_type: "stdio"
      command: ["python", "my_server.py"]
      tool_prefix: "my."
```

Or for SSE servers:
```yaml
mcp:
  servers:
    - name: "my-quickmcp-server"
      connection_type: "sse"
      url: "http://localhost:8080/sse"
      tool_prefix: "my."
```

### Autodiscovery with Gleitzeit

When autodiscovery is enabled, Gleitzeit can automatically find and connect to QuickMCP servers on the network without manual configuration. Servers broadcast:

- Server name and version
- Transport type (stdio/sse/http)
- Connection details (host, port)
- Available capabilities (tools, resources, prompts)
- Custom metadata

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