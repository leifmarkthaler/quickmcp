"""
Comprehensive test suite for QuickMCP Factory
"""

import pytest
import tempfile
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List
import inspect
import asyncio

from quickmcp.factory import (
    MCPFactory,
    create_mcp_from_module,
    create_mcp_from_object,
    mcp_tool,
    FactoryConfig,
    create_safe_config
)
from quickmcp import QuickMCPServer


# Test fixtures and sample code
SAMPLE_MODULE_CODE = '''
"""Sample module for testing."""

def public_function(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

def another_function(text: str) -> str:
    """Convert to uppercase."""
    return text.upper()

def _private_function(x: int) -> int:
    """Private function."""
    return x * 2

class MyClass:
    """Test class."""
    pass

# Global variable
MY_CONSTANT = 42
'''

DECORATED_MODULE_CODE = '''
"""Module with decorated functions."""

from quickmcp.factory import mcp_tool

@mcp_tool
def decorated_func1(x: int) -> int:
    """First decorated function."""
    return x + 1

@mcp_tool(name="custom_name", description="Custom description")
def decorated_func2(x: int) -> int:
    """Second decorated function."""
    return x + 2

def not_decorated(x: int) -> int:
    """Not decorated function."""
    return x + 3

@mcp_tool
async def async_decorated(x: int) -> int:
    """Async decorated function."""
    await asyncio.sleep(0.01)
    return x + 4
'''

COMPLEX_TYPES_CODE = '''
"""Module with complex type signatures."""

from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
import json

@dataclass
class CustomType:
    """Custom dataclass type."""
    value: int
    name: str

def list_function(items: List[str]) -> List[str]:
    """Process list of strings."""
    return [item.upper() for item in items]

def dict_function(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process dictionary."""
    return {k: str(v) for k, v in data.items()}

def optional_function(value: Optional[int] = None) -> Optional[int]:
    """Function with optional parameter."""
    return value * 2 if value else None

def union_function(value: Union[int, str]) -> str:
    """Function with union type."""
    return str(value)

def custom_type_function(obj: CustomType) -> Dict[str, Any]:
    """Function with custom type."""
    return {"value": obj.value, "name": obj.name}

def no_type_hints(x, y):
    """Function without type hints."""
    return x + y

def returns_none(x: int) -> None:
    """Function that returns None."""
    print(x)

def returns_custom_object() -> CustomType:
    """Function that returns custom object."""
    return CustomType(value=42, name="test")
'''

ERROR_MODULE_CODE = '''
"""Module with various error conditions."""

def function_with_error():
    """Function that raises error."""
    raise ValueError("Test error")

def function_with_syntax_error(
    """Invalid syntax."""
    pass

class BrokenClass:
    def __init__(self):
        raise RuntimeError("Cannot instantiate")
'''


