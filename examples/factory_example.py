#!/usr/bin/env python
"""
Example of using MCP Factory to create servers from existing Python code.
Demonstrates the refactored factory with configuration, dependency analysis, and async support.
"""

import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcplite.factory import (
    MCPFactory, 
    create_mcp_from_module, 
    mcp_tool,
    FactoryConfig,
    create_safe_config,
    create_development_config,
    analyze_dependencies,
    print_dependency_report
)


# Example 1: Python module with various functions (sync and async)
def calculate_sum(numbers: list) -> float:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def calculate_average(numbers: list) -> float:
    """Calculate the average of a list of numbers."""
    return sum(numbers) / len(numbers) if numbers else 0


async def fetch_data(url: str) -> dict:
    """Async function to simulate data fetching."""
    await asyncio.sleep(0.1)  # Simulate network delay
    return {
        "url": url,
        "status": 200,
        "data": f"Data from {url}"
    }


async def process_async(items: List[str]) -> List[str]:
    """Process items asynchronously."""
    async def process_one(item: str) -> str:
        await asyncio.sleep(0.01)
        return item.upper()
    
    tasks = [process_one(item) for item in items]
    return await asyncio.gather(*tasks)


def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


def count_words(text: str) -> int:
    """Count the number of words in a text."""
    return len(text.split())


def _private_function():
    """This is a private function (won't be exposed by default)."""
    return "private"


# Example 2: Class with mixed sync/async methods
class DataProcessor:
    """A class for processing data with both sync and async methods."""
    
    def __init__(self):
        self.processed_count = 0
        self.cache = {}
    
    def process_sync(self, data: str) -> str:
        """Synchronous processing."""
        self.processed_count += 1
        result = data.upper()
        self.cache[data] = result
        return result
    
    async def process_async(self, data: str) -> str:
        """Asynchronous processing."""
        await asyncio.sleep(0.05)  # Simulate async work
        self.processed_count += 1
        result = data.lower()
        self.cache[data] = result
        return result
    
    async def batch_process(self, items: List[str]) -> List[str]:
        """Process multiple items in parallel."""
        tasks = [self.process_async(item) for item in items]
        results = await asyncio.gather(*tasks)
        return results
    
    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {
            "processed_count": self.processed_count,
            "cache_size": len(self.cache)
        }
    
    def clear_cache(self) -> None:
        """Clear the cache."""
        self.cache.clear()


# Example 3: Functions with decorator
@mcp_tool
def decorated_add(a: float, b: float) -> float:
    """Add two numbers (decorated)."""
    return a + b


@mcp_tool(name="multiply_numbers", description="Multiply two numbers together")
async def decorated_multiply(a: float, b: float) -> float:
    """Async multiply two numbers (decorated)."""
    await asyncio.sleep(0.01)  # Show it's async
    return a * b


@mcp_tool
async def decorated_fetch(endpoint: str) -> Dict[str, Any]:
    """Decorated async fetch function."""
    await asyncio.sleep(0.1)
    return {
        "endpoint": endpoint,
        "timestamp": "2024-01-01T00:00:00Z",
        "data": {"message": "Hello from async decorated function"}
    }


def not_decorated_function():
    """This function is not decorated."""
    return "not decorated"


# Example 4: Module with optional dependencies (for dependency analysis demo)
def demo_optional_deps():
    """Function with optional dependencies."""
    try:
        import pandas as pd
        HAS_PANDAS = True
    except ImportError:
        HAS_PANDAS = False
    
    if HAS_PANDAS:
        return pd.DataFrame({"a": [1, 2, 3]})
    else:
        return {"a": [1, 2, 3]}


