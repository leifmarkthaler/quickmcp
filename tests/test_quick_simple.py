"""
Simple tests for Quick module to improve coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path

from makemcp.quick import server, from_file, from_object, tool


class TestQuickAPI:
    """Test the quick API functions."""
    
    def test_server_creation(self):
        """Test creating a server with quick.server()."""
        app = server("test-server")
        assert app.name == "test-server"
        assert hasattr(app, 'tool')
        assert hasattr(app, 'resource')
        assert hasattr(app, 'prompt')
    
    def test_from_file(self):
        """Test creating server from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test Python file
            test_file = Path(tmpdir) / "test_utils.py"
            test_file.write_text("""
def add(a: int, b: int) -> int:
    return a + b

def multiply(x: float, y: float) -> float:
    return x * y
""")
            
            with patch('makemcp.quick._create_from_module') as mock_create:
                mock_server = MagicMock()
                mock_create.return_value = mock_server
                
                result = from_file(str(test_file), name="test-mcp")
                
                assert result == mock_server
                mock_create.assert_called_once()
                
                # Check the config passed
                call_args = mock_create.call_args
                assert call_args.kwargs['server_name'] == "test-mcp"
                assert call_args.kwargs['auto_run'] is False
                assert call_args.kwargs['config'].strict_type_conversion is False
    
    def test_from_file_default_name(self):
        """Test from_file with default name generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "my_utils.py"
            test_file.write_text("def test(): pass")
            
            with patch('makemcp.quick._create_from_module') as mock_create:
                mock_server = MagicMock()
                mock_create.return_value = mock_server
                
                from_file(str(test_file))
                
                call_args = mock_create.call_args
                assert call_args.kwargs['server_name'] == "my-utils-mcp"
    
    def test_from_object_with_dict(self):
        """Test creating server from a dict of functions."""
        funcs = {
            "greet": lambda name: f"Hello, {name}!",
            "add": lambda a, b: a + b
        }
        
        with patch('makemcp.factory.create_mcp_from_object') as mock_create:
            mock_server = MagicMock()
            mock_create.return_value = mock_server
            
            result = from_object(funcs, name="test-server")
            
            assert result == mock_server
            mock_create.assert_called_once_with(
                funcs,
                server_name="test-server",
                config=mock_create.call_args.kwargs['config']
            )
    
    def test_from_object_with_class(self):
        """Test creating server from a class."""
        class MyTools:
            def add(self, a: int, b: int) -> int:
                return a + b
        
        with patch('makemcp.factory.create_mcp_from_object') as mock_create:
            mock_server = MagicMock()
            mock_create.return_value = mock_server
            
            result = from_object(MyTools, name="tools-server")
            
            assert result == mock_server
            mock_create.assert_called_once()
    
    def test_tool_decorator(self):
        """Test the tool decorator."""
        @tool
        def my_func(x: int) -> int:
            return x * 2
        
        # Check that the function is marked as a tool
        assert hasattr(my_func, '_mcp_tool')
        assert my_func._mcp_tool is True
        
        # Function should still work normally
        assert my_func(5) == 10
    
    def test_tool_decorator_with_params(self):
        """Test tool decorator with parameters."""
        @tool(name="custom_name", description="Custom description")
        def my_func(x: int) -> int:
            return x * 3
        
        assert hasattr(my_func, '_mcp_tool')
        assert hasattr(my_func, '_mcp_name')
        assert hasattr(my_func, '_mcp_description')
        assert my_func._mcp_name == "custom_name"
        assert my_func._mcp_description == "Custom description"
        assert my_func(5) == 15


class TestQuickRun:
    """Test the quick.run() function."""
    
    def test_run_with_dict(self):
        """Test run with a dictionary of functions."""
        funcs = {"add": lambda a, b: a + b}
        
        with patch('makemcp.quick.from_object') as mock_from_object:
            mock_server = MagicMock()
            mock_from_object.return_value = mock_server
            
            with patch.object(mock_server, 'run'):
                from makemcp.quick import run
                run(funcs, name="test-server")
                
                mock_from_object.assert_called_once_with(funcs, name="test-server")
                mock_server.run.assert_called_once_with(
                    transport='stdio',
                    host='localhost',
                    port=8000
                )
    
    def test_run_with_file_path(self):
        """Test run with a file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def test(): pass")
            
            with patch('makemcp.quick.from_file') as mock_from_file:
                mock_server = MagicMock()
                mock_from_file.return_value = mock_server
                
                with patch.object(mock_server, 'run'):
                    from makemcp.quick import run
                    run(str(test_file), name="test-server")
                    
                    mock_from_file.assert_called_once_with(
                        str(test_file),
                        name="test-server"
                    )
                    mock_server.run.assert_called_once()
    
    def test_run_with_custom_transport(self):
        """Test run with custom transport settings."""
        funcs = {"test": lambda: "test"}
        
        with patch('makemcp.quick.from_object') as mock_from_object:
            mock_server = MagicMock()
            mock_from_object.return_value = mock_server
            
            with patch.object(mock_server, 'run'):
                from makemcp.quick import run
                run(funcs, transport='sse', host='0.0.0.0', port=9000)
                
                mock_server.run.assert_called_once_with(
                    transport='sse',
                    host='0.0.0.0',
                    port=9000
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])