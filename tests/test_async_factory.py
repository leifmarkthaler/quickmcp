"""
Test suite for async function support in MCP Factory
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
import sys

from quickmcp.factory import MCPFactory, create_mcp_from_module, mcp_tool
from quickmcp import QuickMCPServer


ASYNC_MODULE_CODE = '''
"""Module with async functions."""

import asyncio

async def async_add(a: int, b: int) -> int:
    """Add two numbers asynchronously."""
    await asyncio.sleep(0.01)
    return a + b

async def async_multiply(a: int, b: int) -> int:
    """Multiply two numbers asynchronously."""
    await asyncio.sleep(0.01)
    return a * b

def sync_subtract(a: int, b: int) -> int:
    """Subtract two numbers synchronously."""
    return a - b
'''

ASYNC_CLASS_CODE = '''
"""Module with async class methods."""

import asyncio

class AsyncProcessor:
    """Class with async methods."""
    
    def __init__(self):
        self.count = 0
    
    async def async_process(self, value: str) -> str:
        """Process value asynchronously."""
        await asyncio.sleep(0.01)
        self.count += 1
        return f"Processed: {value}"
    
    def sync_process(self, value: str) -> str:
        """Process value synchronously."""
        self.count += 1
        return f"Sync: {value}"
    
    async def batch_process(self, items: list) -> list:
        """Process batch asynchronously."""
        results = []
        for item in items:
            await asyncio.sleep(0.005)
            results.append(f"Batch: {item}")
        return results
'''

DECORATED_ASYNC_CODE = '''
"""Module with decorated async functions."""

import asyncio
from quickmcp.factory import mcp_tool

@mcp_tool
async def decorated_async(x: int) -> int:
    """Decorated async function."""
    await asyncio.sleep(0.01)
    return x * 2

@mcp_tool(name="custom_async", description="Custom async")
async def another_async(x: int) -> int:
    """Another decorated async."""
    await asyncio.sleep(0.01)
    return x + 10

async def not_decorated_async(x: int) -> int:
    """Not decorated async."""
    await asyncio.sleep(0.01)
    return x - 1
'''


class TestAsyncFunctionDiscovery:
    """Test discovering async functions."""
    
    def test_discover_async_functions(self, tmp_path):
        """Test that async functions are discovered."""
        module_file = tmp_path / "async_module.py"
        module_file.write_text(ASYNC_MODULE_CODE)
        
        factory = MCPFactory()
        server = factory.from_module(str(module_file))
        
        tools = server.list_tools()
        assert "async_add" in tools
        assert "async_multiply" in tools
        assert "sync_subtract" in tools
        
        # All functions should be registered
        assert len(tools) == 3
    
    def test_async_class_methods(self, tmp_path):
        """Test async methods in classes."""
        module_file = tmp_path / "async_class.py"
        module_file.write_text(ASYNC_CLASS_CODE)
        
        sys.path.insert(0, str(tmp_path))
        
        # Import the module to get the class
        spec = __import__("async_class")
        
        factory = MCPFactory()
        server = factory.from_class(spec.AsyncProcessor)
        
        tools = server.list_tools()
        assert "async_process" in tools
        assert "sync_process" in tools
        assert "batch_process" in tools
        
        sys.path.remove(str(tmp_path))
    
    def test_decorated_async_functions(self, tmp_path):
        """Test decorated async functions."""
        module_file = tmp_path / "decorated_async.py"
        module_file.write_text(DECORATED_ASYNC_CODE)
        
        sys.path.insert(0, str(tmp_path))
        
        factory = MCPFactory()
        server = factory.from_file_with_decorators(
            str(module_file),
            decorator_name="mcp_tool"
        )
        
        tools = server.list_tools()
        assert "decorated_async" in tools
        assert "another_async" in tools
        assert "not_decorated_async" not in tools
        
        sys.path.remove(str(tmp_path))


class TestAsyncFunctionWrapping:
    """Test that async functions are properly wrapped."""
    
    def test_async_function_remains_async(self):
        """Test that async functions remain async after wrapping."""
        async def async_func(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2
        
        factory = MCPFactory()
        server = factory.from_functions({"async_func": async_func})
        
        tool = server._tools["async_func"]
        
        # The wrapped function should still be async
        assert asyncio.iscoroutinefunction(tool)
    
    def test_sync_function_remains_sync(self):
        """Test that sync functions remain sync after wrapping."""
        def sync_func(x: int) -> int:
            return x * 2
        
        factory = MCPFactory()
        server = factory.from_functions({"sync_func": sync_func})
        
        tool = server._tools["sync_func"]
        
        # The wrapped function should not be async
        assert not asyncio.iscoroutinefunction(tool)
    
    def test_mixed_async_sync_functions(self):
        """Test mixing async and sync functions."""
        async def async_func(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2
        
        def sync_func(x: int) -> int:
            return x * 3
        
        factory = MCPFactory()
        server = factory.from_functions({
            "async_func": async_func,
            "sync_func": sync_func
        })
        
        async_tool = server._tools["async_func"]
        sync_tool = server._tools["sync_func"]
        
        assert asyncio.iscoroutinefunction(async_tool)
        assert not asyncio.iscoroutinefunction(sync_tool)


class TestAsyncExecution:
    """Test executing async functions."""
    
    @pytest.mark.asyncio
    async def test_execute_async_function(self):
        """Test executing an async function through the factory."""
        async def async_add(a: int, b: int) -> int:
            await asyncio.sleep(0.01)
            return a + b
        
        factory = MCPFactory()
        server = factory.from_functions({"add": async_add})
        
        tool = server._tools["add"]
        
        # Execute the async function
        result = await tool(a=5, b=3)
        assert result == 8
    
    @pytest.mark.asyncio
    async def test_execute_multiple_async_parallel(self):
        """Test executing multiple async functions in parallel."""
        async def slow_add(a: int, b: int) -> int:
            await asyncio.sleep(0.1)
            return a + b
        
        factory = MCPFactory()
        server = factory.from_functions({"slow_add": slow_add})
        
        tool = server._tools["slow_add"]
        
        # Execute multiple calls in parallel
        start = asyncio.get_event_loop().time()
        results = await asyncio.gather(
            tool(a=1, b=2),
            tool(a=3, b=4),
            tool(a=5, b=6)
        )
        end = asyncio.get_event_loop().time()
        
        assert results == [3, 7, 11]
        # Should take ~0.1s (parallel) not ~0.3s (sequential)
        assert end - start < 0.2
    
    @pytest.mark.asyncio
    async def test_async_with_exception(self):
        """Test async function that raises an exception."""
        async def async_error(x: int) -> int:
            await asyncio.sleep(0.01)
            raise ValueError("Test error")
        
        factory = MCPFactory()
        server = factory.from_functions({"error": async_error})
        
        tool = server._tools["error"]
        
        # The wrapper catches exceptions and returns error dict
        result = await tool(x=5)
        assert "error" in result
        assert "Test error" in str(result["error"])
    
    def test_execute_sync_function(self):
        """Test that sync functions still work normally."""
        def sync_add(a: int, b: int) -> int:
            return a + b
        
        factory = MCPFactory()
        server = factory.from_functions({"add": sync_add})
        
        tool = server._tools["add"]
        
        # Execute the sync function (no await needed)
        result = tool(a=5, b=3)
        assert result == 8


class TestAsyncClassMethods:
    """Test async methods in classes."""
    
    @pytest.mark.asyncio
    async def test_async_class_method_execution(self):
        """Test executing async methods from a class."""
        class AsyncCounter:
            def __init__(self):
                self.count = 0
            
            async def increment(self) -> int:
                await asyncio.sleep(0.01)
                self.count += 1
                return self.count
            
            async def get_count(self) -> int:
                await asyncio.sleep(0.01)
                return self.count
            
            def sync_reset(self) -> None:
                self.count = 0
                return {"reset": True}
        
        factory = MCPFactory()
        server = factory.from_class(AsyncCounter)
        
        # Check that methods are properly wrapped
        inc_tool = server._tools["increment"]
        get_tool = server._tools["get_count"]
        reset_tool = server._tools["sync_reset"]
        
        assert asyncio.iscoroutinefunction(inc_tool)
        assert asyncio.iscoroutinefunction(get_tool)
        assert not asyncio.iscoroutinefunction(reset_tool)
        
        # Test execution
        result1 = await inc_tool()
        assert result1 == 1
        
        result2 = await inc_tool()
        assert result2 == 2
        
        count = await get_tool()
        assert count == 2
        
        # Sync method should work without await
        reset_result = reset_tool()
        assert reset_result == {"reset": True}


class TestAsyncDecorator:
    """Test mcp_tool decorator with async functions."""
    
    def test_decorator_preserves_async(self):
        """Test that decorator preserves async nature."""
        @mcp_tool
        async def decorated_async(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2
        
        # The decorated function should still be async
        assert asyncio.iscoroutinefunction(decorated_async)
        
        # Decorator attributes should be set
        assert hasattr(decorated_async, "_mcp_tool")
        assert decorated_async._mcp_tool is True
    
    def test_decorator_with_params_async(self):
        """Test decorator with parameters on async function."""
        @mcp_tool(name="custom", description="Custom async")
        async def decorated_async(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2
        
        assert asyncio.iscoroutinefunction(decorated_async)
        assert decorated_async._mcp_name == "custom"
        assert decorated_async._mcp_description == "Custom async"
    
    @pytest.mark.asyncio
    async def test_decorated_async_execution(self):
        """Test executing decorated async function."""
        @mcp_tool
        async def decorated_add(a: int, b: int) -> int:
            await asyncio.sleep(0.01)
            return a + b
        
        # Should be executable
        result = await decorated_add(5, 3)
        assert result == 8


class TestAsyncReturnTypes:
    """Test different return types from async functions."""
    
    @pytest.mark.asyncio
    async def test_async_returning_none(self):
        """Test async function returning None."""
        async def async_none(x: int) -> None:
            await asyncio.sleep(0.01)
            # Side effect only
            return None
        
        factory = MCPFactory()
        server = factory.from_functions({"none": async_none})
        
        tool = server._tools["none"]
        result = await tool(x=5)
        
        # Should return success indicator
        assert result == {"success": True}
    
    @pytest.mark.asyncio
    async def test_async_returning_dict(self):
        """Test async function returning dict."""
        async def async_dict(x: int) -> dict:
            await asyncio.sleep(0.01)
            return {"value": x, "squared": x * x}
        
        factory = MCPFactory()
        server = factory.from_functions({"dict": async_dict})
        
        tool = server._tools["dict"]
        result = await tool(x=5)
        
        assert result == {"value": 5, "squared": 25}
    
    @pytest.mark.asyncio
    async def test_async_returning_list(self):
        """Test async function returning list."""
        async def async_list(count: int) -> list:
            await asyncio.sleep(0.01)
            return [i * 2 for i in range(count)]
        
        factory = MCPFactory()
        server = factory.from_functions({"list": async_list})
        
        tool = server._tools["list"]
        result = await tool(count=3)
        
        assert result == [0, 2, 4]


class TestAsyncIntegration:
    """Integration tests for async support."""
    
    @pytest.mark.asyncio
    async def test_real_world_async_scenario(self):
        """Test a real-world async scenario."""
        # Simulate a data processing pipeline
        class DataPipeline:
            async def fetch_data(self, source: str) -> dict:
                """Fetch data from source."""
                await asyncio.sleep(0.05)  # Simulate network delay
                return {"source": source, "data": [1, 2, 3, 4, 5]}
            
            async def process_data(self, data: dict) -> dict:
                """Process the fetched data."""
                await asyncio.sleep(0.03)  # Simulate processing
                values = data.get("data", [])
                return {
                    "source": data.get("source"),
                    "processed": [v * 2 for v in values],
                    "sum": sum(values)
                }
            
            async def save_results(self, results: dict) -> dict:
                """Save the results."""
                await asyncio.sleep(0.02)  # Simulate save operation
                return {
                    "saved": True,
                    "item_count": len(results.get("processed", []))
                }
        
        factory = MCPFactory()
        server = factory.from_class(DataPipeline)
        
        # Get the tools
        fetch = server._tools["fetch_data"]
        process = server._tools["process_data"]
        save = server._tools["save_results"]
        
        # Run the pipeline
        data = await fetch(source="test_source")
        assert data["source"] == "test_source"
        
        processed = await process(data=data)
        assert processed["processed"] == [2, 4, 6, 8, 10]
        assert processed["sum"] == 15
        
        saved = await save(results=processed)
        assert saved["saved"] is True
        assert saved["item_count"] == 5
    
    @pytest.mark.asyncio
    async def test_concurrent_async_operations(self):
        """Test running multiple async operations concurrently."""
        async def fetch_user(user_id: int) -> dict:
            await asyncio.sleep(0.1)  # Simulate API call
            return {"id": user_id, "name": f"User{user_id}"}
        
        factory = MCPFactory()
        server = factory.from_functions({"fetch_user": fetch_user})
        
        tool = server._tools["fetch_user"]
        
        # Fetch multiple users concurrently
        start = asyncio.get_event_loop().time()
        users = await asyncio.gather(
            tool(user_id=1),
            tool(user_id=2),
            tool(user_id=3),
            tool(user_id=4),
            tool(user_id=5)
        )
        end = asyncio.get_event_loop().time()
        
        # Should have all users
        assert len(users) == 5
        assert users[0]["name"] == "User1"
        assert users[4]["name"] == "User5"
        
        # Should be concurrent (take ~0.1s not ~0.5s)
        assert end - start < 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])