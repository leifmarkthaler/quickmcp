"""
Utility functions and convenience functions for MCP Factory.
"""

from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import logging

from .core import MCPFactory
from .config import FactoryConfig, DEFAULT_CONFIG, create_safe_config, create_development_config
from .import_analyzer import MissingDependency
from .errors import MissingDependencyError, handle_factory_error

logger = logging.getLogger(__name__)


def create_mcp_from_module(
    module_path: str,
    server_name: Optional[str] = None,
    include_private: bool = False,
    auto_run: bool = True,
    config: Optional[FactoryConfig] = None
):
    """
    Convenience function to create and optionally run an MCP server from a module.
    
    Args:
        module_path: Path to Python file or module name
        server_name: Optional server name
        include_private: Include private functions
        auto_run: Automatically run the server
        config: Factory configuration (defaults to DEFAULT_CONFIG)
        
    Returns:
        MakeMCPServer instance
    
    Raises:
        MissingDependencyError: If required dependencies are missing
    
    Example:
        ```python
        # Create MCP server from a Python file
        server = create_mcp_from_module("my_utils.py")
        
        # Or from an installed module
        server = create_mcp_from_module("numpy", server_name="numpy-mcp")
        
        # With custom configuration
        config = create_safe_config()
        server = create_mcp_from_module("my_utils.py", config=config)
        ```
    """
    factory = MCPFactory(name=server_name, config=config)
    server = factory.from_module(module_path, include_private=include_private)
    
    if auto_run:
        server.run()
    
    return server


def create_mcp_from_object(obj: Any, server_name: Optional[str] = None, config: Optional[FactoryConfig] = None):
    """
    Create an MCP server from any Python object.
    
    Args:
        obj: Python object (module, class, instance, or dict of functions)
        server_name: Optional server name
        config: Factory configuration
        
    Returns:
        MakeMCPServer instance
    """
    import inspect
    
    factory = MCPFactory(name=server_name, config=config)
    
    if isinstance(obj, dict):
        # Dictionary of functions
        return factory.from_functions(obj, name=server_name)
    elif inspect.isclass(obj):
        # Class
        return factory.from_class(obj)
    elif inspect.ismodule(obj):
        # Module - use from_module_object for already-loaded modules
        return factory.from_module_object(obj)
    elif hasattr(obj, '__class__') and obj.__class__.__module__ != 'builtins':
        # Instance of a custom class (not built-in types)
        return factory.from_class(obj.__class__)
    else:
        raise ValueError(f"Cannot create MCP server from {type(obj).__name__} object")


# Standalone utility functions for dependency analysis
def analyze_dependencies(file_path: str, config: Optional[FactoryConfig] = None) -> List[MissingDependency]:
    """
    Analyze dependencies of a Python file.
    
    Args:
        file_path: Path to Python file
        config: Factory configuration
        
    Returns:
        List of missing dependencies
    """
    factory = MCPFactory(config=config)
    return factory.analyze_dependencies(file_path)


def check_dependencies(file_path: str, config: Optional[FactoryConfig] = None) -> Dict[str, Any]:
    """
    Check dependencies and return a detailed report.
    
    Args:
        file_path: Path to Python file
        config: Factory configuration
        
    Returns:
        Dictionary with dependency analysis results
    """
    factory = MCPFactory(config=config)
    return factory.check_dependencies(file_path)


