# MakeMCP Examples

This directory contains example MakeMCP servers demonstrating various features and use cases.

## Available Examples

### 1. Simple Server (`simple_server.py`)
A minimal example showing the basic MakeMCP API with simple tools, resources, and prompts.

**Features:**
- Basic tool registration
- Simple resource handling
- Prompt templates
- Minimal boilerplate

**Run:**
```bash
python examples/simple_server.py
```

### 2. Advanced Server (`advanced_server.py`)
Comprehensive example showcasing advanced MakeMCP features.

**Features:**
- Complex tool schemas
- Multiple resource types
- Async operations
- Error handling
- State management

**Run:**
```bash
python examples/advanced_server.py
```

### 3. File Server (`file_server.py`)
A full-featured file system operations server with security features.

**Features:**
- Directory listing and traversal
- File reading with size limits
- File search with pattern matching
- Metadata inspection
- Path sandboxing for security
- Tree structure generation

**Tools:**
- `list_directory` - List directory contents
- `read_file` - Read text files
- `search_files` - Search with patterns
- `file_info` - Get detailed metadata
- `get_tree` - Directory tree structure

**Run:**
```bash
# Basic usage
python examples/file_server.py

# With custom base directory
python examples/file_server.py --base-dir /path/to/directory

# With SSE transport
python examples/file_server.py --transport sse --port 8080
```

### 4. Math Server (`math_server.py`)
Mathematical operations and calculations server.

**Features:**
- Arithmetic operations
- Statistical analysis
- Geometry calculations
- Number theory tools
- Random number generation
- Mathematical constants and formulas

**Tools:**
- `calculate` - Evaluate expressions
- `statistics_summary` - Statistical analysis
- `linear_regression` - Simple regression
- `geometry_circle` - Circle properties
- `geometry_triangle` - Triangle properties
- `prime_check` - Prime number checking
- `fibonacci` - Fibonacci sequence
- `random_numbers` - Random generation

**Run:**
```bash
python examples/math_server.py
```

### 5. Autodiscovery Server (`autodiscovery_server.py`)
Example server with network autodiscovery enabled.

**Features:**
- Automatic network broadcasting
- Zero-configuration discovery
- Capability advertisement
- Custom metadata

**Run:**
```bash
# With autodiscovery (default)
python examples/autodiscovery_server.py

# Disable autodiscovery
python examples/autodiscovery_server.py --no-discovery
```

### 6. Discovery Client (`discover_servers.py`)
Tool for discovering MakeMCP servers on the network.

**Features:**
- Find servers on local network
- Display server capabilities
- Export to JSON
- Continuous monitoring

**Run:**
```bash
# Discover once
python examples/discover_servers.py

# Continuous monitoring
python examples/discover_servers.py continuous

# Export to file
python examples/discover_servers.py export --output servers.json
```

## Running Examples

All examples support both stdio and SSE transports:

### Stdio Transport (Default)
```bash
python examples/<example_name>.py
```

Use with MCP clients:
```bash
# Test with MCP inspector
mcp-inspector stdio -- python examples/<example_name>.py

# Use with Gleitzeit or other MCP clients
```

### SSE Transport
```bash
python examples/<example_name>.py --transport sse --port 8080
```

Connect with:
```bash
mcp-client sse http://localhost:8080/sse
```

## Creating Your Own Server

Use these examples as templates for your own servers:

1. **Start with `simple_server.py`** for basic functionality
2. **Reference `advanced_server.py`** for complex features
3. **Use `file_server.py`** as a template for system integration
4. **Check `math_server.py`** for domain-specific servers
5. **Enable autodiscovery** for automatic network discovery

## Common Patterns

### Tool Registration
```python
@server.tool()
def my_tool(param: str) -> dict:
    """Tool description."""
    return {"result": param}
```

### Resource Registration
```python
@server.resource("data://{id}")
def get_data(id: str) -> str:
    """Resource description."""
    return f"Data for {id}"
```

### Prompt Registration
```python
@server.prompt()
def my_prompt(topic: str) -> str:
    """Generate a prompt."""
    return f"Explain {topic}"
```

### Async Operations
```python
@server.tool()
async def async_tool(param: str) -> str:
    await asyncio.sleep(1)
    return f"Processed {param}"
```

## Testing Your Server

1. **Unit Testing**: Test individual tools/resources
2. **Integration Testing**: Use MCP inspector
3. **Network Testing**: Test with autodiscovery
4. **Client Testing**: Connect with Gleitzeit

## Security Considerations

When building servers that access system resources:

1. **Sandbox Operations**: Restrict to specific directories
2. **Input Validation**: Validate all user inputs
3. **Size Limits**: Implement file/data size limits
4. **Path Traversal**: Prevent directory escape
5. **Rate Limiting**: Consider rate limits for operations
6. **Authentication**: Add auth for sensitive operations

## Support

For more information:
- [MakeMCP Documentation](https://github.com/leifmarkthaler/makemcp)
- [MCP Specification](https://modelcontextprotocol.io)
- [Gleitzeit Integration](https://github.com/leifmarkthaler/gleitzeit)