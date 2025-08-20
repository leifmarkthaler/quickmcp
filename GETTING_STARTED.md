# Getting Started with QuickMCP

## Installation (10 seconds)

```bash
# Get uv (if you don't have it) - makes everything 10-100x faster
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install QuickMCP
uv pip install git+https://github.com/leifmarkthaler/quickmcp.git
```

## Your First Server (30 seconds)

Create `server.py`:

```python
from quickmcp.quick import tool, run

@tool
def hello(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

run()
```

Run it:
```bash
python server.py
```

That's it! You have a working MCP server with two tools.

## Use Your Existing Code (10 seconds)

Have a Python file with functions? Turn it into an MCP server instantly:

```python
from quickmcp.quick import from_file

# Any Python file becomes a server
from_file("my_utils.py").run()
```

Or from the command line:
```bash
mcp-factory my_utils.py
```

## Common Patterns

### Async Functions (Just Works™)

```python
from quickmcp.quick import tool, run
import asyncio

@tool
async def slow_process(data: str) -> str:
    """Process data slowly."""
    await asyncio.sleep(1)
    return data.upper()

@tool
def fast_process(data: str) -> str:
    """Process data fast."""
    return data.lower()

run()  # Both sync and async work together
```

### Working with Files

```python
from quickmcp.quick import tool, run
from pathlib import Path

@tool
def read_file(path: str) -> str:
    """Read a text file."""
    return Path(path).read_text()

@tool
def write_file(path: str, content: str) -> bool:
    """Write a text file."""
    Path(path).write_text(content)
    return True

@tool
def list_files(directory: str = ".") -> list:
    """List files in a directory."""
    return [f.name for f in Path(directory).iterdir()]

run()
```

### Web Requests

```python
from quickmcp.quick import tool, run
import urllib.request
import json

@tool
def fetch_json(url: str) -> dict:
    """Fetch JSON from a URL."""
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

@tool
async def fetch_many(urls: list) -> list:
    """Fetch multiple URLs in parallel."""
    import asyncio
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(session.get(url))
        responses = await asyncio.gather(*tasks)
        return [await r.text() for r in responses]

run()
```

## Next Steps

1. **Explore More Examples**: Check `/examples` folder
2. **Add Resources**: Learn about `@server.resource()` decorator
3. **Add Prompts**: Learn about `@server.prompt()` decorator
4. **Configure Transport**: Use SSE instead of stdio
5. **Enable Discovery**: Let clients find your server automatically

## Tips

- **Start Simple**: Just use `@tool` and `run()`
- **Type Hints = Better Docs**: Your type hints become the schema
- **Docstrings = Descriptions**: Your docstrings become tool descriptions
- **Async Just Works**: Mix async and sync freely
- **Use Your Code**: Don't rewrite, just import with `from_file()`

## Getting Help

- **Examples**: `/examples` folder has many examples
- **Docs**: [README.md](README.md) has full documentation
- **Issues**: [GitHub Issues](https://github.com/leifmarkthaler/quickmcp/issues)

Remember: If something feels complicated, there's probably an easier way!