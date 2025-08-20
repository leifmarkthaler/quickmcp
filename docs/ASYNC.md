# Async Support in QuickMCP

QuickMCP provides comprehensive support for asynchronous (async/await) functions, allowing you to build high-performance MCP servers that can handle concurrent operations efficiently.

## Overview

QuickMCP's async support includes:

- **Automatic Detection**: Async functions are automatically detected and properly handled
- **Preserve Async Nature**: Async functions remain async after wrapping - no conversion to sync
- **Mixed Support**: You can mix sync and async functions in the same server
- **Class Methods**: Both sync and async methods in classes work seamlessly
- **Factory Support**: The MCP Factory system fully supports async functions
- **Decorator Support**: The `@mcp_tool` decorator works with async functions

## Key Features

### 1. Automatic Detection and Wrapping

QuickMCP uses `inspect.iscoroutinefunction()` to detect async functions and creates appropriate wrappers:

```python
# In MCPFactory._register_function_as_tool()
if inspect.iscoroutinefunction(func):
    async def tool_wrapper(**kwargs):
        # Type conversion and validation
        converted_args = self._convert_arguments(kwargs, sig, type_hints)
        
        # Call the original async function (preserving await)
        result = await func(**converted_args)
        
        # Convert result to JSON-serializable format
        return self._convert_result(result)
else:
    def tool_wrapper(**kwargs):
        # Sync function wrapper
        # ...
```

### 2. Preserving Async Nature

Unlike many wrapper systems, QuickMCP preserves the async nature of functions:

```python
import asyncio
from quickmcp.factory import MCPFactory

async def my_async_function(x: int) -> int:
    await asyncio.sleep(0.1)
    return x * 2

factory = MCPFactory()
server = factory.from_functions({"async_func": my_async_function})

# The wrapped function is still async
tool = server._tools["async_func"]
assert asyncio.iscoroutinefunction(tool)  # True
```

## Usage Examples

### Basic Async Tools

```python
from quickmcp import QuickMCPServer
import asyncio
import aiohttp

server = QuickMCPServer("async-server")

@server.tool()
async def fetch_url(url: str) -> dict:
    """Fetch content from a URL asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return {
                "url": url,
                "status": response.status,
                "content": await response.text(),
                "headers": dict(response.headers)
            }

@server.tool()
async def parallel_fetch(urls: list) -> list:
    """Fetch multiple URLs in parallel."""
    tasks = [fetch_url(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [
        result if isinstance(result, dict) else {"error": str(result)}
        for result in results
    ]

server.run()
```

### Mixed Sync and Async Functions

```python
from quickmcp import QuickMCPServer
import asyncio

server = QuickMCPServer("mixed-server")

# Async function
@server.tool()
async def slow_calculation(x: int, y: int) -> int:
    """Perform calculation with simulated delay."""
    await asyncio.sleep(1)  # Simulate complex computation
    return x * y

# Sync function
@server.tool()
def quick_add(x: int, y: int) -> int:
    """Quick addition (synchronous)."""
    return x + y

# Both work in the same server
server.run()
```

### Async Class Methods

