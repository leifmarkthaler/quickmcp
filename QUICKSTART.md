# MakeMCP - 2 Minute Quickstart

Get an MCP server running in under 2 minutes!

## 1. Install (10 seconds)

```bash
# Fast install with uv
uv pip install git+https://github.com/leifmarkthaler/makemcp.git
```

Don't have uv? `curl -LsSf https://astral.sh/uv/install.sh | sh` (it's worth it - 10-100x faster)

## 2. Create Your First Server (1 minute)

Create a file `hello_server.py`:

```python
from makemcp import MakeMCPServer

server = MakeMCPServer("hello")

@server.tool()
def greet(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}! 👋"

@server.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

if __name__ == "__main__":
    server.run()
```

## 3. Run It (10 seconds)

```bash
python hello_server.py
```

That's it! Your MCP server is running. 🎉

## 4. Test It (30 seconds)

In another terminal:
```bash
# If you have mcp-client installed
echo '{"method": "tools/list"}' | python hello_server.py
```

## 5. Use Your Existing Code (1 minute)

Have existing Python code? No need to rewrite anything:

```bash
# Turn ANY Python file into an MCP server instantly
mcp-factory my_utils.py

# Or in Python
from makemcp.factory import create_mcp_from_module
server = create_mcp_from_module("my_utils.py")
```

## That's All! 🚀

You now have a working MCP server. Here's what you can do next:

### Add More Tools

```python
@server.tool()
async def fetch_weather(city: str) -> dict:
    """Get weather for a city."""
    # Your async code works automatically!
    return {"city": city, "temp": 72}
```

### Add Resources

```python
@server.resource("data://{key}")
def get_data(key: str) -> str:
    """Get data by key."""
    return f"Data for {key}"
```

### Use With Claude Desktop

Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "hello": {
      "command": "python",
      "args": ["path/to/hello_server.py"]
    }
  }
}
```

## Common Patterns

### Pattern 1: Math Tools
```python
@server.tool()
def calculate(expression: str) -> float:
    """Safely evaluate a math expression."""
    # Only allow safe operations
    allowed = set("0123456789+-*/()., ")
    if all(c in allowed for c in expression):
        return eval(expression)
    return 0.0
```

### Pattern 2: File Operations
```python
@server.tool()
def read_file(path: str) -> str:
    """Read a text file."""
    with open(path, 'r') as f:
        return f.read()
```

### Pattern 3: Web Requests
```python
@server.tool()
async def fetch_url(url: str) -> dict:
    """Fetch data from a URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return {
                "status": response.status,
                "text": await response.text()
            }
```

## Troubleshooting

**Import Error?**
```bash
pip install makemcp
```

**Missing dependencies?**
The factory will tell you exactly what to install:
```bash
❌ Missing: numpy
💡 Quick install: pip install numpy
```

**Need help?**
- Examples: `/examples` folder
- Docs: [README.md](README.md)
- Issues: [GitHub Issues](https://github.com/leifmarkthaler/makemcp/issues)

## Next Steps

1. **Explore examples**: Check out `/examples` folder
2. **Read the docs**: See [README.md](README.md) for full documentation
3. **Join the community**: Contribute or ask questions on GitHub

---

**Remember**: MakeMCP is designed to be simple. If something feels complicated, we probably have an easier way. Just ask!