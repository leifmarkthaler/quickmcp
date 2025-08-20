"""
QuickMCP Decorators - Standalone decorators for MCP components
"""

from typing import Callable, Optional, Dict, Any, List
from functools import wraps
import inspect
import logging

logger = logging.getLogger(__name__)

# Global registry for decorated functions (before server is created)
_pending_tools: List[Dict[str, Any]] = []
_pending_resources: List[Dict[str, Any]] = []
_pending_prompts: List[Dict[str, Any]] = []


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    schema: Optional[Dict[str, Any]] = None,
) -> Callable:
    """
    Standalone decorator to mark a function as an MCP tool.
    
    Can be used before creating a server instance:
    
    ```python
    @tool()
    def calculate(a: int, b: int) -> int:
        return a + b
    
    # Later...
    server = QuickMCPServer("my-server")
    server.register_decorated()  # Registers all decorated functions
    ```
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_desc = description or (func.__doc__ or "").strip()
        
        # Store metadata for later registration
        _pending_tools.append({
            "function": func,
            "name": tool_name,
            "description": tool_desc,
            "schema": schema,
        })
        
        # Mark the function
        func._mcp_tool = True
        func._mcp_metadata = {
            "name": tool_name,
            "description": tool_desc,
            "schema": schema,
        }
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def resource(
    uri_template: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    mime_type: str = "text/plain",
) -> Callable:
    """
    Standalone decorator to mark a function as an MCP resource.
    
    ```python
    @resource("config://{key}")
    def get_config(key: str) -> str:
        return config_data[key]
    ```
    """
    def decorator(func: Callable) -> Callable:
        resource_name = name or func.__name__
        resource_desc = description or (func.__doc__ or "").strip()
        
        # Store metadata for later registration
        _pending_resources.append({
            "function": func,
            "uri_template": uri_template,
            "name": resource_name,
            "description": resource_desc,
            "mime_type": mime_type,
        })
        
        # Mark the function
        func._mcp_resource = True
        func._mcp_metadata = {
            "uri_template": uri_template,
            "name": resource_name,
            "description": resource_desc,
            "mime_type": mime_type,
        }
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def prompt(
    name: Optional[str] = None,
    description: Optional[str] = None,
    arguments: Optional[List[Dict[str, Any]]] = None,
) -> Callable:
    """
    Standalone decorator to mark a function as an MCP prompt template.
    
    ```python
    @prompt()
    def code_review(language: str, code: str) -> str:
        return f"Review this {language} code: {code}"
    ```
    """
    def decorator(func: Callable) -> Callable:
        prompt_name = name or func.__name__
        prompt_desc = description or (func.__doc__ or "").strip()
        
        # Store metadata for later registration
        _pending_prompts.append({
            "function": func,
            "name": prompt_name,
            "description": prompt_desc,
            "arguments": arguments,
        })
        
        # Mark the function
        func._mcp_prompt = True
        func._mcp_metadata = {
            "name": prompt_name,
            "description": prompt_desc,
            "arguments": arguments,
        }
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def get_pending_tools() -> List[Dict[str, Any]]:
    """Get all pending tools waiting for registration."""
    return _pending_tools.copy()


def get_pending_resources() -> List[Dict[str, Any]]:
    """Get all pending resources waiting for registration."""
    return _pending_resources.copy()


def get_pending_prompts() -> List[Dict[str, Any]]:
    """Get all pending prompts waiting for registration."""
    return _pending_prompts.copy()


def clear_pending() -> None:
    """Clear all pending registrations."""
    _pending_tools.clear()
    _pending_resources.clear()
    _pending_prompts.clear()


def auto_discover_mcp_components(module) -> Dict[str, List[Callable]]:
    """
    Auto-discover MCP components in a module.
    
    Args:
        module: Python module to scan
    
    Returns:
        Dictionary with discovered tools, resources, and prompts
    """
    discovered = {
        "tools": [],
        "resources": [],
        "prompts": [],
    }
    
    for name, obj in inspect.getmembers(module):
        if callable(obj):
            if hasattr(obj, "_mcp_tool"):
                discovered["tools"].append(obj)
            elif hasattr(obj, "_mcp_resource"):
                discovered["resources"].append(obj)
            elif hasattr(obj, "_mcp_prompt"):
                discovered["prompts"].append(obj)
    
    return discovered