class TestMCPFactory:
    """Test MCPFactory class."""
    
    def test_factory_initialization(self):
        """Test factory initialization."""
        factory = MCPFactory()
        assert factory.name is None
        assert factory.version == "1.0.0"
        assert factory.server is None
        
        factory = MCPFactory(name="test-server", version="2.0.0")
        assert factory.name == "test-server"
        assert factory.version == "2.0.0"
    
    def test_from_module_basic(self, tmp_path):
        """Test creating server from basic module."""
        # Create temporary module file
        module_file = tmp_path / "test_module.py"
        module_file.write_text(SAMPLE_MODULE_CODE)
        
        factory = MCPFactory(name="test-server")
        server = factory.from_module(str(module_file))
        
        assert isinstance(server, QuickMCPServer)
        assert server.name == "test-server"
        assert server.version == "1.0.0"
        
        tools = server.list_tools()
        assert "public_function" in tools
        assert "another_function" in tools
        assert "_private_function" not in tools  # Private by default
        assert "MyClass" not in tools  # Classes not included
        assert "MY_CONSTANT" not in tools  # Variables not included
    
    def test_from_module_include_private(self, tmp_path):
        """Test including private functions."""
        module_file = tmp_path / "test_module.py"
        module_file.write_text(SAMPLE_MODULE_CODE)
        
        factory = MCPFactory()
        server = factory.from_module(str(module_file), include_private=True)
        
        tools = server.list_tools()
        assert "_private_function" in tools
    
    def test_from_module_with_decorators(self, tmp_path):
        """Test creating server from decorated functions."""
        module_file = tmp_path / "decorated_module.py"
        module_file.write_text(DECORATED_MODULE_CODE)
        
        # Add parent to path for import
        sys.path.insert(0, str(tmp_path))
        
        factory = MCPFactory()
        server = factory.from_file_with_decorators(
            str(module_file),
            decorator_name="mcp_tool"
        )
        
        tools = server.list_tools()
        assert "decorated_func1" in tools
        assert "decorated_func2" in tools
        assert "not_decorated" not in tools
        assert "async_decorated" in tools
        
        # Clean up sys.path
        sys.path.remove(str(tmp_path))
    
    def test_from_functions_dict(self):
        """Test creating server from functions dictionary."""
        def func1(x: int) -> int:
            return x + 1
        
        def func2(text: str) -> str:
            return text.upper()
        
        functions = {
            "add_one": func1,
            "uppercase": func2
        }
        
        factory = MCPFactory(name="dict-server")
        server = factory.from_functions(functions)
        
        assert server.name == "dict-server"
        tools = server.list_tools()
        assert "add_one" in tools
        assert "uppercase" in tools
        assert len(tools) == 2
    
    def test_from_class(self):
        """Test creating server from a class."""
        class TestClass:
            """Test class with methods."""
            
            def __init__(self):
                self.counter = 0
            
            def increment(self) -> int:
                """Increment counter."""
                self.counter += 1
                return self.counter
            
            def reset(self) -> None:
                """Reset counter."""
                self.counter = 0
            
            def _private_method(self) -> str:
                """Private method."""
                return "private"
            
            @property
            def count(self) -> int:
                """Property (should not be included)."""
                return self.counter
        
        factory = MCPFactory()
        server = factory.from_class(TestClass)
        
        tools = server.list_tools()
        assert "increment" in tools
        assert "reset" in tools
        assert "_private_method" not in tools
        assert "count" not in tools  # Properties not included
    
    def test_from_class_include_private(self):
        """Test including private methods from class."""
        class TestClass:
            def public_method(self):
                return "public"
            
            def _private_method(self):
                return "private"
        
        factory = MCPFactory()
        server = factory.from_class(TestClass, include_private=True)
        
        tools = server.list_tools()
        assert "public_method" in tools
        assert "_private_method" in tools


class TestComplexTypes:
    """Test handling of complex type signatures."""
    
    def test_complex_types_module(self, tmp_path):
        """Test module with complex type signatures."""
        module_file = tmp_path / "complex_types.py"
        module_file.write_text(COMPLEX_TYPES_CODE)
        
        sys.path.insert(0, str(tmp_path))
        
        factory = MCPFactory()
        server = factory.from_module(str(module_file))
        
        tools = server.list_tools()
        assert "list_function" in tools
        assert "dict_function" in tools
        assert "optional_function" in tools
        assert "union_function" in tools
        assert "custom_type_function" in tools
        assert "no_type_hints" in tools
        assert "returns_none" in tools
        assert "returns_custom_object" in tools
        
        # Test that functions are callable through server
        # (Would need to test actual execution in integration tests)
        
        sys.path.remove(str(tmp_path))
    
    def test_function_metadata_preservation(self):
        """Test that function metadata is preserved."""
        def test_function(x: int, y: str = "default") -> Dict[str, Any]:
            """Test function with metadata.
            
            Args:
                x: Integer parameter
                y: String parameter with default
                
            Returns:
                Dictionary result
            """
            return {"x": x, "y": y}
        
        factory = MCPFactory()
        server = factory.from_functions({"test": test_function})
        
        # Check that metadata is preserved
        tool_func = server._tools["test"]
        assert tool_func.__doc__ == test_function.__doc__
        assert tool_func.__name__ == "test"
        assert hasattr(tool_func, "__annotations__")