```python
from quickmcp.factory import MCPFactory
import asyncio
import aiohttp

class AsyncWebScraper:
    """Web scraper with async methods."""
    
    def __init__(self):
        self.scraped_urls = []
        self.session = None
    
    async def scrape_url(self, url: str) -> dict:
        """Scrape content from a URL."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(url) as response:
                content = await response.text()
                self.scraped_urls.append(url)
                
                return {
                    "url": url,
                    "status": response.status,
                    "content_length": len(content),
                    "title": self._extract_title(content)
                }
        except Exception as e:
            return {"url": url, "error": str(e)}
    
    def _extract_title(self, html: str) -> str:
        """Extract title from HTML (sync helper)."""
        # Simple title extraction
        start = html.find("<title>")
        if start == -1:
            return "No title found"
        end = html.find("</title>", start)
        return html[start + 7:end] if end != -1 else "No title found"
    
    async def batch_scrape(self, urls: list) -> dict:
        """Scrape multiple URLs in parallel."""
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = [r for r in results if isinstance(r, dict) and "error" not in r]
        failed = [r for r in results if isinstance(r, dict) and "error" in r]
        
        return {
            "total": len(urls),
            "successful": len(successful),
            "failed": len(failed),
            "results": results
        }
    
    def get_stats(self) -> dict:
        """Get scraping statistics (sync method)."""
        return {
            "total_scraped": len(self.scraped_urls),
            "urls": self.scraped_urls.copy()
        }

# Create server from class
factory = MCPFactory(name="web-scraper")
server = factory.from_class(AsyncWebScraper)
server.run()
```

### Using the MCP Factory with Async Modules

```python
# async_utilities.py
import asyncio
import json
import time
from typing import Dict, List

async def process_data_stream(data: List[dict]) -> Dict[str, any]:
    """Process a stream of data asynchronously."""
    results = []
    
    for item in data:
        await asyncio.sleep(0.01)  # Simulate processing time
        processed = {
            "id": item.get("id"),
            "processed_at": time.time(),
            "result": item.get("value", 0) * 2
        }
        results.append(processed)
    
    return {
        "processed_count": len(results),
        "processing_time": sum(0.01 for _ in results),
        "results": results
    }

async def concurrent_calculations(numbers: List[float]) -> Dict[str, float]:
    """Perform multiple calculations concurrently."""
    
    async def calc_sum():
        await asyncio.sleep(0.1)
        return sum(numbers)
    
    async def calc_product():
        await asyncio.sleep(0.1)
        result = 1
        for n in numbers:
            result *= n
        return result
    
    async def calc_stats():
        await asyncio.sleep(0.1)
        return {
            "min": min(numbers) if numbers else 0,
            "max": max(numbers) if numbers else 0,
            "avg": sum(numbers) / len(numbers) if numbers else 0
        }
    
    # Run calculations in parallel
    total, product, stats = await asyncio.gather(
        calc_sum(),
        calc_product(),
        calc_stats()
    )
    
    return {
        "sum": total,
        "product": product,
        **stats
    }

def sync_validator(data: dict) -> bool:
    """Validate data structure (sync function)."""
    required_fields = ["id", "value"]
    return all(field in data for field in required_fields)

# Generate MCP server from this module
if __name__ == "__main__":
    from quickmcp.factory import create_mcp_from_module
    server = create_mcp_from_module(__file__, server_name="async-utilities")
    server.run()
```

Then use the factory:

```bash
# CLI usage
mcp-factory async_utilities.py --name async-utils

# Or programmatically
from quickmcp.factory import create_mcp_from_module
server = create_mcp_from_module("async_utilities.py")
```

### Decorated Async Functions

```python
from quickmcp.factory import mcp_tool, create_mcp_from_module
import asyncio

@mcp_tool
async def fetch_and_process(url: str, transform: str = "upper") -> dict:
    """Fetch URL content and apply transformation."""
    # Simulate fetching
    await asyncio.sleep(0.5)
    mock_content = f"Content from {url}"
    
    # Apply transformation
    if transform == "upper":
        content = mock_content.upper()
    elif transform == "lower":
        content = mock_content.lower()
    else:
        content = mock_content
    
    return {
        "url": url,
        "transformed_content": content,
        "transform": transform
    }

@mcp_tool(name="async_timer", description="Time an async operation")
async def measure_async_operation(duration: float) -> dict:
    """Measure the timing of an async operation."""
    start = time.time()
    await asyncio.sleep(duration)
    end = time.time()
    
    return {
        "requested_duration": duration,
        "actual_duration": end - start,
        "overhead": (end - start) - duration
    }

# Not decorated - won't be exposed
async def internal_helper(data: str) -> str:
    await asyncio.sleep(0.1)
    return data.strip()

# Create server from decorated functions only
if __name__ == "__main__":
    # Only @mcp_tool decorated functions become tools
    server = create_mcp_from_module(__file__)
    server.run()
```