def demo_module_factory():
    """Demo: Create MCP server from current module with configuration."""
    print("=" * 60)
    print("Demo 1: Create MCP server from current module")
    print("=" * 60)
    
    # Show different configuration options
    print("\nUsing development configuration...")
    config = create_development_config()
    
    factory = MCPFactory(name="math-tools", config=config)
    server = factory.from_module(__file__, include_private=False)
    
    print(f"Created server: {server.name}")
    print(f"Description: {server.description}")
    print(f"Tools created: {len(server.list_tools())}")
    
    # Show which are async
    sync_tools = []
    async_tools = []
    for tool_name in server.list_tools():
        tool = server._tools.get(tool_name)
        if tool and asyncio.iscoroutinefunction(tool):
            async_tools.append(tool_name)
        else:
            sync_tools.append(tool_name)
    
    print(f"\nSync tools ({len(sync_tools)}):")
    for tool in sync_tools:
        print(f"  - {tool}")
    
    print(f"\nAsync tools ({len(async_tools)}):")
    for tool in async_tools:
        print(f"  - {tool} ⚡")
    
    return server


def demo_class_factory():
    """Demo: Create MCP server from a class with async methods."""
    print("\n" + "=" * 60)
    print("Demo 2: Create MCP server from DataProcessor class")
    print("=" * 60)
    
    # Use safe configuration for class
    config = create_safe_config()
    config.allow_code_execution = True  # Need to execute to load class
    
    factory = MCPFactory(config=config)
    server = factory.from_class(DataProcessor)
    
    print(f"Created server: {server.name}")
    print(f"Description: {server.description}")
    print(f"Tools created: {len(server.list_tools())}")
    
    # Show sync vs async methods
    for tool_name in server.list_tools():
        tool = server._tools.get(tool_name)
        if tool and asyncio.iscoroutinefunction(tool):
            print(f"  - {tool_name} ⚡ (async)")
        else:
            print(f"  - {tool_name} (sync)")
    
    return server


def demo_dependency_analysis():
    """Demo: Analyze dependencies before creating server."""
    print("\n" + "=" * 60)
    print("Demo 3: Dependency Analysis")
    print("=" * 60)
    
    # Analyze this file's dependencies
    print("\nAnalyzing dependencies for current file...")
    print_dependency_report(__file__)
    
    # Show how to handle missing dependencies
    missing_deps = analyze_dependencies(__file__)
    if missing_deps:
        print(f"\nFound {len(missing_deps)} missing dependencies")
        for dep in missing_deps:
            print(f"  - {dep.module} ({dep.import_type})")
            if dep.suggested_install:
                print(f"    Install: uv pip install {dep.suggested_install}")
    else:
        print("\n✅ All dependencies are available!")
    
    return missing_deps


def demo_configured_factory():
    """Demo: Create factory with custom configuration."""
    print("\n" + "=" * 60)
    print("Demo 4: Custom Configuration")
    print("=" * 60)
    
    # Create custom configuration
    config = FactoryConfig(
        # Dependency settings
        check_dependencies=True,
        warn_on_optional_missing=True,
        
        # Type conversion settings
        strict_type_conversion=False,
        convert_complex_types=True,
        
        # Performance settings
        cache_dependency_analysis=True,
        cache_type_conversions=True,
        
        # Safety limits
        max_result_size=5_000_000,  # 5MB
        max_string_length=50_000,
        
        # Custom pip mappings
        additional_pip_mappings={
            "cv2": "opencv-python",
            "sklearn": "scikit-learn"
        }
    )
    
    print("Custom configuration:")
    print(f"  - Check dependencies: {config.check_dependencies}")
    print(f"  - Cache enabled: {config.cache_dependency_analysis}")
    print(f"  - Max result size: {config.max_result_size:,} bytes")
    print(f"  - Custom mappings: {len(config.additional_pip_mappings)}")
    
    # Create factory with custom config
    factory = MCPFactory(name="configured-server", config=config)
    
    # Select specific functions
    selected_functions = {
        "sum": calculate_sum,
        "avg": calculate_average,
        "reverse": reverse_string,
        "fetch": fetch_data,  # Async function
        "process": process_async  # Another async function
    }
    
    server = factory.from_functions(selected_functions)
    
    print(f"\nCreated server: {server.name}")
    print(f"Tools created: {len(server.list_tools())}")
    for tool in server.list_tools():
        print(f"  - {tool}")
    
    return server