class TestCreateHelpers:
    """Test helper functions."""
    
    def test_create_mcp_from_module(self, tmp_path):
        """Test create_mcp_from_module helper."""
        module_file = tmp_path / "test_module.py"
        module_file.write_text(SAMPLE_MODULE_CODE)
        
        server = create_mcp_from_module(
            str(module_file),
            server_name="helper-test",
            include_private=False,
            auto_run=False
        )
        
        assert isinstance(server, QuickMCPServer)
        assert server.name == "helper-test"
        assert "public_function" in server.list_tools()
    
    def test_create_mcp_from_object_dict(self):
        """Test create_mcp_from_object with dictionary."""
        functions = {
            "func1": lambda x: x + 1,
            "func2": lambda x: x * 2
        }
        
        server = create_mcp_from_object(functions, server_name="dict-test")
        
        assert server.name == "dict-test"
        assert "func1" in server.list_tools()
        assert "func2" in server.list_tools()
    
    def test_create_mcp_from_object_class(self):
        """Test create_mcp_from_object with class."""
        class TestClass:
            def method1(self):
                return "method1"
            
            def method2(self):
                return "method2"
        
        server = create_mcp_from_object(TestClass, server_name="class-test")
        
        assert server.name == "class-test"
        assert "method1" in server.list_tools()
        assert "method2" in server.list_tools()
    
    def test_create_mcp_from_object_instance(self):
        """Test create_mcp_from_object with class instance."""
        class TestClass:
            def method(self):
                return "method"
        
        instance = TestClass()
        server = create_mcp_from_object(instance, server_name="instance-test")
        
        assert server.name == "instance-test"
        assert "method" in server.list_tools()
    
    def test_create_mcp_from_object_invalid(self):
        """Test create_mcp_from_object with invalid object."""
        with pytest.raises(ValueError):
            create_mcp_from_object(42)  # Invalid object type


class TestDecorator:
    """Test mcp_tool decorator."""
    
    def test_decorator_basic(self):
        """Test basic decorator usage."""
        @mcp_tool
        def test_function(x: int) -> int:
            """Test function."""
            return x + 1
        
        assert hasattr(test_function, "_mcp_tool")
        assert test_function._mcp_tool is True
        assert test_function._mcp_name == "test_function"
        assert test_function._mcp_description == "Test function."
        
        # Function should still be callable
        assert test_function(5) == 6
    
    def test_decorator_with_params(self):
        """Test decorator with parameters."""
        @mcp_tool(name="custom", description="Custom desc")
        def test_function():
            return "test"
        
        assert test_function._mcp_name == "custom"
        assert test_function._mcp_description == "Custom desc"
    
    def test_decorator_async_function(self):
        """Test decorator on async function."""
        @mcp_tool
        async def async_function(x: int) -> int:
            """Async function."""
            await asyncio.sleep(0.01)
            return x + 1
        
        assert hasattr(async_function, "_mcp_tool")
        assert asyncio.iscoroutinefunction(async_function)


