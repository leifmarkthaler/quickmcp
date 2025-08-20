"""
Pytest configuration and shared fixtures for QuickMCP tests
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path for development testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickmcp import QuickMCPServer


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def simple_server():
    """Create a simple test server."""
    server = QuickMCPServer(
        name="test-server",
        version="1.0.0",
        description="Test server for unit tests"
    )
    return server


@pytest.fixture
def server_with_tools():
    """Create a server with some test tools."""
    server = QuickMCPServer("test-server-tools")
    
    @server.tool()
    def add(a: float, b: float) -> float:
        """Add two numbers."""
        return a + b
    
    @server.tool()
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
    
    @server.tool(name="custom_name", description="Custom tool")
    def custom_tool(value: str) -> str:
        """Custom named tool."""
        return f"processed: {value}"
    
    return server


@pytest.fixture
def server_with_resources():
    """Create a server with test resources."""
    server = QuickMCPServer("test-server-resources")
    
    test_data = {"key1": "value1", "key2": "value2"}
    
    @server.resource("test://{key}")
    def get_test_data(key: str) -> str:
        """Get test data by key."""
        return test_data.get(key, "not found")
    
    @server.resource("info://server")
    def get_server_info() -> str:
        """Get server information."""
        return "Test server info"
    
    return server


@pytest.fixture
def server_with_prompts():
    """Create a server with test prompts."""
    server = QuickMCPServer("test-server-prompts")
    
    @server.prompt()
    def test_prompt(topic: str) -> str:
        """Generate a test prompt."""
        return f"Test prompt for {topic}"
    
    @server.prompt(name="custom_prompt")
    def another_prompt(value: str, level: str = "basic") -> str:
        """Another test prompt."""
        return f"Prompt: {value} at {level} level"
    
    return server


@pytest.fixture
async def async_server():
    """Create a server with async operations."""
    server = QuickMCPServer("test-async-server")
    
    @server.tool()
    async def async_add(a: float, b: float) -> float:
        """Async addition."""
        await asyncio.sleep(0.01)  # Simulate async work
        return a + b
    
    @server.tool()
    async def async_process(data: str) -> dict:
        """Async data processing."""
        await asyncio.sleep(0.01)
        return {"processed": data, "async": True}
    
    @server.resource("async://{id}")
    async def async_resource(id: str) -> str:
        """Async resource fetcher."""
        await asyncio.sleep(0.01)
        return f"Async resource {id}"
    
    return server


@pytest.fixture
def mock_mcp_server(monkeypatch):
    """Mock the underlying MCP server for testing."""
    class MockMCPServer:
        def __init__(self, name):
            self.name = name
            self.tools = {}
            self.resources = {}
            self.prompts = {}
            
        def tool(self, **kwargs):
            def decorator(func):
                self.tools[kwargs.get('name', func.__name__)] = func
                return func
            return decorator
            
        def resource(self, **kwargs):
            def decorator(func):
                self.resources[kwargs.get('uri_template')] = func
                return func
            return decorator
            
        def prompt(self, **kwargs):
            def decorator(func):
                self.prompts[kwargs.get('name', func.__name__)] = func
                return func
            return decorator
    
    # Patch the Server import in quickmcp.server
    monkeypatch.setattr("quickmcp.server.Server", MockMCPServer)
    
    return MockMCPServer