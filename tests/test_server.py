"""
Tests for MakeMCPServer basic functionality
"""

import pytest
from makemcp import MakeMCPServer


class TestServerCreation:
    """Test server creation and configuration."""
    
    def test_create_basic_server(self):
        """Test creating a basic server."""
        server = MakeMCPServer("test-server")
        
        assert server.name == "test-server"
        assert server.version == "1.0.0"
        assert server.description == "test-server MCP Server"
        assert len(server._tools) == 0
        assert len(server._resources) == 0
        assert len(server._prompts) == 0
    
    def test_create_server_with_options(self):
        """Test creating a server with custom options."""
        server = MakeMCPServer(
            name="custom-server",
            version="2.0.0",
            description="Custom test server",
            log_level="DEBUG"
        )
        
        assert server.name == "custom-server"
        assert server.version == "2.0.0"
        assert server.description == "Custom test server"
    
    def test_server_info(self, simple_server):
        """Test getting server information."""
        info = simple_server.get_info()
        
        assert info["name"] == "test-server"
        assert info["version"] == "1.0.0"
        assert info["description"] == "Test server for unit tests"
        assert info["tools"] == []
        assert info["resources"] == []
        assert info["prompts"] == []
    
    def test_server_repr(self, simple_server):
        """Test server string representation."""
        repr_str = repr(simple_server)
        
        assert "MakeMCPServer" in repr_str
        assert "test-server" in repr_str
        assert "1.0.0" in repr_str


class TestServerComponents:
    """Test server component registration."""
    
    def test_list_tools(self, server_with_tools):
        """Test listing registered tools."""
        tools = server_with_tools.list_tools()
        
        assert len(tools) == 3
        assert "add" in tools
        assert "multiply" in tools
        assert "custom_name" in tools
    
    def test_list_resources(self, server_with_resources):
        """Test listing registered resources."""
        resources = server_with_resources.list_resources()
        
        assert len(resources) == 2
        assert "test://{key}" in resources
        assert "info://server" in resources
    
    def test_list_prompts(self, server_with_prompts):
        """Test listing registered prompts."""
        prompts = server_with_prompts.list_prompts()
        
        assert len(prompts) == 2
        assert "test_prompt" in prompts
        assert "custom_prompt" in prompts
    
    def test_server_info_with_components(self, server_with_tools):
        """Test server info includes registered components."""
        info = server_with_tools.get_info()
        
        assert len(info["tools"]) == 3
        assert "add" in info["tools"]
        assert "multiply" in info["tools"]
        assert "custom_name" in info["tools"]


class TestServerMethods:
    """Test server utility methods."""
    
    def test_add_tool_from_function(self, simple_server):
        """Test adding a tool from an existing function."""
        def my_function(x: int) -> int:
            """Test function."""
            return x * 2
        
        simple_server.add_tool_from_function(my_function)
        
        tools = simple_server.list_tools()
        assert "my_function" in tools
    
    def test_add_tool_from_function_with_name(self, simple_server):
        """Test adding a tool with custom name."""
        def my_function(x: int) -> int:
            return x * 2
        
        simple_server.add_tool_from_function(
            my_function,
            name="double",
            description="Double a number"
        )
        
        tools = simple_server.list_tools()
        assert "double" in tools
        assert "my_function" not in tools
    
    def test_export_openapi(self, server_with_tools):
        """Test exporting OpenAPI specification."""
        spec = server_with_tools.export_openapi()
        
        assert spec["openapi"] == "3.0.0"
        assert spec["info"]["title"] == "test-server-tools"
        assert spec["info"]["version"] == "1.0.0"
        assert "/tools" in spec["paths"]


class TestServerTransports:
    """Test different transport configurations."""
    
    def test_run_stdio_transport(self, simple_server, monkeypatch):
        """Test stdio transport configuration."""
        run_called = False
        
        def mock_asyncio_run(coro):
            nonlocal run_called
            run_called = True
            # Properly close the coroutine to avoid warning
            coro.close()
        
        # Mock asyncio.run to prevent actual server start
        monkeypatch.setattr("asyncio.run", mock_asyncio_run)
        
        simple_server.run_stdio()
        assert run_called
    
    def test_run_with_invalid_transport(self, simple_server):
        """Test running with invalid transport raises error."""
        with pytest.raises(ValueError, match="Unknown transport"):
            simple_server.run(transport="invalid")
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, simple_server):
        """Test the health check endpoint."""
        # Create a mock request
        class MockRequest:
            pass
        
        response = await simple_server._health_check(MockRequest())
        
        # The method returns a Starlette JSONResponse, so check the content
        assert response.body
        
        # Parse the JSON response
        import json
        data = json.loads(response.body)
        
        assert data["status"] == "healthy"
        assert data["server"] == "test-server"
        assert data["version"] == "1.0.0"
        assert data["tools"] == 0
        assert data["resources"] == 0
        assert data["prompts"] == 0