## Performance Considerations

### Concurrent Execution

Async functions in QuickMCP can be executed concurrently, providing significant performance benefits:

```python
import asyncio
import time
from quickmcp import QuickMCPServer

server = QuickMCPServer("performance-demo")

@server.tool()
async def slow_operation(delay: float) -> dict:
    """Simulate a slow async operation."""
    start = time.time()
    await asyncio.sleep(delay)
    end = time.time()
    
    return {
        "delay": delay,
        "actual_time": end - start,
        "timestamp": end
    }

# Multiple calls to slow_operation can run concurrently
# instead of blocking each other
```

### Resource Management

For async functions that use resources (like HTTP sessions), consider proper resource management:

```python
import aiohttp
from quickmcp.factory import MCPFactory

class AsyncAPIClient:
    """API client with proper resource management."""
    
    def __init__(self):
        self._session = None
    
    async def _get_session(self):
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def make_request(self, url: str, method: str = "GET") -> dict:
        """Make HTTP request with session reuse."""
        session = await self._get_session()
        
        async with session.request(method, url) as response:
            return {
                "url": url,
                "method": method,
                "status": response.status,
                "content": await response.text()
            }
    
    async def cleanup(self) -> dict:
        """Clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()
        return {"cleanup": "completed"}

# The factory will create a single instance
# All method calls will reuse the same session
factory = MCPFactory()
server = factory.from_class(AsyncAPIClient)
```

## Testing Async Functions

Testing async MCP tools requires async test functions:

```python
import pytest
import asyncio
from quickmcp.factory import MCPFactory

# Your async functions
async def async_add(a: int, b: int) -> int:
    await asyncio.sleep(0.01)
    return a + b

@pytest.mark.asyncio
async def test_async_tool():
    """Test async function through factory."""
    factory = MCPFactory()
    server = factory.from_functions({"add": async_add})
    
    # Get the wrapped tool
    tool = server._tools["add"]
    
    # Verify it's still async
    assert asyncio.iscoroutinefunction(tool)
    
    # Test execution
    result = await tool(a=5, b=3)
    assert result == 8

@pytest.mark.asyncio
async def test_concurrent_execution():
    """Test that async tools can run concurrently."""
    factory = MCPFactory()
    server = factory.from_functions({"slow_add": async_add})
    
    tool = server._tools["slow_add"]
    
    # Execute multiple calls concurrently
    start = time.time()
    results = await asyncio.gather(
        tool(a=1, b=2),
        tool(a=3, b=4),
        tool(a=5, b=6)
    )
    end = time.time()
    
    assert results == [3, 7, 11]
    # Should be concurrent (~0.01s) not sequential (~0.03s)
    assert end - start < 0.02
```

## Error Handling

Async functions can raise exceptions that need proper handling:

```python
from quickmcp import QuickMCPServer
import asyncio

server = QuickMCPServer("error-handling")

@server.tool()
async def risky_operation(fail: bool = False) -> dict:
    """Operation that might fail."""
    await asyncio.sleep(0.1)
    
    if fail:
        raise ValueError("Operation failed as requested")
    
    return {"success": True, "result": "Operation completed"}

@server.tool()
async def handle_errors(operations: list) -> dict:
    """Handle multiple operations with error recovery."""
    results = []
    
    for i, op in enumerate(operations):
        try:
            # Each operation is awaited individually
            result = await risky_operation(fail=op.get("fail", False))
            results.append({"operation": i, "result": result})
        except Exception as e:
            results.append({"operation": i, "error": str(e)})
    
    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    
    return {
        "total": len(operations),
        "successful": len(successful),
        "failed": len(failed),
        "results": results
    }

server.run()
```

