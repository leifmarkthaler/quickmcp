# Claude Integration Guide for QuickMCP

## Overview

QuickMCP is a wrapper library that simplifies creating MCP (Model Context Protocol) servers using the **official MCP Python SDK** (`mcp` package). This guide helps Claude and other AI assistants understand how to properly work with this codebase.

## Important: Use the Official MCP Python SDK

QuickMCP is built on top of the official MCP Python SDK from Anthropic. It is **NOT** compatible with FastMCP or other third-party MCP implementations.

### Required Dependencies

```bash
# Install using uv (recommended)
uv pip install mcp

# Or using pip
pip install mcp
```

The official MCP SDK package is `mcp` (not `mcp-python`, `fastmcp`, or any other variant).

## Architecture Overview

QuickMCP provides a decorator-based API that internally uses the official SDK's handler-based approach:

1. **Decorators** (`@server.tool()`, `@server.resource()`, `@server.prompt()`) - Simple API for users
2. **Handler Registration** - QuickMCP registers handlers with the MCP Server internally
3. **Official SDK Server** - The underlying `mcp.server.Server` handles the protocol

## Key Implementation Details

### Server Initialization

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, Prompt, TextContent

class QuickMCPServer:
    def __init__(self, name: str, version: str = "1.0.0"):
        # Create the official SDK server
        self._server = Server(name, version=version)
        
        # Register handlers
        self._register_handlers()
```

### Handler Registration Pattern

The official MCP SDK uses a handler-based approach, NOT decorators on the Server class:

```python
def _register_handlers(self):
    @self._server.list_tools()
    async def list_tools():
        # Return list of Tool objects
        return [Tool(...) for tool in self._tools]
    
    @self._server.call_tool()
    async def call_tool(name: str, arguments: dict):
        # Execute tool and return TextContent
        result = await self._tools[name](**arguments)
        return [TextContent(type="text", text=str(result))]
```

### Important: The Server Class Does NOT Have Tool/Resource/Prompt Methods

The official `mcp.server.Server` class does **NOT** have these methods:
- ❌ `server.tool()` - Does not exist
- ❌ `server.resource()` - Does not exist  
- ❌ `server.prompt()` - Does not exist

Instead, it has handler registration methods:
- ✅ `server.list_tools()` - Register handler for listing tools
- ✅ `server.call_tool()` - Register handler for calling tools
- ✅ `server.list_resources()` - Register handler for listing resources
- ✅ `server.read_resource()` - Register handler for reading resources
- ✅ `server.list_prompts()` - Register handler for listing prompts
- ✅ `server.get_prompt()` - Register handler for getting prompts

## Running Tests

The test suite validates compatibility with the official MCP SDK:

```bash
# Make test script executable
chmod +x run_tests.sh

# Run all tests
./run_tests.sh

# Or run with pytest directly
pytest tests/ -v
```

## Transport Modes

### stdio Transport (Default)
```python
async def run_stdio(self):
    async with stdio_server(self._server) as transport:
        await transport.run()
```

### SSE Transport
Requires additional dependencies: `pip install starlette uvicorn`

## Common Pitfalls to Avoid

1. **Don't try to use FastMCP patterns** - FastMCP has a different API that's incompatible
2. **Don't call non-existent methods** - The Server class doesn't have decorator methods
3. **Always use handler registration** - This is how the official SDK works
4. **Return proper types** - Tools must return TextContent objects, not raw values

## Development Workflow

When making changes to QuickMCP:

1. **Ensure official SDK is installed**: `uv pip install mcp`
2. **Run tests after changes**: `./run_tests.sh`
3. **Check coverage**: Open `htmlcov/index.html` after running tests
4. **Follow the handler pattern**: Don't try to add methods to the Server class

## Code Style Guidelines

- Use type hints for all function parameters and return values
- Follow the async/await pattern for all handlers
- Generate JSON schemas from function signatures when possible
- Keep the decorator API simple for end users

## Example Implementation Pattern

When adding new functionality, follow this pattern:

```python
# In QuickMCPServer class

def new_feature(self, **kwargs):
    """User-facing decorator."""
    def decorator(func):
        # Store function and metadata
        self._features[name] = func
        self._feature_metadata[name] = {...}
        return func
    return decorator

def _register_handlers(self):
    @self._server.list_features()  # If such handler exists
    async def list_features():
        # Return appropriate MCP types
        return [...]
```

## Testing New Features

When adding features:

1. Add unit tests in `tests/test_*.py`
2. Test both sync and async functions
3. Verify handler registration works
4. Ensure proper type conversion (to TextContent, etc.)

## Questions to Ask When Debugging

1. Is the official MCP SDK installed? (`pip show mcp`)
2. Are we using handler registration, not method decoration?
3. Are we returning the correct MCP types?
4. Is the async/await pattern used correctly?

## Additional Resources

- [Official MCP Documentation](https://modelcontextprotocol.io)
- [MCP Python SDK Repository](https://github.com/modelcontextprotocol/python-sdk)
- [QuickMCP Repository](https://github.com/leifmarkthaler/quickmcp)