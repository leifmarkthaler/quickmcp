"""
Tests for the quickmcp.quick module - the simplified API.
"""

import pytest
import tempfile
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from makemcp.quick import (
    server,
    from_file,
    from_object,
    run,
    tool
)
from makemcp import MakeMCPServer


class TestQuickServer:
    """Test the server() function."""
    
    def test_server_creation_default(self):
        """Test creating a server with default name."""
        s = server()
        assert isinstance(s, MakeMCPServer)
        assert s.name == "makemcp-server"
    
    def test_server_creation_custom_name(self):
        """Test creating a server with custom name."""
        s = server("my-test-server")
        assert isinstance(s, MakeMCPServer)
        assert s.name == "my-test-server"
    
    def test_server_can_add_tools(self):
        """Test that we can add tools to the server."""
        s = server("test")
        
        @s.tool()
        def test_func(x: int) -> int:
            return x * 2
        
        assert "test_func" in s.list_tools()


class TestFromFile:
    """Test the from_file() function."""
    
    def test_from_file_basic(self, tmp_path):
        """Test creating server from a Python file."""
        # Create a test Python file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def add(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b

def multiply(x: float, y: float) -> float:
    '''Multiply two numbers.'''
    return x * y

def _private_func():
    '''This should not be included by default.'''
    return "private"
""")
        
        # Create server from file
        s = from_file(str(test_file))
        
        assert isinstance(s, MakeMCPServer)
        assert "test-module-mcp" in s.name
        
        tools = s.list_tools()
        assert "add" in tools
        assert "multiply" in tools
        assert "_private_func" not in tools
    
    def test_from_file_custom_name(self, tmp_path):
        """Test creating server with custom name."""
        test_file = tmp_path / "utils.py"
        test_file.write_text("def hello(): return 'hi'")
        
        s = from_file(str(test_file), name="custom-name")
        assert s.name == "custom-name"
    
    def test_from_file_include_private(self, tmp_path):
        """Test including private functions."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def public(): return "public"
def _private(): return "private"
""")
        
        s = from_file(str(test_file), include_private=True)
        tools = s.list_tools()
        assert "public" in tools
        assert "_private" in tools
    
    def test_from_file_with_async(self, tmp_path):
        """Test that async functions are preserved."""
        test_file = tmp_path / "async_test.py"
        test_file.write_text("""
import asyncio

async def async_func(x: int) -> int:
    await asyncio.sleep(0.01)
    return x * 2

def sync_func(x: int) -> int:
    return x + 1