def demo_decorated_functions():
    """Demo: Create MCP server from decorated functions only."""
    print("\n" + "=" * 60)
    print("Demo 5: Decorated Functions (with async)")
    print("=" * 60)
    
    factory = MCPFactory()
    server = factory.from_file_with_decorators(__file__, decorator_name="mcp_tool")
    
    print(f"Created server: {server.name}")
    print(f"Tools created: {len(server.list_tools())}")
    
    # Show which decorated functions are async
    for tool_name in server.list_tools():
        tool = server._tools.get(tool_name)
        if tool and asyncio.iscoroutinefunction(tool):
            print(f"  - {tool_name} ⚡ (async decorated)")
        else:
            print(f"  - {tool_name} (sync decorated)")
    
    return server


def demo_error_handling():
    """Demo: Error handling and missing dependencies."""
    print("\n" + "=" * 60)
    print("Demo 6: Error Handling")
    print("=" * 60)
    
    # Create a test file with missing dependencies
    test_code = '''
import numpy as np  # This might be missing
import definitely_missing_module  # This will definitely be missing

def calculate_mean(data):
    return np.mean(data)
'''
    
    from tempfile import NamedTemporaryFile
    
    with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        print(f"\nTrying to create server from file with missing dependencies...")
        factory = MCPFactory()
        server = factory.from_module(temp_file)
        print("✅ Server created successfully")
    except Exception as e:
        print(f"❌ Error: {e.__class__.__name__}")
        
        if hasattr(e, 'format_error_message'):
            print("\nDetailed error message:")
            print(e.format_error_message())
        
        if hasattr(e, 'get_install_commands'):
            commands = e.get_install_commands()
            if commands:
                print("\nInstall commands:")
                for dep_type, cmd in commands.items():
                    print(f"  {dep_type}: {cmd}")
    
    finally:
        # Clean up
        Path(temp_file).unlink()


async def demo_async_execution():
    """Demo: Execute async tools."""
    print("\n" + "=" * 60)
    print("Demo 7: Async Tool Execution")
    print("=" * 60)
    
    # Create server with async functions
    factory = MCPFactory()
    server = factory.from_functions({
        "fetch": fetch_data,
        "process": process_async,
        "sync_reverse": reverse_string  # Mix sync and async
    })
    
    print("Testing async tool execution...")
    
    # Test async tool
    fetch_tool = server._tools["fetch"]
    if asyncio.iscoroutinefunction(fetch_tool):
        result = await fetch_tool(url="https://example.com")
        print(f"✅ Async fetch result: {result}")
    
    # Test another async tool
    process_tool = server._tools["process"]
    if asyncio.iscoroutinefunction(process_tool):
        result = await process_tool(items=["hello", "world"])
        print(f"✅ Async process result: {result}")
    
    # Test sync tool still works
    reverse_tool = server._tools["sync_reverse"]
    result = reverse_tool(text="hello")
    print(f"✅ Sync reverse result: {result}")
    
    return server


def main():
    """Run all demos."""
    print("QuickMCP Factory Examples (Refactored)")
    print("=" * 60)
    print("Demonstrates:")
    print("  - Configuration system")
    print("  - Dependency analysis")
    print("  - Async function support")
    print("  - Error handling")
    print("  - UV integration (if available)")
    print()
    
    # Check if uv is available
    import shutil
    if shutil.which('uv'):
        print("✅ UV detected - will use for faster installations")
    else:
        print("ℹ️  UV not detected - using standard pip")
    print()
    
    # Run demos
    server1 = demo_module_factory()
    server2 = demo_class_factory()
    deps = demo_dependency_analysis()
    server3 = demo_configured_factory()
    server4 = demo_decorated_functions()
    demo_error_handling()
    
    # Run async demo
    print("\nRunning async demo...")
    asyncio.run(demo_async_execution())
    
    print("\n" + "=" * 60)
    print("Factory Examples Complete!")
    print("=" * 60)
    
    # Optionally run one of the servers
    if "--run" in sys.argv:
        print("\nRunning the math-tools server...")
        print("Connect with: mcp-client stdio")
        server1.run()


if __name__ == "__main__":
    main()