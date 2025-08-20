"""
Tests for QuickMCP standalone decorators
"""

import pytest
from quickmcp.decorators import (
    tool,
    resource,
    prompt,
    get_pending_tools,
    get_pending_resources,
    get_pending_prompts,
    clear_pending,
    auto_discover_mcp_components
)


class TestStandaloneDecorators:
    """Test standalone decorator functionality."""
    
    def test_standalone_tool_decorator(self):
        """Test using tool decorator without server."""
        # Clear any previous pending items
        clear_pending()
        
        @tool()
        def my_tool(x: int) -> int:
            """Test tool."""
            return x * 2
        
        # Function should still work
        assert my_tool(5) == 10
        
        # Should be marked
        assert hasattr(my_tool, "_mcp_tool")
        assert my_tool._mcp_tool is True
        
        # Should be in pending list
        pending = get_pending_tools()
        assert len(pending) == 1
        # The function might be wrapped, so check by name
        assert pending[0]["name"] == "my_tool"
    
    def test_standalone_tool_with_options(self):
        """Test standalone tool with custom options."""
        clear_pending()
        
        @tool(name="custom_tool", description="Custom description")
        def another_tool(x: int) -> int:
            return x + 1
        
        pending = get_pending_tools()
        assert len(pending) == 1
        assert pending[0]["name"] == "custom_tool"
        assert pending[0]["description"] == "Custom description"
    
    def test_standalone_resource_decorator(self):
        """Test using resource decorator without server."""
        clear_pending()
        
        @resource("test://{id}")
        def my_resource(id: str) -> str:
            """Test resource."""
            return f"Data {id}"
        
        # Function should still work
        assert my_resource("123") == "Data 123"
        
        # Should be marked
        assert hasattr(my_resource, "_mcp_resource")
        assert my_resource._mcp_resource is True
        
        # Should be in pending list
        pending = get_pending_resources()
        assert len(pending) == 1
        # The function might be wrapped, so check by uri_template
        assert pending[0]["uri_template"] == "test://{id}"
    
    def test_standalone_resource_with_options(self):
        """Test standalone resource with custom options."""
        clear_pending()
        
        @resource(
            "data://{key}",
            name="data_fetcher",
            description="Fetch data",
            mime_type="application/json"
        )
        def fetch_data(key: str) -> str:
            return f"{key}"
        
        pending = get_pending_resources()
        assert len(pending) == 1
        assert pending[0]["name"] == "data_fetcher"
        assert pending[0]["description"] == "Fetch data"
        assert pending[0]["mime_type"] == "application/json"
    
    def test_standalone_prompt_decorator(self):
        """Test using prompt decorator without server."""
        clear_pending()
        
        @prompt()
        def my_prompt(topic: str) -> str:
            """Test prompt."""
            return f"Tell me about {topic}"
        
        # Function should still work
        assert my_prompt("Python") == "Tell me about Python"
        
        # Should be marked
        assert hasattr(my_prompt, "_mcp_prompt")
        assert my_prompt._mcp_prompt is True
        
        # Should be in pending list
        pending = get_pending_prompts()
        assert len(pending) == 1
        # The function might be wrapped, so check by name
        assert pending[0]["name"] == "my_prompt"
    
    def test_standalone_prompt_with_options(self):
        """Test standalone prompt with custom options."""
        clear_pending()
        
        arguments = [{"name": "topic", "type": "string"}]
        
        @prompt(
            name="analysis",
            description="Analysis prompt",
            arguments=arguments
        )
        def analyze(topic: str) -> str:
            return f"Analyze {topic}"
        
        pending = get_pending_prompts()
        assert len(pending) == 1
        assert pending[0]["name"] == "analysis"
        assert pending[0]["description"] == "Analysis prompt"
        assert pending[0]["arguments"] == arguments


class TestPendingManagement:
    """Test management of pending decorations."""
    
    def test_clear_pending(self):
        """Test clearing pending items."""
        clear_pending()
        
        # Add some items
        @tool()
        def t1():
            pass
        
        @resource("test://{id}")
        def r1(id):
            pass
        
        @prompt()
        def p1():
            pass
        
        # Verify they're pending
        assert len(get_pending_tools()) == 1
        assert len(get_pending_resources()) == 1
        assert len(get_pending_prompts()) == 1
        
        # Clear
        clear_pending()
        
        # Verify cleared
        assert len(get_pending_tools()) == 0
        assert len(get_pending_resources()) == 0
        assert len(get_pending_prompts()) == 0
    
    def test_multiple_pending_items(self):
        """Test multiple pending items of same type."""
        clear_pending()
        
        @tool()
        def tool1():
            pass
        
        @tool(name="tool_two")
        def tool2():
            pass
        
        @tool()
        def tool3():
            pass
        
        pending = get_pending_tools()
        assert len(pending) == 3
        
        names = [p["name"] for p in pending]
        assert "tool1" in names
        assert "tool_two" in names
        assert "tool3" in names


class TestAutoDiscovery:
    """Test auto-discovery of MCP components."""
    
    def test_auto_discover_in_module(self):
        """Test auto-discovering MCP components in a module."""
        # Create a test module
        import types
        test_module = types.ModuleType("test_module")
        
        # Add decorated functions to module
        @tool()
        def module_tool():
            return "tool"
        
        @resource("test://{id}")
        def module_resource(id):
            return f"resource {id}"
        
        @prompt()
        def module_prompt():
            return "prompt"
        
        # Regular function (not decorated)
        def regular_function():
            return "regular"
        
        # Add to module
        test_module.module_tool = module_tool
        test_module.module_resource = module_resource
        test_module.module_prompt = module_prompt
        test_module.regular_function = regular_function
        
        # Discover
        discovered = auto_discover_mcp_components(test_module)
        
        assert len(discovered["tools"]) == 1
        assert module_tool in discovered["tools"]
        
        assert len(discovered["resources"]) == 1
        assert module_resource in discovered["resources"]
        
        assert len(discovered["prompts"]) == 1
        assert module_prompt in discovered["prompts"]
        
        # Regular function should not be discovered
        assert regular_function not in discovered["tools"]
        assert regular_function not in discovered["resources"]
        assert regular_function not in discovered["prompts"]
    
    def test_auto_discover_empty_module(self):
        """Test auto-discovery on module with no MCP components."""
        import types
        empty_module = types.ModuleType("empty_module")
        
        def regular_func():
            pass
        
        empty_module.regular_func = regular_func
        
        discovered = auto_discover_mcp_components(empty_module)
        
        assert len(discovered["tools"]) == 0
        assert len(discovered["resources"]) == 0
        assert len(discovered["prompts"]) == 0