""")
        
        s = from_file(str(test_file))
        
        # Check both functions are registered
        assert "async_func" in s.list_tools()
        assert "sync_func" in s.list_tools()
        
        # Check async function is still async
        async_tool = s._tools.get("async_func")
        sync_tool = s._tools.get("sync_func")
        
        assert asyncio.iscoroutinefunction(async_tool)
        assert not asyncio.iscoroutinefunction(sync_tool)


class TestFromObject:
    """Test the from_object() function."""
    
    def test_from_dict(self):
        """Test creating server from dictionary of functions."""
        functions = {
            "add": lambda a, b: a + b,
            "multiply": lambda x, y: x * y,
            "greet": lambda name: f"Hello, {name}!"
        }
        
        s = from_object(functions)
        
        assert isinstance(s, MakeMCPServer)
        tools = s.list_tools()
        assert "add" in tools
        assert "multiply" in tools
        assert "greet" in tools
    
    def test_from_class(self):
        """Test creating server from a class."""
        class TestClass:
            def __init__(self):
                self.counter = 0
            
            def increment(self) -> int:
                self.counter += 1
                return self.counter
            
            def reset(self) -> None:
                self.counter = 0
            
            def _private(self):
                return "private"
        
        s = from_object(TestClass)
        
        tools = s.list_tools()
        assert "increment" in tools
        assert "reset" in tools
        assert "_private" not in tools  # Private methods excluded by default
    
    def test_from_module(self):
        """Test creating server from a module."""
        import math
        
        s = from_object(math, name="math-server")
        
        assert s.name == "math-server"
        tools = s.list_tools()
        
        # Should have various math functions
        assert len(tools) > 0
        # Common math functions should be there
        assert any("sin" in t for t in tools)
    
    def test_from_instance(self):
        """Test creating server from class instance."""
        class Counter:
            def __init__(self, start=0):
                self.value = start
            
            def get(self) -> int:
                return self.value
            
            def add(self, n: int) -> int:
                self.value += n
                return self.value
        
        counter = Counter(10)
        s = from_object(counter)
        
        tools = s.list_tools()
        assert "get" in tools
        assert "add" in tools


class TestToolDecorator:
    """Test the @tool decorator."""
    
    def test_tool_basic(self):
        """Test basic tool decorator."""
        @tool
        def test_func(x: int) -> int:
            """Test function."""
            return x * 2
        
        # Should have mcp_tool attributes
        assert hasattr(test_func, "_mcp_tool")
        assert test_func._mcp_tool is True
        assert test_func._mcp_name == "test_func"
        assert test_func._mcp_description == "Test function."
        
        # Should still be callable
        assert test_func(5) == 10
    
    def test_tool_with_params(self):
        """Test tool decorator with parameters."""
        @tool(name="custom", description="Custom description")
        def test_func():
            return "test"
        
        assert test_func._mcp_name == "custom"
        assert test_func._mcp_description == "Custom description"
    
    def test_tool_async(self):
        """Test tool decorator on async function."""
        @tool
        async def async_func(x: int) -> int:
            """Async function."""
            await asyncio.sleep(0.01)
            return x * 2
        
        assert hasattr(async_func, "_mcp_tool")
        assert asyncio.iscoroutinefunction(async_func)
    
    def test_tool_preserves_function(self):
        """Test that decorator preserves the original function."""
        def original(x: int, y: str = "default") -> str:
            """Original docstring."""
            return f"{x}: {y}"
        
        decorated = tool(original)
        
        # Should preserve function properties
        assert decorated.__name__ == original.__name__
        assert decorated.__doc__ == original.__doc__
        assert decorated(10) == "10: default"
        assert decorated(10, "custom") == "10: custom"


class TestRun:
    """Test the run() function."""
    
    @patch('makemcp.quick.server')
    def test_run_no_args(self, mock_server):
        """Test run() with no arguments."""
        mock_instance = Mock()
        mock_server.return_value = mock_instance
        
        # Mock getting the caller's module
        with patch('inspect.currentframe') as mock_frame:
            mock_frame.return_value = None
            
            with patch.object(mock_instance, 'run'):
                run()
                mock_instance.run.assert_called_once_with(
                    transport='stdio',
                    host='localhost', 
                    port=8000
                )
    
    @patch('makemcp.quick.from_file')
    def test_run_with_file(self, mock_from_file):
        """Test run() with file path."""
        mock_server = Mock()
        mock_from_file.return_value = mock_server
        
        with patch.object(mock_server, 'run'):
            run("test.py", name="test-server")
            
            mock_from_file.assert_called_once_with("test.py", name="test-server")
            mock_server.run.assert_called_once()
    
    @patch('makemcp.quick.from_object')
    def test_run_with_dict(self, mock_from_object):
        """Test run() with dictionary."""
        mock_server = Mock()
        mock_from_object.return_value = mock_server
        
        functions = {"test": lambda: "test"}
        
        with patch.object(mock_server, 'run'):
            run(functions, name="dict-server")
            
            mock_from_object.assert_called_once_with(functions, name="dict-server")
            mock_server.run.assert_called_once()
    
    @patch('makemcp.quick.from_object')
    def test_run_with_function(self, mock_from_object):
        """Test run() with single function."""
        mock_server = Mock()
        mock_from_object.return_value = mock_server
        
        def test_func():
            return "test"
        
        with patch.object(mock_server, 'run'):
            run(test_func)
            
            # Should wrap function in dict
            call_args = mock_from_object.call_args[0][0]
            assert isinstance(call_args, dict)
            assert "test_func" in call_args
    
    @patch('makemcp.quick.from_object')
    def test_run_with_transport_options(self, mock_from_object):
        """Test run() with transport options."""
        mock_server = Mock()
        mock_from_object.return_value = mock_server
        
        with patch.object(mock_server, 'run'):
            run({}, transport='sse', host='0.0.0.0', port=9000)
            
            mock_server.run.assert_called_once_with(
                transport='sse',
                host='0.0.0.0',
                port=9000
            )


class TestIntegration:
    """Integration tests for the quick module."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow from file to server."""
        # Create a test module
        test_file = tmp_path / "workflow_test.py"
        test_file.write_text("""
from makemcp.factory import mcp_tool

def regular_func(x: int) -> int:
    return x * 2

@mcp_tool
def decorated_func(y: int) -> int:
    return y + 10

async def async_func(z: int) -> int:
    import asyncio
    await asyncio.sleep(0.01)
    return z * 3
""")
        
        # Create server from file
        s = from_file(str(test_file))
        
        # Check all functions are there
        tools = s.list_tools()
        assert "regular_func" in tools
        assert "decorated_func" in tools
        assert "async_func" in tools
        
        # Test execution
        regular = s._tools["regular_func"]
        assert regular(x=5) == 10
        
        decorated = s._tools["decorated_func"]
        assert decorated(y=5) == 15
        
        # Test async execution
        async_tool = s._tools["async_func"]
        assert asyncio.iscoroutinefunction(async_tool)
        result = asyncio.run(async_tool(z=5))
        assert result == 15
    
    def test_mixed_sync_async(self, tmp_path):
        """Test that sync and async functions work together."""
        test_file = tmp_path / "mixed.py"
        test_file.write_text("""
import asyncio

async def fetch_data(url: str) -> str:
    await asyncio.sleep(0.01)
    return f"Data from {url}"

def process_data(data: str) -> str:
    return data.upper()

async def fetch_and_process(url: str) -> str:
    data = await fetch_data(url)
    return process_data(data)
""")
        
        s = from_file(str(test_file))
        
        # All functions should be registered
        tools = s.list_tools()
        assert len(tools) == 3
        
        # Check async nature is preserved
        fetch = s._tools["fetch_data"]
        process = s._tools["process_data"]
        fetch_process = s._tools["fetch_and_process"]
        
        assert asyncio.iscoroutinefunction(fetch)
        assert not asyncio.iscoroutinefunction(process)
        assert asyncio.iscoroutinefunction(fetch_process)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])