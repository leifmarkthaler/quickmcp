# MakeMCP

The fastest way to create MCP (Model Context Protocol) servers in Python. Zero boilerplate, maximum functionality.

```python
from makemcp.quick import tool, run

@tool
def hello(name: str) -> str:
    return f"Hello, {name}! 👋"

run()  # Your MCP server is running!
```

MakeMCP is built on the **official MCP Python SDK** but removes all the complexity. Create powerful MCP servers with just decorators.

**[Quickstart](QUICKSTART.md)** • **[Getting Started](GETTING_STARTED.md)** • **[Examples](examples/)** • **[Documentation](#documentation)**

## Why MakeMCP?

- **Zero Boilerplate**: Just decorators. No classes, no handlers, no setup.
- **Use Your Existing Code**: Any Python file becomes an MCP server instantly
- **Async Native**: Async functions work automatically alongside sync ones
- **Type Safe**: Full type hints and schema generation
- **Fast**: Built on the official MCP SDK for maximum performance
- **Simple**: If you can write Python functions, you can build an MCP server

## Installation

```bash
# Install uv if you don't have it (optional but recommended for 10-100x faster installs)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install MakeMCP
uv pip install git+https://github.com/leifmarkthaler/makemcp.git
```

That's it! You're ready to create MCP servers.

<details>
<summary>Alternative installation methods</summary>

### Using pip (slower but works everywhere)
```bash
pip install git+https://github.com/leifmarkthaler/makemcp.git
```

### For development
```bash
git clone https://github.com/leifmarkthaler/makemcp.git
cd makemcp
uv pip install -e ".[dev]"
```

### For SSE/HTTP transport
```bash
uv pip install "makemcp[http] @ git+https://github.com/leifmarkthaler/makemcp.git"
```
</details>

## Quick Start

### The Simplest Example (3 lines)

```python
from makemcp.quick import tool, run

@tool
def hello(name: str) -> str:
    return f"Hello, {name}!"

run()
```

### Use Your Existing Code (1 line)

```python
from makemcp.quick import from_file

# Any Python file becomes an MCP server
from_file("my_utils.py").run()
```

### Traditional Approach (More Control)

```python
from makemcp import MakeMCPServer

# Create a server
server = MakeMCPServer("my-server")

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
from makemcp import MakeMCPServer

server = MakeMCPServer("calculator")

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

MakeMCP has **full support for async functions**. Async functions are automatically detected and properly wrapped while preserving their async nature.

```python
from makemcp import MakeMCPServer
import asyncio
import aiohttp

server = MakeMCPServer("async-example")

@server.tool()
async def fetch_url(url: str) -> dict:
    """Fetch data from a URL asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return {
                "url": url,
                "status": response.status,
                "content": await response.text()
            }

@server.tool()
async def parallel_process(items: list) -> list:
    """Process multiple items in parallel."""
    async def process_item(item):
        await asyncio.sleep(0.1)  # Simulate work
        return f"Processed: {item}"
    
    # Process all items concurrently
    results = await asyncio.gather(*[process_item(item) for item in items])
    return results

# Mix async and sync tools in the same server
@server.tool()
def sync_operation(x: int, y: int) -> int:
    """Synchronous operation."""
    return x + y

server.run()
```

### Resources and Prompts

```python
from makemcp import MakeMCPServer
import json

server = MakeMCPServer("knowledge-base")

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
from makemcp import MakeMCPServer

server = MakeMCPServer("network-server")

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

## MCP Factory - Auto-Generate Servers

The MCP Factory automatically creates MCP servers from existing Python code with intelligent dependency analysis, safe type conversion, and full async support. [Full documentation →](docs/FACTORY.md)

### Quick Examples

```python
from makemcp.factory import create_mcp_from_module

# Create server from any Python file
server = create_mcp_from_module("my_utils.py")
server.run()

# CLI with auto-dependency detection
# mcp-factory my_utils.py --name utils-server
```

### Smart Dependency Detection

```python
# If dependencies are missing, get helpful errors:
$ mcp-factory my_module.py

Missing dependencies detected:
❌ Required: numpy, pandas
⚠️  Optional: matplotlib (in try/except block)

💡 Quick install: uv pip install numpy pandas  # Uses uv if available
```

### Async Functions Work Automatically

```python
# my_async_tools.py
import asyncio
import aiohttp

async def fetch_webpage(url: str) -> dict:
    """Fetch webpage content asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return {
                "url": url,
                "status": response.status,
                "content": await response.text()
            }

async def parallel_requests(urls: list) -> list:
    """Fetch multiple URLs in parallel."""
    tasks = [fetch_webpage(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)

def sync_helper(text: str) -> str:
    """Synchronous helper function."""
    return text.upper()

# Generate server automatically
if __name__ == "__main__":
    from makemcp.factory import create_mcp_from_module
    server = create_mcp_from_module(__file__)
    server.run()
```

### Generate from Classes with Async Methods

```python
from makemcp.factory import MCPFactory

class AsyncDataProcessor:
    """Data processor with async methods."""
    
    def __init__(self):
        self.processed_count = 0
    
    async def process_batch(self, items: list) -> dict:
        """Process items asynchronously."""
        results = []
        for item in items:
            await asyncio.sleep(0.1)  # Simulate async work
            results.append(f"Processed: {item}")
        
        self.processed_count += len(items)
        return {
            "results": results,
            "total_processed": self.processed_count
        }
    
    def get_stats(self) -> dict:
        """Get processing statistics (sync method)."""
        return {"processed_count": self.processed_count}

# Generate server from class
factory = MCPFactory()
server = factory.from_class(AsyncDataProcessor)
server.run()
```

### Use Decorators for Selective Exposure

```python
from makemcp.factory import mcp_tool, create_mcp_from_module

@mcp_tool
async def exposed_async_function(data: str) -> str:
    """This async function will be exposed as an MCP tool."""
    await asyncio.sleep(0.1)
    return f"Processed: {data}"

@mcp_tool(name="custom_name", description="Custom async tool")
async def another_async(value: int) -> int:
    """Another async function with custom metadata."""
    await asyncio.sleep(0.1)
    return value * 2

async def not_exposed(data: str) -> str:
    """This function won't be exposed (no decorator)."""
    return data

# Only decorated functions become tools
server = create_mcp_from_module(__file__)
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
from makemcp import MakeMCPServer

server = MakeMCPServer(
    name="my-server",
    version="2.0.0",
    description="My advanced MCP server",
    log_level="DEBUG"  # Enable debug logging
)
```

### Standalone Decorators

You can also use decorators before creating the server:

```python
from makemcp import tool, resource, prompt, MakeMCPServer

@tool()
def my_tool(arg: str) -> str:
    return f"Processed: {arg}"

@resource("data://{id}")
def my_resource(id: str) -> str:
    return f"Data for {id}"

# Later, create server and register
server = MakeMCPServer("my-server")
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

MakeMCP provides comprehensive discovery mechanisms for both local and network-based MCP servers, making it easy to integrate with Gleitzeit and other MCP clients.

### Overview

MakeMCP supports two discovery approaches:
- **Registry-based discovery** for stdio servers (launched as child processes)
- **Network autodiscovery** for SSE/HTTP servers (running as network services)

### Server Registry (for stdio servers)

The server registry allows you to register MakeMCP servers that can be launched via stdio transport.

#### Registering Servers

```bash
# Register a server with the CLI
makemcp register my-server "python my_server.py" \
    --description "My custom MCP server" \
    --tool-prefix "my."

# Or register programmatically
from makemcp import register_server

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
makemcp list

# Or programmatically
from makemcp import list_servers

for server in list_servers():
    print(f"{server.name}: {server.description}")
```

#### Auto-Discovery in Filesystem

MakeMCP can automatically discover servers in your filesystem:

```bash
# Discover servers in current directory and common locations
makemcp discover --scan-filesystem

# Discover and auto-register found servers
makemcp discover --scan-filesystem --auto-register

# Specify custom search paths
makemcp discover --scan-filesystem --paths ./my-servers ~/mcp-servers
```

### Network Autodiscovery (for SSE/HTTP servers)

Network servers automatically broadcast their presence via UDP multicast when running with SSE or HTTP transport.

#### Server-Side (Automatic)

```python
from makemcp import MakeMCPServer

# Network servers automatically broadcast when running
server = MakeMCPServer("my-server")

# Add discovery metadata
server = MakeMCPServer(
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
makemcp discover --scan-network

# Discover with custom timeout
makemcp discover --scan-network --timeout 10
```

Or programmatically:

```python
import asyncio
from makemcp import discover_servers

async def find_network_servers():
    servers = await discover_servers(timeout=5.0)
    for server in servers:
        print(f"Found: {server.name} at {server.host}:{server.port}")

asyncio.run(find_network_servers())
```

### MakeMCP CLI

The MakeMCP CLI provides comprehensive server management:

```bash
# Register a server
makemcp register <name> <command> [options]

# Unregister a server
makemcp unregister <name>

# List registered servers
makemcp list

# Show server information
makemcp info <name>

# Discover servers (filesystem and/or network)
makemcp discover [--scan-filesystem] [--scan-network]

# Export configuration for Gleitzeit
makemcp export --format yaml > ~/.gleitzeit/mcp_servers.yaml
```

### Server Metadata

MakeMCP servers can provide metadata via the `--info` flag:

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

MakeMCP servers work seamlessly with [Gleitzeit](https://github.com/leifmarkthaler/gleitzeit):

### Automatic Configuration Export

MakeMCP can export your registered servers directly to Gleitzeit configuration:

```bash
# Export all registered servers to Gleitzeit config
makemcp export --format yaml > ~/.gleitzeit/mcp_servers.yaml

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

You can also manually configure MakeMCP servers in Gleitzeit:

```yaml
# ~/.gleitzeit/config.yaml
mcp:
  servers:
    # Stdio server (launched as child process)
    - name: "my-makemcp-server"
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

1. **Register your servers** with MakeMCP:
   ```bash
   makemcp register my-server "python my_server.py" --tool-prefix "my."
   ```

2. **Export to Gleitzeit**:
   ```bash
   makemcp export > ~/.gleitzeit/mcp_servers.yaml
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
# Your MakeMCP server broadcasts automatically
server = MakeMCPServer("my-server")
server.run(transport="sse", port=8080)  # Broadcasts on network

# Gleitzeit can discover it
# (when auto_discover: true in config)
```

## API Reference

### MakeMCPServer

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

MakeMCP provides several helpful type definitions:

- `ToolResult` - Standard result format for tools
- `ResourceContent` - Content returned by resources
- `PromptMessage` - Message in a prompt template
- `Context` - Execution context for tools
- `ServerConfig` - Server configuration

## Testing

MakeMCP includes a comprehensive test suite. Run tests using:

```bash
# Using the test runner script (auto-detects uv)
./run_tests.sh

# Using uv directly (fastest)
uv run pytest tests/ -v

# Using standard pytest
pytest tests/ -v

# Run specific test file
uv run pytest tests/test_factory.py -v

# Run with coverage
uv run pytest tests/ --cov=src/makemcp --cov-report=html
```

## Dependency Management

MakeMCP uses smart dependency detection and can automatically use `uv` for faster installations:

### Automatic Detection

When the MCP Factory detects missing dependencies, it will:
1. Check if `uv` is available
2. Use `uv pip install` if available (10-100x faster)
3. Fall back to `pip install` if not

### Example with Missing Dependencies

```python
# If numpy is not installed, MakeMCP will detect it
import numpy as np

def calculate_mean(data: list) -> float:
    """Calculate mean using numpy."""
    return np.mean(data)
```

When running the factory:
```bash
$ mcp-factory my_module.py

Missing dependencies detected:
❌ Required: numpy

💡 Quick install: uv pip install numpy  # or pip install if uv not available
```

### Managing Dependencies

For projects using MakeMCP:

```bash
# Fast dependency installation with uv
uv pip sync      # Install from requirements.txt
uv pip compile   # Generate locked requirements

# Or traditional pip
pip install -r requirements.txt
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/leifmarkthaler/makemcp.git
cd makemcp

# Use the setup script (recommended)
./setup.sh

# Or manual setup with uv
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests
./run_tests.sh
```

## License

MIT License - see LICENSE file for details.

## Full Feature Set

<details>
<summary>All features MakeMCP supports</summary>

- ✅ **Tools** - Functions that LLMs can call
- ✅ **Resources** - Data/content LLMs can access  
- ✅ **Prompts** - Reusable prompt templates
- ✅ **Async/Await** - Full async support
- ✅ **Type Safety** - Automatic schema from type hints
- ✅ **Multiple Transports** - stdio, SSE, more coming
- ✅ **Auto-discovery** - Network and registry based
- ✅ **Factory System** - Convert existing code instantly
- ✅ **Configuration** - Safe, dev, and custom configs
- ✅ **Dependency Analysis** - Smart missing package detection
- ✅ **UV Integration** - 10-100x faster package management
- ✅ **Error Handling** - Comprehensive error messages
- ✅ **Testing** - Full test suite included
- ✅ **Examples** - Many examples to learn from
</details>

## Links

- [MCP Specification](https://modelcontextprotocol.io)
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Gleitzeit Integration](https://github.com/leifmarkthaler/gleitzeit)

## Important Notes

### Official MCP SDK Compatibility

MakeMCP is specifically designed to work with the **official MCP Python SDK** (`mcp` package). It is **not** compatible with:
- FastMCP or other third-party implementations
- Older or experimental MCP libraries

The official SDK uses a handler-based approach for registering tools, resources, and prompts. MakeMCP provides a decorator-based interface that internally manages these handlers for you.

## Acknowledgments

MakeMCP is built on top of the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) and aims to make MCP server development more accessible and enjoyable.