def print_dependency_report(file_path: str, config: Optional[FactoryConfig] = None, include_dev: bool = True) -> None:
    """
    Print a formatted dependency report for a Python file.
    
    Args:
        file_path: Path to Python file
        config: Factory configuration
        include_dev: Include development dependencies in report
    """
    try:
        report = check_dependencies(file_path, config)
        
        print(f"\nDependency Analysis for: {file_path}")
        print("=" * 60)
        
        if report["total_missing"] == 0:
            print("✅ All dependencies are available!")
            return
        
        print(f"Total missing: {report['total_missing']}")
        print(f"Required missing: {report['required_missing']}")
        print(f"Optional missing: {report['optional_missing']}")
        if include_dev:
            print(f"Dev missing: {report['dev_missing']}")
        print(f"Can load module: {'✅ Yes' if report['can_load'] else '❌ No'}")
        
        if report["required_dependencies"]:
            print("\n❌ Required dependencies (will cause import errors):")
            for dep in report["required_dependencies"]:
                print(f"  • {dep.module}")
                if dep.source_line and dep.line_number:
                    print(f"    Line {dep.line_number}: {dep.source_line}")
                install_pkg = dep.suggested_install or dep.module
                if install_pkg != dep.module:
                    print(f"    Install: pip install {install_pkg}")
                else:
                    print(f"    Install: pip install {dep.module}")
        
        if report["optional_dependencies"]:
            print("\n⚠️  Optional dependencies (handled gracefully):")
            for dep in report["optional_dependencies"]:
                if not dep.is_dev_dependency:  # Don't show dev deps in optional section
                    print(f"  • {dep.module}")
                    install_pkg = dep.suggested_install or dep.module
                    if install_pkg != dep.module:
                        print(f"    Install: pip install {install_pkg}")
                    else:
                        print(f"    Install: pip install {dep.module}")
        
        if include_dev and report["dev_dependencies"]:
            print("\n🛠️  Development dependencies:")
            for dep in report["dev_dependencies"]:
                print(f"  • {dep.module}")
                install_pkg = dep.suggested_install or dep.module
                if install_pkg != dep.module:
                    print(f"    Install: pip install {install_pkg}")
                else:
                    print(f"    Install: pip install {dep.module}")
        
        if report["install_command"]:
            print(f"\n💡 Quick install command (required):")
            print(f"   {report['install_command']}")
        
        print()
        
    except Exception as e:
        error_msg = handle_factory_error(e, "Dependency analysis")
        print(f"Error: {error_msg}")


def get_install_command(file_path: str, include_optional: bool = False, include_dev: bool = False, config: Optional[FactoryConfig] = None) -> Dict[str, Optional[str]]:
    """
    Get pip install commands for missing dependencies.
    
    Args:
        file_path: Path to Python file
        include_optional: Include optional dependencies
        include_dev: Include development dependencies
        config: Factory configuration
        
    Returns:
        Dictionary with install commands for different dependency types
    """
    try:
        report = check_dependencies(file_path, config)
        commands = {}
        
        # Required dependencies
        if report["install_command"]:
            commands["required"] = report["install_command"]
        
        # Optional dependencies
        if include_optional and report["optional_dependencies"]:
            optional_non_dev = [dep for dep in report["optional_dependencies"] if not dep.is_dev_dependency]
            if optional_non_dev:
                packages = set(dep.suggested_install or dep.module for dep in optional_non_dev)
                commands["optional"] = f"pip install {' '.join(packages)}"
        
        # Development dependencies
        if include_dev and report["dev_dependencies"]:
            packages = set(dep.suggested_install or dep.module for dep in report["dev_dependencies"])
            commands["dev"] = f"pip install {' '.join(packages)}"
        
        return commands
        
    except Exception as e:
        logger.error(f"Failed to get install commands: {e}")
        return {}


def validate_factory_setup(file_path: str, config: Optional[FactoryConfig] = None) -> bool:
    """
    Validate that a file can be used with the factory.
    
    Args:
        file_path: Path to Python file
        config: Factory configuration
        
    Returns:
        True if file can be loaded, False otherwise
    """
    try:
        report = check_dependencies(file_path, config)
        return report["can_load"]
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False


# Decorator for marking functions to be exposed as MCP tools
def mcp_tool(func: Optional[Callable] = None, *, name: Optional[str] = None, description: Optional[str] = None):
    """
    Decorator to mark a function for MCP exposure.
    
    Args:
        func: Function to decorate
        name: Optional tool name (defaults to function name)
        description: Optional description (defaults to docstring)
        
    Example:
        ```python
        @mcp_tool
        def calculate(x: int, y: int) -> int:
            return x + y
        
        @mcp_tool(name="custom_name", description="Custom description")
        async def my_async_function():
            pass
        ```
    """
    def decorator(f):
        f._mcp_tool = True
        f._mcp_name = name or f.__name__
        f._mcp_description = description or f.__doc__
        return f
    
    if func is None:
        return decorator
    else:
        return decorator(func)


# Configuration shortcuts
def create_factory_for_development(name: Optional[str] = None) -> MCPFactory:
    """Create a factory configured for development use."""
    config = create_development_config()
    return MCPFactory(name=name, config=config)


def create_safe_factory(name: Optional[str] = None) -> MCPFactory:
    """Create a factory configured for safe operation."""
    config = create_safe_config()
    return MCPFactory(name=name, config=config)


def create_factory_with_config(**kwargs) -> MCPFactory:
    """Create a factory with custom configuration options."""
    config = FactoryConfig(**kwargs)
    return MCPFactory(config=config)