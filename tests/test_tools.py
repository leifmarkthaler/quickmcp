"""
Tests for QuickMCP tool functionality
"""

import pytest
from makemcp import MakeMCPServer


class TestToolRegistration:
    """Test tool registration and decoration."""
    
    def test_register_simple_tool(self, simple_server):
        """Test registering a simple tool."""
        @simple_server.tool()
        def test_tool(x: int) -> int:
            """Test tool."""
            return x * 2
        
        tools = simple_server.list_tools()
        assert "test_tool" in tools
        assert len(tools) == 1
    
    def test_register_tool_with_custom_name(self, simple_server):
        """Test registering a tool with custom name."""
        @simple_server.tool(name="custom_tool")
        def my_function(x: int) -> int:
            """Test function."""
            return x * 2
        
        tools = simple_server.list_tools()
        assert "custom_tool" in tools
        assert "my_function" not in tools
    
    def test_register_tool_with_description(self, simple_server):
        """Test registering a tool with custom description."""
        @simple_server.tool(description="Custom description")
        def test_tool(x: int) -> int:
            return x * 2
        
        tools = simple_server.list_tools()
        assert "test_tool" in tools
        
        # Check that the tool has the custom description
        # (would need to check internal registry for full verification)
        assert simple_server._tools["test_tool"] is not None
    
    def test_register_tool_with_schema(self, simple_server):
        """Test registering a tool with custom schema."""
        schema = {
            "type": "object",
            "properties": {
                "value": {"type": "number"}
            }
        }
        
        @simple_server.tool(schema=schema)
        def test_tool(value: float) -> float:
            """Test tool with schema."""
            return value * 2
        
        tools = simple_server.list_tools()
        assert "test_tool" in tools
    
    def test_register_multiple_tools(self, simple_server):
        """Test registering multiple tools."""
        @simple_server.tool()
        def tool1(x: int) -> int:
            return x + 1
        
        @simple_server.tool()
        def tool2(x: int) -> int:
            return x * 2
        
        @simple_server.tool(name="tool_three")
        def tool3(x: int) -> int:
            return x * 3
        
        tools = simple_server.list_tools()
        assert len(tools) == 3
        assert "tool1" in tools
        assert "tool2" in tools
        assert "tool_three" in tools
    
    def test_tool_decorator_preserves_function(self, simple_server):
        """Test that tool decorator preserves the original function."""
        @simple_server.tool()
        def test_tool(x: int) -> int:
            """Original docstring."""
            return x * 2
        
        # Function should still be callable
        result = test_tool(5)
        assert result == 10
        
        # Docstring should be preserved
        assert test_tool.__doc__ == "Original docstring."


class TestToolExecution:
    """Test tool execution (when integrated with MCP)."""
    
    def test_tool_in_registry(self, server_with_tools):
        """Test that tools are properly registered."""
        tools = server_with_tools._tools
        
        assert "add" in tools
        assert "multiply" in tools
        assert "custom_name" in tools
        
        # Test that the functions are callable
        add_func = tools["add"]
        assert callable(add_func)
        
        # Direct function call should work
        result = add_func(2, 3)
        assert result == 5
    
    def test_tool_with_type_hints(self, simple_server):
        """Test tool with various type hints."""
        from typing import List, Dict, Optional
        
        @simple_server.tool()
        def complex_tool(
            items: List[str],
            config: Dict[str, int],
            optional: Optional[str] = None
        ) -> Dict[str, any]:
            """Tool with complex types."""
            return {
                "items_count": len(items),
                "config_keys": list(config.keys()),
                "has_optional": optional is not None
            }
        
        tools = simple_server.list_tools()
        assert "complex_tool" in tools
        
        # Test direct execution
        result = complex_tool(
            items=["a", "b"],
            config={"x": 1},
            optional="test"
        )
        assert result["items_count"] == 2
        assert result["config_keys"] == ["x"]
        assert result["has_optional"] is True


class TestToolErrors:
    """Test error handling in tools."""
    
    def test_tool_with_invalid_name(self, simple_server):
        """Test that tool names are validated."""
        # This should work - the MCP server will handle validation
        @simple_server.tool(name="tool-with-dash")
        def test_tool():
            return "test"
        
        tools = simple_server.list_tools()
        assert "tool-with-dash" in tools
    
    def test_tool_raising_exception(self, simple_server):
        """Test tool that raises an exception."""
        @simple_server.tool()
        def failing_tool(x: int) -> int:
            """Tool that raises an error."""
            if x < 0:
                raise ValueError("Negative values not allowed")
            return x * 2
        
        # Direct call should raise the exception
        with pytest.raises(ValueError, match="Negative values not allowed"):
            failing_tool(-1)
        
        # Normal call should work
        result = failing_tool(5)
        assert result == 10