class TestErrorHandling:
    """Test error handling."""
    
    def test_invalid_module_path(self):
        """Test with non-existent module."""
        factory = MCPFactory()
        
        with pytest.raises(Exception):
            factory.from_module("nonexistent_module.py")
    
    def test_module_with_syntax_error(self, tmp_path):
        """Test module with syntax errors."""
        module_file = tmp_path / "broken.py"
        module_file.write_text("def broken(\n    pass")  # Syntax error
        
        factory = MCPFactory()
        
        with pytest.raises((SyntaxError, Exception)):  # Could be SyntaxError or ModuleLoadError
            factory.from_module(str(module_file))
    
    def test_empty_module(self, tmp_path):
        """Test with empty module."""
        module_file = tmp_path / "empty.py"
        module_file.write_text("")
        
        factory = MCPFactory()
        server = factory.from_module(str(module_file))
        
        assert len(server.list_tools()) == 0
    
    def test_module_with_only_imports(self, tmp_path):
        """Test module with only imports."""
        module_file = tmp_path / "imports.py"
        module_file.write_text("""
import os
import sys
from pathlib import Path
""")
        
        factory = MCPFactory()
        server = factory.from_module(str(module_file))
        
        # Should not include imported functions
        assert len(server.list_tools()) == 0
    
    def test_class_that_cannot_instantiate(self):
        """Test with class that cannot be instantiated."""
        from quickmcp.factory.errors import FunctionExtractionError
        
        class BrokenClass:
            def __init__(self):
                raise RuntimeError("Cannot instantiate")
            
            def method(self):
                return "method"
        
        factory = MCPFactory()
        
        with pytest.raises(FunctionExtractionError):
            factory.from_class(BrokenClass)


class TestToolExecution:
    """Test actual tool execution through factory-created servers."""
    
    def test_execute_simple_tool(self):
        """Test executing a simple tool."""
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b
        
        factory = MCPFactory()
        server = factory.from_functions({"add": add})
        
        # Get the wrapped tool
        tool = server._tools["add"]
        result = tool(a=5, b=3)
        
        assert result == 8
    
    def test_execute_tool_with_type_conversion(self):
        """Test tool with automatic type conversion."""
        def multiply(x: float, y: float) -> float:
            """Multiply two numbers."""
            return x * y
        
        factory = MCPFactory()
        server = factory.from_functions({"multiply": multiply})
        
        tool = server._tools["multiply"]
        
        # Pass strings that should be converted to float
        result = tool(x="3.5", y="2.0")
        assert result == 7.0
    
    def test_execute_tool_returning_none(self):
        """Test tool that returns None."""
        def void_function(x: int) -> None:
            """Function that returns None."""
            # Just a side effect
            pass
        
        factory = MCPFactory()
        server = factory.from_functions({"void": void_function})
        
        tool = server._tools["void"]
        result = tool(x=5)
        
        # Should return success indicator
        assert result == {"success": True}
    
    def test_execute_tool_with_complex_result(self):
        """Test tool returning complex object."""
        class Result:
            def __init__(self, value):
                self.value = value
                self.timestamp = "2024-01-01"
        
        def complex_function() -> Result:
            """Return complex object."""
            return Result(42)
        
        factory = MCPFactory()
        server = factory.from_functions({"complex": complex_function})
        
        tool = server._tools["complex"]
        result = tool()
        
        # Should convert to dict
        assert isinstance(result, dict)
        assert result["value"] == 42
        assert result["timestamp"] == "2024-01-01"
    
    @pytest.mark.asyncio
    async def test_execute_async_tool(self):
        """Test executing async tool."""
        async def async_add(a: int, b: int) -> int:
            """Async add."""
            await asyncio.sleep(0.01)
            return a + b
        
        factory = MCPFactory()
        server = factory.from_functions({"async_add": async_add})
        
        tool = server._tools["async_add"]
        
        # Tool wrapper should handle async
        if asyncio.iscoroutinefunction(tool):
            result = await tool(a=5, b=3)
        else:
            result = tool(a=5, b=3)
        
        assert result == 8


