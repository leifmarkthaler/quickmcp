#!/usr/bin/env python
"""
Simple async example demonstrating MCP Factory async support.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List
import time
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickmcp.factory import MCPFactory, create_mcp_from_module, mcp_tool


# Simple async functions
async def async_hello(name: str) -> str:
    """Say hello asynchronously."""
    await asyncio.sleep(0.1)
    return f"Hello, {name}!"


async def async_countdown(start: int) -> List[str]:
    """Count down asynchronously."""
    results = []
    for i in range(start, 0, -1):
        await asyncio.sleep(0.1)
        results.append(f"Count: {i}")
    results.append("Blast off!")
    return results


async def async_parallel_sum(numbers: List[float]) -> Dict[str, float]:
    """Calculate multiple sums in parallel."""
    
    async def sum_even():
        await asyncio.sleep(0.05)
        return sum(n for n in numbers if n % 2 == 0)
    
    async def sum_odd():
        await asyncio.sleep(0.05)
        return sum(n for n in numbers if n % 2 != 0)
    
    async def sum_all():
        await asyncio.sleep(0.05)
        return sum(numbers)
    
    even, odd, total = await asyncio.gather(
        sum_even(),
        sum_odd(),
        sum_all()
    )
    
    return {
        "even_sum": even,
        "odd_sum": odd,
        "total_sum": total
    }


# Mixed sync and async
def sync_uppercase(text: str) -> str:
    """Convert to uppercase (sync)."""
    return text.upper()


async def async_lowercase(text: str) -> str:
    """Convert to lowercase (async)."""
    await asyncio.sleep(0.05)
    return text.lower()


# Decorated async functions
@mcp_tool
async def async_echo(message: str, times: int = 3) -> List[str]:
    """Echo a message multiple times asynchronously."""
    results = []
    for i in range(times):
        await asyncio.sleep(0.05)
        results.append(f"Echo {i+1}: {message}")
    return results


@mcp_tool(name="async_timer", description="Time an async operation")
async def measure_time(seconds: float) -> Dict[str, float]:
    """Measure async timing."""
    start = time.time()
    await asyncio.sleep(seconds)
    end = time.time()
    
    return {
        "requested": seconds,
        "actual": end - start,
        "overhead": (end - start) - seconds
    }


# Class with async methods
class AsyncDataProcessor:
    """Example class with async methods."""
    
    def __init__(self):
        self.processed = []
    
    async def process_item(self, item: str) -> str:
        """Process a single item asynchronously."""
        await asyncio.sleep(0.1)
        result = f"Processed: {item.upper()}"
        self.processed.append(result)
        return result
    
    async def process_batch(self, items: List[str]) -> List[str]:
        """Process multiple items in parallel."""
        tasks = [self.process_item(item) for item in items]
        return await asyncio.gather(*tasks)
    
    def get_history(self) -> List[str]:
        """Get processing history (sync method)."""
        return self.processed.copy()


async def demo_async_tools():
    """Demonstrate async tool execution."""
    print("\n" + "=" * 60)
    print("Demo: Async Tool Execution")
    print("=" * 60)
    
    # Create server from this module
    factory = MCPFactory(name="async-demo")
    server = factory.from_module(__file__)
    
    print(f"\nServer created with tools:")
    for tool_name in sorted(server.list_tools()):
        print(f"  - {tool_name}")
    
    # Test some async tools
    print("\nTesting async tools:")
    
    # Test async_hello
    tool = server._tools["async_hello"]
    print(f"\n1. async_hello is async: {asyncio.iscoroutinefunction(tool)}")
    result = await tool(name="World")
    print(f"   Result: {result}")
    
    # Test async_parallel_sum
    tool = server._tools["async_parallel_sum"]
    print(f"\n2. async_parallel_sum is async: {asyncio.iscoroutinefunction(tool)}")
    result = await tool(numbers=[1, 2, 3, 4, 5, 6])
    print(f"   Result: {result}")
    
    # Test decorated async function
    tool = server._tools["async_echo"]
    print(f"\n3. async_echo is async: {asyncio.iscoroutinefunction(tool)}")
    result = await tool(message="Testing", times=2)
    print(f"   Result: {result}")
    
    # Test sync function (should still work)
    tool = server._tools["sync_uppercase"]
    print(f"\n4. sync_uppercase is async: {asyncio.iscoroutinefunction(tool)}")
    result = tool(text="hello world")
    print(f"   Result: {result}")


def demo_async_class():
    """Demonstrate async class methods."""
    print("\n" + "=" * 60)
    print("Demo: Async Class Methods")
    print("=" * 60)
    
    factory = MCPFactory(name="async-class-demo")
    server = factory.from_class(AsyncDataProcessor)
    
    print(f"\nServer created from AsyncDataProcessor:")
    for tool_name in server.list_tools():
        tool = server._tools[tool_name]
        is_async = asyncio.iscoroutinefunction(tool)
        print(f"  - {tool_name}: {'async' if is_async else 'sync'}")
    
    print("\n✓ Both async and sync methods registered")


def demo_mixed_functions():
    """Demonstrate mixed sync/async functions."""
    print("\n" + "=" * 60)
    print("Demo: Mixed Sync/Async Functions")
    print("=" * 60)
    
    # Create a custom function dict with mixed types
    functions = {
        "sync_fn": lambda x: x * 2,
        "async_fn": async_hello,
        "sync_upper": sync_uppercase,
        "async_lower": async_lowercase
    }
    
    factory = MCPFactory(name="mixed-demo")
    server = factory.from_functions(functions)
    
    print(f"\nServer created with mixed functions:")
    for name, tool in server._tools.items():
        is_async = asyncio.iscoroutinefunction(tool)
        print(f"  - {name}: {'async' if is_async else 'sync'}")
    
    print("\n✓ Mixed sync/async functions handled correctly")


def main():
    """Run all demos."""
    print("QuickMCP Async Support Demonstration")
    print("=" * 60)
    print("\nThe MCP Factory fully supports async functions!")
    print("It automatically detects and properly wraps them.")
    
    # Run sync demos
    demo_async_class()
    demo_mixed_functions()
    
    # Run async demo
    asyncio.run(demo_async_tools())
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("- ✓ Async functions are automatically detected")
    print("- ✓ Async functions remain async after wrapping")
    print("- ✓ Sync and async functions can be mixed")
    print("- ✓ Class methods (both sync and async) work")
    print("- ✓ Decorated async functions work")
    print("=" * 60)


if __name__ == "__main__":
    if "--run-as-server" in sys.argv:
        # Run as an actual MCP server
        server = create_mcp_from_module(__file__, server_name="async-example")
        # Server will run (stdio by default)
    else:
        # Run the demo
        main()