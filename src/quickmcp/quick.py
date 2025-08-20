"""
QuickMCP - Super Simple API
The easiest way to create MCP servers.
"""

from typing import Optional, Any, Callable
from pathlib import Path

from .server import QuickMCPServer
from .factory import create_mcp_from_module as _create_from_module
from .factory import MCPFactory, FactoryConfig


def server(name: str = "quickmcp-server") -> QuickMCPServer:
    """
    Create a new MCP server with zero configuration.
    
    Example:
        from quickmcp.quick import server
        
        app = server("my-app")
        
        @app.tool()
        def hello(name: str) -> str:
            return f"Hello, {name}!"
        
        app.run()
    """
    return QuickMCPServer(name)


def from_file(
    file_path: str,
    name: Optional[str] = None,
    include_private: bool = False
) -> QuickMCPServer:
    """
    Create an MCP server from any Python file instantly.
    
    Example:
        from quickmcp.quick import from_file
        
        # Turn any Python file into an MCP server
        app = from_file("my_utils.py")
        app.run()
    
    Args:
        file_path: Path to Python file
        name: Optional server name (defaults to filename)
        include_private: Include functions starting with underscore
    
    Returns:
        Ready-to-run MCP server
    """
    # Use sensible defaults - no configuration needed
    config = FactoryConfig(
        check_dependencies=False,  # Don't fail on missing optional deps
        warn_on_code_execution=False,  # Don't warn, just work
        strict_type_conversion=False,  # Be flexible
        cache_dependency_analysis=True,  # Fast
        cache_type_conversions=True,  # Fast
    )
    
    if name is None:
        name = Path(file_path).stem.replace("_", "-") + "-mcp"
    
    return _create_from_module(
        file_path,
        server_name=name,
        include_private=include_private,
        auto_run=False,
        config=config
    )


def from_object(obj: Any, name: Optional[str] = None) -> QuickMCPServer:
    """
    Create an MCP server from any Python object (module, class, or dict).
    
    Example:
        from quickmcp.quick import from_object
        import math
        
        # From a module
        app = from_object(math)
        
        # From a class
        class MyTools:
            def add(self, a: int, b: int) -> int:
                return a + b
        
        app = from_object(MyTools)
        
        # From a dict of functions
        app = from_object({
            "greet": lambda name: f"Hello, {name}!",
            "add": lambda a, b: a + b
        })
        
        app.run()
    """
    from .factory import create_mcp_from_object as _create_from_object
    
    # Use sensible defaults
    config = FactoryConfig(
        check_dependencies=False,
        warn_on_code_execution=False,
        strict_type_conversion=False,
        cache_dependency_analysis=True,
        cache_type_conversions=True,
    )
    
    return _create_from_object(obj, server_name=name, config=config)


def run(
    func_or_file: Optional[Any] = None,
    name: str = "quickmcp-server",
    **kwargs
):
    """
    The simplest way to run an MCP server.
    
    Example:
        from quickmcp.quick import run
        
        # Run current file as server
        run(__file__)
        
        # Run with a function dict
        run({
            "hello": lambda name: f"Hello, {name}!",
            "add": lambda a, b: a + b
        })
        
        # Run with decorators in current file
        from quickmcp.quick import run, tool
        
        @tool
        def greet(name: str) -> str:
            return f"Hello, {name}!"
        
        run()  # Automatically finds decorated functions
    """
    import sys
    import inspect
    
    # If no argument, try to find decorated functions in caller's module
    if func_or_file is None:
        # Get the calling module
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_module = inspect.getmodule(frame.f_back)
            if caller_module and hasattr(caller_module, '__file__'):
                func_or_file = caller_module.__file__
    
    # Determine what we're working with
    if isinstance(func_or_file, str):
        # It's a file path
        app = from_file(func_or_file, name=name)
    elif isinstance(func_or_file, dict):
        # It's a dictionary of functions
        app = from_object(func_or_file, name=name)
    elif callable(func_or_file):
        # It's a single function
        app = from_object({func_or_file.__name__: func_or_file}, name=name)
    elif hasattr(func_or_file, '__class__'):
        # It's an object/class
        app = from_object(func_or_file, name=name)
    else:
        # Create empty server
        app = server(name)
    
    # Run the server
    transport = kwargs.get('transport', 'stdio')
    host = kwargs.get('host', 'localhost')
    port = kwargs.get('port', 8000)
    
    app.run(transport=transport, host=host, port=port)


# Simple decorator for marking functions as tools
def tool(func: Optional[Callable] = None, *, name: Optional[str] = None, description: Optional[str] = None):
    """
    Simple decorator to mark a function as an MCP tool.
    
    Example:
        from quickmcp.quick import tool, run
        
        @tool
        def hello(name: str) -> str:
            return f"Hello, {name}!"
        
        @tool(description="Add two numbers")
        def add(a: int, b: int) -> int:
            return a + b
        
        run()  # Automatically creates server with these tools
    """
    from .factory import mcp_tool
    return mcp_tool(func, name=name, description=description)


# Export the simplest API
__all__ = [
    'server',
    'from_file',
    'from_object',
    'run',
    'tool',
]