class TestFactoryIntegration:
    """Integration tests for factory with real scenarios."""
    
    def test_stdlib_module(self):
        """Test with Python standard library module."""
        import base64
        
        factory = MCPFactory()
        server = create_mcp_from_object(base64, server_name="base64-mcp")
        
        tools = server.list_tools()
        
        # Should include various base64 functions
        assert "b64encode" in tools or "encodebytes" in tools
        assert len(tools) > 0
    
    def test_nested_module_structure(self, tmp_path):
        """Test with nested module structure."""
        # Create package structure
        package_dir = tmp_path / "mypackage"
        package_dir.mkdir()
        
        (package_dir / "__init__.py").write_text("")
        
        (package_dir / "utils.py").write_text("""
def util_function(x: int) -> int:
    return x * 2
""")
        
        (package_dir / "helpers.py").write_text("""
def helper_function(x: str) -> str:
    return x.upper()
""")
        
        sys.path.insert(0, str(tmp_path))
        
        # Test loading submodule
        factory = MCPFactory()
        server = factory.from_module("mypackage.utils")
        
        assert "util_function" in server.list_tools()
        
        sys.path.remove(str(tmp_path))
    
    def test_circular_import_handling(self, tmp_path):
        """Test handling of circular imports."""
        # Create modules with circular dependency
        module_a = tmp_path / "module_a.py"
        module_b = tmp_path / "module_b.py"
        
        module_a.write_text("""
from module_b import func_b

def func_a():
    return "a"
""")
        
        module_b.write_text("""
def func_b():
    return "b"

# Circular import
from module_a import func_a
""")
        
        sys.path.insert(0, str(tmp_path))
        
        factory = MCPFactory()
        
        # Should handle circular import gracefully
        try:
            server = factory.from_module(str(module_a))
            assert "func_a" in server.list_tools()
        finally:
            sys.path.remove(str(tmp_path))


class TestFactoryEdgeCases:
    """Test edge cases and unusual scenarios."""
    
    def test_generator_function(self):
        """Test with generator function."""
        def my_generator(n: int):
            """Generator function."""
            for i in range(n):
                yield i
        
        factory = MCPFactory()
        server = factory.from_functions({"gen": my_generator})
        
        tool = server._tools["gen"]
        result = tool(n=3)
        
        # Generator should be converted to something serializable
        assert result is not None
    
    def test_function_with_kwargs(self):
        """Test function with **kwargs."""
        def flexible_function(**kwargs):
            """Function with kwargs."""
            return kwargs
        
        factory = MCPFactory()
        server = factory.from_functions({"flexible": flexible_function})
        
        tool = server._tools["flexible"]
        result = tool(a=1, b="test", c=True)
        
        assert result == {"a": 1, "b": "test", "c": True}
    
    def test_function_with_args(self):
        """Test function with *args."""
        def variadic_function(*args):
            """Function with args."""
            return list(args)
        
        factory = MCPFactory()
        server = factory.from_functions({"variadic": variadic_function})
        
        # Note: MCP tools work with named parameters, so *args might not work as expected
        # This is a limitation to document
        assert "variadic" in server.list_tools()
    
    def test_lambda_functions(self):
        """Test with lambda functions."""
        functions = {
            "add": lambda x, y: x + y,
            "multiply": lambda x, y: x * y
        }
        
        factory = MCPFactory()
        server = factory.from_functions(functions)
        
        assert "add" in server.list_tools()
        assert "multiply" in server.list_tools()
        
        # Lambda functions won't have good descriptions
        tool = server._tools["add"]
        result = tool(x=3, y=4)
        assert result == 7
    
    def test_recursive_function(self):
        """Test with recursive function."""
        def factorial(n: int) -> int:
            """Calculate factorial recursively."""
            if n <= 1:
                return 1
            return n * factorial(n - 1)
        
        factory = MCPFactory()
        server = factory.from_functions({"factorial": factorial})
        
        tool = server._tools["factorial"]
        result = tool(n=5)
        assert result == 120
    
    def test_function_with_mutable_default(self):
        """Test function with mutable default argument."""
        def append_to_list(item: str, items: list = None) -> list:
            """Append to list with mutable default."""
            if items is None:
                items = []
            items.append(item)
            return items
        
        factory = MCPFactory()
        server = factory.from_functions({"append": append_to_list})
        
        tool = server._tools["append"]
        
        # Should handle mutable defaults safely
        result1 = tool(item="a")
        result2 = tool(item="b")
        
        assert result1 == ["a"]
        assert result2 == ["b"]  # Should not be ["a", "b"]


