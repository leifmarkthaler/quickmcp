"""
Tests for QuickMCP async functionality
"""

import pytest
import asyncio
from quickmcp import QuickMCPServer


class TestAsyncTools:
    """Test async tool functionality."""
    
    @pytest.mark.asyncio
    async def test_register_async_tool(self):
        """Test registering an async tool."""
        server = QuickMCPServer("async-test-server")
        
        @server.tool()
        async def async_tool(x: int) -> int:
            """Async tool."""
            await asyncio.sleep(0.01)
            return x * 2
        
        tools = server.list_tools()
        assert "async_tool" in tools
        
        # Test direct execution
        result = await async_tool(5)
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_multiple_async_tools(self):
        """Test multiple async tools."""
        server = QuickMCPServer("async-test-server")
        
        @server.tool()
        async def fetch_data(id: str) -> dict:
            """Fetch data asynchronously."""
            await asyncio.sleep(0.01)
            return {"id": id, "data": "test"}
        
        @server.tool()
        async def process_data(data: dict) -> dict:
            """Process data asynchronously."""
            await asyncio.sleep(0.01)
            return {"processed": True, **data}
        
        tools = server.list_tools()
        assert len(tools) == 2
        assert "fetch_data" in tools
        assert "process_data" in tools
        
        # Test execution chain
        fetched = await fetch_data("123")
        processed = await process_data(fetched)
        
        assert processed["processed"] is True
        assert processed["id"] == "123"
        assert processed["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_async_tool_with_error(self):
        """Test async tool error handling."""
        server = QuickMCPServer("async-test-server")
        
        @server.tool()
        async def failing_async_tool(value: int) -> int:
            """Async tool that can fail."""
            await asyncio.sleep(0.01)
            if value < 0:
                raise ValueError("Negative value not allowed")
            return value * 2
        
        # Test normal execution
        result = await failing_async_tool(5)
        assert result == 10
        
        # Test error case
        with pytest.raises(ValueError, match="Negative value not allowed"):
            await failing_async_tool(-1)
    
    @pytest.mark.asyncio
    async def test_concurrent_async_tools(self):
        """Test running async tools concurrently."""
        server = QuickMCPServer("async-test-server")
        
        call_count = 0
        
        @server.tool()
        async def slow_tool(delay: float) -> float:
            """Tool with configurable delay."""
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(delay)
            return delay * 10
        
        # Run multiple tools concurrently
        tasks = [
            slow_tool(0.01),
            slow_tool(0.02),
            slow_tool(0.03)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert results == [0.1, 0.2, 0.3]
        assert call_count == 3


class TestAsyncResources:
    """Test async resource functionality."""
    
    @pytest.mark.asyncio
    async def test_register_async_resource(self):
        """Test registering an async resource."""
        server = QuickMCPServer("async-test-server")
        
        @server.resource("async://{id}")
        async def async_resource(id: str) -> str:
            """Async resource."""
            await asyncio.sleep(0.01)
            return f"Async data for {id}"
        
        resources = server.list_resources()
        assert "async://{id}" in resources
        
        # Test direct execution
        result = await async_resource("test")
        assert result == "Async data for test"
    
    @pytest.mark.asyncio
    async def test_async_resource_with_processing(self):
        """Test async resource with data processing."""
        server = QuickMCPServer("async-test-server")
        
        # Simulate async data source
        async def fetch_from_database(key: str) -> dict:
            """Simulate database fetch."""
            await asyncio.sleep(0.01)
            return {"key": key, "value": f"data_{key}"}
        
        @server.resource("db://{key}")
        async def database_resource(key: str) -> str:
            """Fetch from database."""
            data = await fetch_from_database(key)
            import json
            return json.dumps(data)
        
        # Test execution
        result = await database_resource("item1")
        import json
        data = json.loads(result)
        
        assert data["key"] == "item1"
        assert data["value"] == "data_item1"


class TestAsyncPrompts:
    """Test async prompt functionality."""
    
    @pytest.mark.asyncio
    async def test_register_async_prompt(self):
        """Test registering an async prompt."""
        server = QuickMCPServer("async-test-server")
        
        @server.prompt()
        async def async_prompt(topic: str) -> str:
            """Async prompt generation."""
            await asyncio.sleep(0.01)
            return f"Generated prompt for {topic}"
        
        prompts = server.list_prompts()
        assert "async_prompt" in prompts
        
        # Test direct execution
        result = await async_prompt("testing")
        assert result == "Generated prompt for testing"
    
    @pytest.mark.asyncio
    async def test_async_prompt_with_external_data(self):
        """Test async prompt that fetches external data."""
        server = QuickMCPServer("async-test-server")
        
        async def fetch_context(topic: str) -> str:
            """Simulate fetching context."""
            await asyncio.sleep(0.01)
            return f"Context about {topic}"
        
        @server.prompt()
        async def contextual_prompt(topic: str) -> str:
            """Generate prompt with context."""
            context = await fetch_context(topic)
            return f"Using context: {context}\n\nExplain {topic}"
        
        result = await contextual_prompt("Python")
        assert "Context about Python" in result
        assert "Explain Python" in result


class TestMixedSyncAsync:
    """Test mixing sync and async operations."""
    
    @pytest.mark.asyncio
    async def test_mixed_tools(self):
        """Test server with both sync and async tools."""
        server = QuickMCPServer("mixed-server")
        
        @server.tool()
        def sync_tool(x: int) -> int:
            """Sync tool."""
            return x * 2
        
        @server.tool()
        async def async_tool(x: int) -> int:
            """Async tool."""
            await asyncio.sleep(0.01)
            return x * 3
        
        tools = server.list_tools()
        assert len(tools) == 2
        assert "sync_tool" in tools
        assert "async_tool" in tools
        
        # Test execution
        sync_result = sync_tool(5)
        async_result = await async_tool(5)
        
        assert sync_result == 10
        assert async_result == 15
    
    @pytest.mark.asyncio
    async def test_mixed_all_components(self):
        """Test server with mixed sync/async tools, resources, and prompts."""
        server = QuickMCPServer("mixed-server")
        
        # Sync tool
        @server.tool()
        def sync_calculate(x: int, y: int) -> int:
            return x + y
        
        # Async tool
        @server.tool()
        async def async_process(data: str) -> dict:
            await asyncio.sleep(0.01)
            return {"processed": data}
        
        # Sync resource
        @server.resource("sync://{id}")
        def sync_resource(id: str) -> str:
            return f"Sync data {id}"
        
        # Async resource
        @server.resource("async://{id}")
        async def async_resource(id: str) -> str:
            await asyncio.sleep(0.01)
            return f"Async data {id}"
        
        # Sync prompt
        @server.prompt()
        def sync_prompt(topic: str) -> str:
            return f"Prompt for {topic}"
        
        # Async prompt
        @server.prompt()
        async def async_prompt(topic: str) -> str:
            await asyncio.sleep(0.01)
            return f"Async prompt for {topic}"
        
        # Verify all registered
        assert len(server.list_tools()) == 2
        assert len(server.list_resources()) == 2
        assert len(server.list_prompts()) == 2
        
        # Test execution of each
        assert sync_calculate(2, 3) == 5
        assert (await async_process("test"))["processed"] == "test"
        assert sync_resource("1") == "Sync data 1"
        assert await async_resource("2") == "Async data 2"
        assert sync_prompt("AI") == "Prompt for AI"
        assert await async_prompt("ML") == "Async prompt for ML"