"""
QuickMCP Factory - Automatically generate MCP servers from Python code.

This package provides a refactored, modular architecture for creating MCP servers
from existing Python code with comprehensive dependency analysis, safe type conversion,
and flexible configuration options.

Key Components:
- MCPFactory: Core factory class for creating servers
- ImportAnalyzer: Dependency analysis with required vs optional detection  
- TypeConverter: Safe type conversion with validation
- FactoryConfig: Flexible configuration system
- Error handling: Comprehensive error types with detailed messages

Example Usage:
    ```python
    from quickmcp.factory import create_mcp_from_module, FactoryConfig
    
    # Simple usage
    server = create_mcp_from_module("my_utils.py")
    
    # With configuration
    config = FactoryConfig(strict_type_conversion=True)
    server = create_mcp_from_module("my_utils.py", config=config)
    
    # Check dependencies first
    from quickmcp.factory import print_dependency_report
    print_dependency_report("my_utils.py")
    ```
"""

# Core classes
from .core import MCPFactory, ModuleLoader, FunctionExtractor
from .config import FactoryConfig, DEFAULT_CONFIG, create_safe_config, create_development_config, create_permissive_config

# Import analysis
from .import_analyzer import ImportAnalyzer, MissingDependency

# Error handling
from .errors import (
    FactoryError, MissingDependencyError, ModuleLoadError, FunctionExtractionError,
    ToolRegistrationError, TypeConversionError, CodeExecutionError, SafetyError,
    handle_factory_error, log_factory_error
)

# Type conversion
from .type_conversion import TypeConverter

# Tool wrappers
from .wrappers import ToolWrapper, SyncToolWrapper, AsyncToolWrapper, MethodToolWrapper, ToolWrapperFactory, create_tool_wrapper

# Utility functions
from .utils import (
    create_mcp_from_module, create_mcp_from_object,
    analyze_dependencies, check_dependencies, print_dependency_report, get_install_command,
    validate_factory_setup, mcp_tool,
    create_factory_for_development, create_safe_factory, create_factory_with_config
)

# Version information
__version__ = "2.0.0"
__author__ = "QuickMCP Team"

# Public API
__all__ = [
    # Core classes
    "MCPFactory", "Factory", "ModuleLoader", "FunctionExtractor",
    
    # Configuration
    "FactoryConfig", "DEFAULT_CONFIG", 
    "create_safe_config", "create_development_config", "create_permissive_config",
    
    # Import analysis
    "ImportAnalyzer", "MissingDependency",
    
    # Errors
    "FactoryError", "MissingDependencyError", "ModuleLoadError", "FunctionExtractionError",
    "ToolRegistrationError", "TypeConversionError", "CodeExecutionError", "SafetyError",
    "handle_factory_error", "log_factory_error",
    
    # Type conversion  
    "TypeConverter",
    
    # Tool wrappers
    "ToolWrapper", "SyncToolWrapper", "AsyncToolWrapper", "MethodToolWrapper", 
    "ToolWrapperFactory", "create_tool_wrapper",
    
    # Convenience functions
    "create_mcp_from_module", "create_mcp_from_object",
    "analyze_dependencies", "check_dependencies", "print_dependency_report", "get_install_command",
    "validate_factory_setup", "mcp_tool",
    "create_factory_for_development", "create_safe_factory", "create_factory_with_config",
]

# Main entry points (for easy importing)
Factory = MCPFactory  # Alias for compatibility