## Best Practices

### 1. Use Async for I/O Operations

```python
# Good: Use async for I/O bound operations
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Less optimal: Sync for I/O operations
def fetch_data_sync(url: str) -> dict:
    import requests
    response = requests.get(url)
    return response.json()
```

### 2. Mix Async and Sync Appropriately

```python
# CPU-bound operations can remain sync
def calculate_fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# I/O-bound operations should be async
async def save_to_database(data: dict) -> bool:
    # Simulate database operation
    await asyncio.sleep(0.1)
    return True

# Combine both in one server
from quickmcp.factory import MCPFactory
factory = MCPFactory()
server = factory.from_functions({
    "fibonacci": calculate_fibonacci,  # Sync
    "save_data": save_to_database      # Async
})
```

### 3. Proper Resource Management

```python
class AsyncResourceManager:
    def __init__(self):
        self.resources = {}
    
    async def get_resource(self, name: str):
        if name not in self.resources:
            # Create resource async
            await asyncio.sleep(0.1)
            self.resources[name] = f"Resource: {name}"
        return self.resources[name]
    
    async def cleanup_resources(self) -> dict:
        count = len(self.resources)
        self.resources.clear()
        return {"cleaned_up": count}
```

### 4. Use Type Hints

```python
from typing import List, Dict, Optional
import asyncio

async def process_batch(
    items: List[str], 
    batch_size: int = 10
) -> Dict[str, any]:
    """Process items in batches with type hints."""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(*[
            process_single_item(item) for item in batch
        ])
        results.extend(batch_results)
    
    return {
        "processed": len(results),
        "results": results
    }

async def process_single_item(item: str) -> str:
    await asyncio.sleep(0.01)
    return f"Processed: {item}"
```

## Debugging Async Functions

### 1. Enable Debug Logging

```python
import logging
import asyncio

# Enable asyncio debug mode
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
logging.basicConfig(level=logging.DEBUG)

from quickmcp import QuickMCPServer

server = QuickMCPServer("debug-server", log_level="DEBUG")
```

### 2. Use Async Context Managers

```python
import aiohttp
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def http_session():
    session = aiohttp.ClientSession()
    try:
        yield session
    finally:
        await session.close()

async def fetch_with_context(url: str) -> dict:
    """Fetch using context manager."""
    async with http_session() as session:
        async with session.get(url) as response:
            return {
                "url": url,
                "status": response.status,
                "content": await response.text()
            }
```

### 3. Monitor Async Tasks

```python
import asyncio
import time

async def monitored_operation(name: str, duration: float) -> dict:
    """Operation with monitoring."""
    start = time.time()
    
    try:
        await asyncio.sleep(duration)
        end = time.time()
        
        return {
            "name": name,
            "duration": duration,
            "actual_time": end - start,
            "success": True
        }
    except Exception as e:
        end = time.time()
        return {
            "name": name,
            "duration": duration,
            "actual_time": end - start,
            "success": False,
            "error": str(e)
        }
```

## Summary

QuickMCP's async support provides:

- ✅ **Automatic Detection**: Async functions are detected and wrapped properly
- ✅ **Preserved Behavior**: Async functions remain async, sync functions remain sync
- ✅ **Concurrent Execution**: Multiple async operations can run in parallel
- ✅ **Mixed Support**: Sync and async functions work together seamlessly
- ✅ **Class Method Support**: Both sync and async methods in classes work
- ✅ **Factory Integration**: MCP Factory fully supports async patterns
- ✅ **Decorator Compatibility**: `@mcp_tool` works with async functions
- ✅ **Error Handling**: Proper exception propagation for async functions
- ✅ **Type Safety**: Type hints are preserved and validated

This comprehensive async support makes QuickMCP ideal for building high-performance MCP servers that can handle I/O-bound operations efficiently while maintaining the simplicity of the decorator-based API.