class TestCLIFactory:
    """Test CLI factory command (would need subprocess testing)."""
    
    @pytest.mark.skip(reason="Requires subprocess and installed package")
    def test_cli_basic(self):
        """Test basic CLI usage."""
        # This would require subprocess testing
        pass
    
    @pytest.mark.skip(reason="Requires subprocess and installed package")
    def test_cli_with_filters(self):
        """Test CLI with filters."""
        pass


# Test with real-world scenarios
class TestRealWorldScenarios:
    """Test with real-world use cases."""
    
    def test_data_science_module(self, tmp_path):
        """Test with data science style module."""
        module_file = tmp_path / "data_utils.py"
        module_file.write_text("""
import json

def load_data(filepath: str) -> dict:
    \"\"\"Load JSON data from file.\"\"\"
    with open(filepath, 'r') as f:
        return json.load(f)

def process_data(data: dict) -> dict:
    \"\"\"Process data dictionary.\"\"\"
    return {k: str(v).upper() for k, v in data.items()}

def save_data(data: dict, filepath: str) -> None:
    \"\"\"Save data to JSON file.\"\"\"
    with open(filepath, 'w') as f:
        json.dump(data, f)

def calculate_stats(numbers: list) -> dict:
    \"\"\"Calculate basic statistics.\"\"\"
    if not numbers:
        return {}
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "mean": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers)
    }
""")
        
        factory = MCPFactory(name="data-tools")
        server = factory.from_module(str(module_file))
        
        tools = server.list_tools()
        assert "load_data" in tools
        assert "process_data" in tools
        assert "save_data" in tools
        assert "calculate_stats" in tools
        
        # Test execution
        tool = server._tools["calculate_stats"]
        result = tool(numbers=[1, 2, 3, 4, 5])
        
        assert result["count"] == 5
        assert result["sum"] == 15
        assert result["mean"] == 3.0
    
    def test_api_client_module(self, tmp_path):
        """Test with API client style module."""
        module_file = tmp_path / "api_client.py"
        module_file.write_text("""
from typing import Dict, List, Optional

class APIClient:
    \"\"\"Mock API client.\"\"\"
    
    def __init__(self):
        self.base_url = "https://api.example.com"
        self.authenticated = False
    
    def authenticate(self, token: str) -> bool:
        \"\"\"Authenticate with API.\"\"\"
        self.authenticated = True
        return True
    
    def get_users(self, limit: int = 10) -> List[Dict]:
        \"\"\"Get list of users.\"\"\"
        return [{"id": i, "name": f"User{i}"} for i in range(limit)]
    
    def get_user(self, user_id: int) -> Dict:
        \"\"\"Get single user by ID.\"\"\"
        return {"id": user_id, "name": f"User{user_id}"}
    
    def create_user(self, name: str, email: str) -> Dict:
        \"\"\"Create new user.\"\"\"
        return {"id": 999, "name": name, "email": email}
    
    def _internal_method(self):
        \"\"\"Internal method.\"\"\"
        pass
""")
        
        sys.path.insert(0, str(tmp_path))
        
        # Import the module to get the class
        spec = __import__("api_client")
        
        factory = MCPFactory()
        server = factory.from_class(spec.APIClient)
        
        tools = server.list_tools()
        assert "authenticate" in tools
        assert "get_users" in tools
        assert "get_user" in tools
        assert "create_user" in tools
        assert "_internal_method" not in tools
        
        sys.path.remove(str(tmp_path))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])