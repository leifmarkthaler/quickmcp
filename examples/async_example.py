#!/usr/bin/env python
"""
Example demonstrating async function support in MCP Factory.
"""

import asyncio
import aiohttp
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickmcp.factory import MCPFactory, mcp_tool


# Async utility functions
async def fetch_url(url: str, timeout: int = 10) -> Dict[str, any]:
    """Fetch content from a URL asynchronously."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=timeout) as response:
                return {
                    "status": response.status,
                    "content": await response.text(),
                    "headers": dict(response.headers),
                    "url": str(response.url)
                }
        except asyncio.TimeoutError:
            return {"error": "Request timed out"}
        except Exception as e:
            return {"error": str(e)}


async def parallel_fetch(urls: List[str]) -> List[Dict]:
    """Fetch multiple URLs in parallel."""
    tasks = [fetch_url(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [
        result if isinstance(result, dict) else {"error": str(result)}
        for result in results
    ]


async def delayed_response(message: str, delay: float = 1.0) -> str:
    """Return a message after a delay (simulating async work)."""
    await asyncio.sleep(delay)
    return f"After {delay}s delay: {message}"


async def async_calculation(numbers: List[float]) -> Dict[str, float]:
    """Perform calculations asynchronously."""
    await asyncio.sleep(0.1)  # Simulate async work
    
    # Simulate parallel calculations
    async def calc_sum():
        await asyncio.sleep(0.05)
        return sum(numbers)
    
    async def calc_product():
        await asyncio.sleep(0.05)
        result = 1
        for n in numbers:
            result *= n
        return result
    
    async def calc_average():
        await asyncio.sleep(0.05)
        return sum(numbers) / len(numbers) if numbers else 0
    
    # Run calculations in parallel
    results = await asyncio.gather(
        calc_sum(),
        calc_product(),
        calc_average()
    )
    
    return {
        "sum": results[0],
        "product": results[1],
        "average": results[2],
        "min": min(numbers) if numbers else None,
        "max": max(numbers) if numbers else None
    }


async def stream_data(count: int = 5) -> List[str]:
    """Simulate streaming data asynchronously."""
    results = []
    for i in range(count):
        await asyncio.sleep(0.2)
        results.append(f"Data chunk {i+1}")
    return results


# Mixed sync and async functions
def sync_process(data: str) -> str:
    """Synchronous data processing."""
    return data.upper()


async def async_process(data: str) -> str:
    """Asynchronous data processing."""
    await asyncio.sleep(0.1)
    return data.lower()


# Decorated async functions
@mcp_tool
async def decorated_async_fetch(url: str) -> Dict:
    """Decorated async function for fetching URLs."""
    await asyncio.sleep(0.5)
    # Simulate fetch without actual HTTP call
    return {
        "url": url,
        "mock_data": "This is mock data",
        "timestamp": time.time()
    }


@mcp_tool(name="async_batch", description="Process batch asynchronously")
async def decorated_batch_process(items: List[str]) -> List[str]:
    """Process items in batch asynchronously."""
    async def process_item(item):
        await asyncio.sleep(0.1)
        return f"Processed: {item}"
    
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)


# Class with async methods
class AsyncProcessor:
    """Class with async methods."""
    
    def __init__(self):
        self.processed_count = 0
    
    async def async_method(self, value: str) -> str:
        """Async method in class."""
        await asyncio.sleep(0.1)
        self.processed_count += 1
        return f"Async processed: {value}"
    
    def sync_method(self, value: str) -> str:
        """Sync method in class."""
        self.processed_count += 1
        return f"Sync processed: {value}"
    
    async def batch_async(self, items: List[str]) -> List[str]:
        """Process batch asynchronously."""
        results = []
        for item in items:
            await asyncio.sleep(0.05)
            results.append(f"Batch: {item}")
        return results


async def test_async_execution():
    """Test executing async functions through MCP Factory."""
    print("Testing Async Function Execution")
    print("=" * 60)
    
    # Create server from module with async functions
    factory = MCPFactory(name="async-test")
    server = factory.from_module(__file__)
    
    print(f"Created server with {len(server.list_tools())} tools")
    print(f"Tools: {', '.join(server.list_tools())}\n")
    
    # Test async tool execution
    print("Testing async tools:")
    
    # Get the delayed_response tool
    tool = server._tools.get("delayed_response")
    if tool:
        print("- Testing delayed_response...")
        if asyncio.iscoroutinefunction(tool):
            result = await tool(message="Hello", delay=0.5)
        else:
            result = tool(message="Hello", delay=0.5)
        print(f"  Result: {result}")
    
    # Get the async_calculation tool
    tool = server._tools.get("async_calculation")
    if tool:
        print("- Testing async_calculation...")
        if asyncio.iscoroutinefunction(tool):
            result = await tool(numbers=[1, 2, 3, 4, 5])
        else:
            result = tool(numbers=[1, 2, 3, 4, 5])
        print(f"  Result: {result}")
    
    # Test decorated async function
    tool = server._tools.get("decorated_async_fetch")
    if tool:
        print("- Testing decorated_async_fetch...")
        if asyncio.iscoroutinefunction(tool):
            result = await tool(url="https://example.com")
        else:
            result = tool(url="https://example.com")
        print(f"  Result: {result}")
    
    print("\n" + "=" * 60)
    print("Async execution test complete!")


def test_async_class():
    """Test creating server from class with async methods."""
    print("\nTesting Async Class Methods")
    print("=" * 60)
    
    factory = MCPFactory()
    server = factory.from_class(AsyncProcessor)
    
    print(f"Created server from AsyncProcessor class")
    print(f"Tools: {', '.join(server.list_tools())}")
    
    # The async methods should be registered
    assert "async_method" in server.list_tools()
    assert "sync_method" in server.list_tools()
    assert "batch_async" in server.list_tools()
    
    print("✓ All async and sync methods registered as tools")
    print("=" * 60)


def test_decorated_async():
    """Test that decorated async functions are discovered."""
    print("\nTesting Decorated Async Functions")
    print("=" * 60)
    
    factory = MCPFactory()
    server = factory.from_file_with_decorators(__file__, decorator_name="mcp_tool")
    
    print(f"Found decorated functions: {', '.join(server.list_tools())}")
    
    assert "decorated_async_fetch" in server.list_tools()
    assert "decorated_batch_process" in server.list_tools()
    
    print("✓ Decorated async functions discovered correctly")
    print("=" * 60)


def main():
    """Run all async tests."""
    print("QuickMCP Async Support Demo")
    print("=" * 60)
    
    # Test decorated async discovery
    test_decorated_async()
    
    # Test class with async methods
    test_async_class()
    
    # Test async execution
    asyncio.run(test_async_execution())
    
    print("\nAll async tests completed successfully!")


if __name__ == "__main__":
    # Check if running as MCP server
    if "--info" in sys.argv:
        # This would be called by the discovery system
        factory = MCPFactory(name="async-example")
        server = factory.from_module(__file__)
        info = {
            "name": "async-example",
            "version": "1.0.0",
            "description": "Async function examples for MCP",
            "capabilities": {
                "tools": server.list_tools()
            }
        }
        print(json.dumps(info))
        sys.exit(0)
    
    # Run tests
    main()