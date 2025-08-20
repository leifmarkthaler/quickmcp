"""
QuickMCP Factory - Automatically generate MCP servers from Python code
"""

import ast
import inspect
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, get_type_hints, Set
import json
import logging
import re
import traceback
from dataclasses import dataclass

from .server import QuickMCPServer

logger = logging.getLogger(__name__)


@dataclass
class MissingDependency:
    """Information about a missing dependency."""
    module: str
    import_type: str  # "import", "from_import", "optional"
    line_number: Optional[int] = None
    source_line: Optional[str] = None
    suggested_install: Optional[str] = None


class ImportAnalyzer:
    """Analyze Python files for imports and missing dependencies."""
    
    # Common package name to pip install name mappings
    PIP_MAPPINGS = {
        'aiohttp': 'aiohttp',
        'requests': 'requests',
        'fastapi': 'fastapi',
        'starlette': 'starlette',
        'uvicorn': 'uvicorn',
        'pydantic': 'pydantic',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'sqlalchemy': 'sqlalchemy',
        'psycopg2': 'psycopg2-binary',
        'mysql': 'mysql-connector-python',
        'redis': 'redis',
        'celery': 'celery',
        'pytest': 'pytest',
        'click': 'click',
        'typer': 'typer',
        'rich': 'rich',
        'httpx': 'httpx',
        'websockets': 'websockets',
        'jinja2': 'jinja2',
        'flask': 'flask',
        'django': 'django',
        'boto3': 'boto3',
        'openai': 'openai',
        'anthropic': 'anthropic',
        'langchain': 'langchain',
        'transformers': 'transformers',
        'torch': 'torch',
        'tensorflow': 'tensorflow',
        'sklearn': 'scikit-learn',
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'toml': 'toml',
        'dotenv': 'python-dotenv',
        'jwt': 'PyJWT',
        'bcrypt': 'bcrypt',
        'cryptography': 'cryptography',
    }
    
    def analyze_file(self, file_path: str) -> List[MissingDependency]:
        """Analyze a Python file for missing dependencies."""
        missing_deps = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Parse the AST
            tree = ast.parse(content)
            
            # Find all import statements
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        missing = self._check_module(alias.name, "import", node.lineno, lines)
                        if missing:
                            missing_deps.append(missing)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        missing = self._check_module(node.module, "from_import", node.lineno, lines)
                        if missing:
                            missing_deps.append(missing)
        
        except Exception as e:
            logger.debug(f"Failed to analyze imports in {file_path}: {e}")
        
        return missing_deps
    
    def _check_module(self, module_name: str, import_type: str, line_num: int, lines: List[str]) -> Optional[MissingDependency]:
        """Check if a module is available."""
        # Get the top-level module name
        top_module = module_name.split('.')[0]
        
        # Skip standard library modules (basic check)
        if self._is_stdlib_module(top_module):
            return None
        
        try:
            importlib.import_module(top_module)
            return None  # Module is available
        except ImportError:
            source_line = lines[line_num - 1] if line_num <= len(lines) else None
            
            # Check if this is an optional import (in try/except block)
            # Convert AST line number (1-indexed) to list index (0-indexed)
            is_optional = self._is_optional_import(lines, line_num - 1)
            
            return MissingDependency(
                module=top_module,
                import_type="optional" if is_optional else import_type,
                line_number=line_num,
                source_line=source_line.strip() if source_line else None,
                suggested_install=self.PIP_MAPPINGS.get(top_module, top_module)
            )
    
    def _is_stdlib_module(self, module_name: str) -> bool:
        """Check if a module is part of the standard library."""
        stdlib_modules = {
            'os', 'sys', 'json', 'ast', 'inspect', 'importlib', 'pathlib', 
            'typing', 'logging', 'asyncio', 'traceback', 'dataclasses',
            'functools', 'itertools', 'collections', 'datetime', 'time',
            'math', 'random', 'string', 're', 'urllib', 'http', 'email',
            'xml', 'html', 'sqlite3', 'pickle', 'csv', 'configparser',
            'argparse', 'subprocess', 'threading', 'multiprocessing',
            'queue', 'socket', 'ssl', 'hashlib', 'uuid', 'tempfile',
            'shutil', 'glob', 'fnmatch', 'zipfile', 'tarfile', 'gzip',
            'io', 'contextlib', 'warnings', 'unittest', 'doctest'
        }
        return module_name in stdlib_modules
    
    def _is_optional_import(self, lines: List[str], line_index: int) -> bool:
        """Check if an import is inside a try/except block."""
        if line_index < 0 or line_index >= len(lines):
            return False
        
        # Get the indentation level of the import line
        import_line = lines[line_index]
        import_indent = len(import_line) - len(import_line.lstrip())
        
        # Look backwards for 'try:' at the same or lesser indentation
        try_found = False
        for i in range(line_index - 1, max(-1, line_index - 20), -1):
            line = lines[i]
            if not line.strip():  # Skip empty lines
                continue
            
            line_indent = len(line) - len(line.lstrip())
            
            # If we find a line at the same or lesser indentation that's not try:, stop
            if line_indent <= import_indent:
                if line.strip().startswith('try:'):
                    try_found = True
                    break
                else:
                    # Found other code at same level, not in a try block
                    break
        
        if not try_found:
            return False
        
        # Look forwards for 'except' block at the same indentation as try (less than import)
        for i in range(line_index + 1, min(len(lines), line_index + 20)):
            line = lines[i]
            if not line.strip():  # Skip empty lines
                continue
            
            line_indent = len(line) - len(line.lstrip())
            
            # Look for except at the same level as the try (less indented than the import)
            if line_indent < import_indent:
                if line.strip().startswith('except'):
                    return True
                else:
                    # Found other code at try level, not an except block
                    break
            # Continue looking through same-level code inside the try block
        
        return False


class MissingDependencyError(ImportError):
    """Raised when required dependencies are missing."""
    
    def __init__(self, message: str, missing_dependencies: List[MissingDependency]):
        super().__init__(message)
        self.missing_dependencies = missing_dependencies
    
    def format_error_message(self) -> str:
        """Format a detailed error message with installation suggestions."""
        lines = [str(self)]
        
        if not self.missing_dependencies:
            return lines[0]
        
        lines.append("\nMissing dependencies:")
        
        # Group by required vs optional
        required = [dep for dep in self.missing_dependencies if dep.import_type != "optional"]
        optional = [dep for dep in self.missing_dependencies if dep.import_type == "optional"]
        
        if required:
            lines.append("\nRequired dependencies (will cause import errors):")
            for dep in required:
                lines.append(f"  • {dep.module}")
                if dep.source_line:
                    lines.append(f"    Line {dep.line_number}: {dep.source_line}")
                if dep.suggested_install and dep.suggested_install != dep.module:
                    lines.append(f"    Install: pip install {dep.suggested_install}")
                else:
                    lines.append(f"    Install: pip install {dep.module}")
        
        if optional:
            lines.append("\nOptional dependencies (handled gracefully):")
            for dep in optional:
                lines.append(f"  • {dep.module} (optional)")
                if dep.suggested_install and dep.suggested_install != dep.module:
                    lines.append(f"    Install: pip install {dep.suggested_install}")
                else:
                    lines.append(f"    Install: pip install {dep.module}")
        
        # Generate installation command
        required_installs = [dep.suggested_install or dep.module for dep in required]
        if required_installs:
            lines.append(f"\nQuick install: pip install {' '.join(required_installs)}")
        
        return "\n".join(lines)


class MCPFactory:
    """Factory for creating MCP servers from Python code."""
    
    def __init__(self, name: Optional[str] = None, version: str = "1.0.0", check_dependencies: bool = True):
        """
        Initialize the MCP factory.
        
        Args:
            name: Server name (defaults to module name)
            version: Server version
            check_dependencies: Whether to analyze and report missing dependencies
        """
        self.name = name
        self.version = version
        self.server: Optional[QuickMCPServer] = None
        self.dependency_checking_enabled = check_dependencies
        self.import_analyzer = ImportAnalyzer()
    
    def from_module(self, module_path: str, include_private: bool = False) -> QuickMCPServer:
        """
        Create an MCP server from a Python module.
        
        Args:
            module_path: Path to Python file or module name
            include_private: Include private functions (starting with _)
            
        Returns:
            QuickMCPServer with tools generated from module functions
            
        Raises:
            MissingDependencyError: If required dependencies are missing
        """
        # Analyze dependencies before attempting to load
        missing_deps = []
        if self.dependency_checking_enabled and Path(module_path).exists():
            missing_deps = self.import_analyzer.analyze_file(module_path)
        
        # Try to load the module
        try:
            module = self._load_module(module_path)
        except ImportError as e:
            # If we have dependency analysis, provide a detailed error
            if missing_deps:
                required_deps = [dep for dep in missing_deps if dep.import_type != "optional"]
                if required_deps:
                    raise MissingDependencyError(
                        f"Failed to load module '{module_path}' due to missing dependencies", 
                        missing_deps
                    ) from e
            raise  # Re-raise original error if no dependency analysis available
        
        module_name = module.__name__ if hasattr(module, '__name__') else Path(module_path).stem
        
        # Create server
        server_name = self.name or f"{module_name}-mcp"
        server_description = module.__doc__ or f"MCP server for {module_name}"
        
        self.server = QuickMCPServer(
            name=server_name,
            version=self.version,
            description=server_description.strip()
        )
        
        # Extract and register functions as tools
        functions = self._extract_functions(module, include_private)
        for func_name, func in functions.items():
            self._register_function_as_tool(func_name, func)
        
        logger.info(f"Created MCP server '{server_name}' with {len(functions)} tools")
        
        # Report optional dependencies if any were found
        if missing_deps:
            optional_deps = [dep for dep in missing_deps if dep.import_type == "optional"]
            if optional_deps:
                logger.info(f"Note: {len(optional_deps)} optional dependencies not installed: " +
                          ", ".join([dep.module for dep in optional_deps]))
        
        return self.server
    
    def from_functions(self, functions: Dict[str, Callable], name: Optional[str] = None) -> QuickMCPServer:
        """
        Create an MCP server from a dictionary of functions.
        
        Args:
            functions: Dictionary mapping tool names to functions
            name: Server name
            
        Returns:
            QuickMCPServer with specified functions as tools
        """
        server_name = name or self.name or "custom-mcp"
        
        self.server = QuickMCPServer(
            name=server_name,
            version=self.version,
            description=f"MCP server with {len(functions)} custom tools"
        )
        
        for func_name, func in functions.items():
            self._register_function_as_tool(func_name, func)
        
        return self.server
    
    def from_class(self, cls: type, include_private: bool = False) -> QuickMCPServer:
        """
        Create an MCP server from a class.
        
        Args:
            cls: Class to extract methods from
            include_private: Include private methods
            
        Returns:
            QuickMCPServer with class methods as tools
        """
        class_name = cls.__name__
        server_name = self.name or f"{class_name.lower()}-mcp"
        
        self.server = QuickMCPServer(
            name=server_name,
            version=self.version,
            description=cls.__doc__ or f"MCP server for {class_name}"
        )
        
        # Create an instance if needed
        instance = cls()
        
        # Extract methods
        for name in dir(instance):
            if name.startswith('__'):
                continue
            if not include_private and name.startswith('_'):
                continue
            
            attr = getattr(instance, name)
            if callable(attr) and not inspect.isclass(attr):
                # Create a wrapper that captures the instance
                def make_wrapper(method):
                    # Check if method is async
                    if inspect.iscoroutinefunction(method):
                        async def async_wrapper(**kwargs):
                            return await method(**kwargs)
                        async_wrapper.__name__ = method.__name__
                        async_wrapper.__doc__ = method.__doc__
                        async_wrapper.__annotations__ = getattr(method, '__annotations__', {})
                        return async_wrapper
                    else:
                        def wrapper(**kwargs):
                            return method(**kwargs)
                        wrapper.__name__ = method.__name__
                        wrapper.__doc__ = method.__doc__
                        wrapper.__annotations__ = getattr(method, '__annotations__', {})
                        return wrapper
                
                self._register_function_as_tool(name, make_wrapper(attr))
        
        return self.server
    
    def from_file_with_decorators(self, file_path: str, decorator_name: str = "mcp_tool") -> QuickMCPServer:
        """
        Create an MCP server from functions decorated with a specific decorator.
        
        Args:
            file_path: Path to Python file
            decorator_name: Name of decorator to look for
            
        Returns:
            QuickMCPServer with decorated functions as tools
        """
        # Parse the file to find decorated functions
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        decorated_functions = []
        for node in ast.walk(tree):
            # Check both FunctionDef and AsyncFunctionDef
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                        decorated_functions.append(node.name)
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == decorator_name:
                            decorated_functions.append(node.name)
        
        # Load the module and extract decorated functions
        module = self._load_module(file_path)
        module_name = Path(file_path).stem
        
        server_name = self.name or f"{module_name}-mcp"
        self.server = QuickMCPServer(
            name=server_name,
            version=self.version,
            description=f"MCP server for {module_name}"
        )
        
        for func_name in decorated_functions:
            if hasattr(module, func_name):
                func = getattr(module, func_name)
                self._register_function_as_tool(func_name, func)
        
        return self.server
    
    def analyze_dependencies(self, module_path: str) -> List[MissingDependency]:
        """
        Analyze dependencies of a Python file without loading it.
        
        Args:
            module_path: Path to Python file
            
        Returns:
            List of missing dependencies
        """
        if not Path(module_path).exists():
            return []
        return self.import_analyzer.analyze_file(module_path)
    
    def check_dependencies(self, module_path: str) -> Dict[str, Any]:
        """
        Check dependencies and return a summary report.
        
        Args:
            module_path: Path to Python file
            
        Returns:
            Dictionary with dependency analysis results
        """
        missing_deps = self.analyze_dependencies(module_path)
        
        required = [dep for dep in missing_deps if dep.import_type != "optional"]
        optional = [dep for dep in missing_deps if dep.import_type == "optional"]
        
        return {
            "file": module_path,
            "total_missing": len(missing_deps),
            "required_missing": len(required),
            "optional_missing": len(optional),
            "required_dependencies": required,
            "optional_dependencies": optional,
            "can_load": len(required) == 0,
            "install_command": self._generate_install_command(required) if required else None
        }
    
    def _generate_install_command(self, dependencies: List[MissingDependency]) -> str:
        """Generate a pip install command for missing dependencies."""
        packages = []
        for dep in dependencies:
            packages.append(dep.suggested_install or dep.module)
        return f"pip install {' '.join(set(packages))}"  # Remove duplicates
    
    def _load_module(self, module_path: str):
        """Load a Python module from a file path or module name."""
        path = Path(module_path)
        
        if path.exists() and path.suffix == '.py':
            # Load from file
            spec = importlib.util.spec_from_file_location(path.stem, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[path.stem] = module
                spec.loader.exec_module(module)
                return module
        else:
            # Try to import as module name
            return importlib.import_module(module_path)
    
    def _extract_functions(self, module, include_private: bool = False) -> Dict[str, Callable]:
        """Extract functions from a module."""
        functions = {}
        
        for name in dir(module):
            # Skip special attributes
            if name.startswith('__'):
                continue
            
            # Skip private functions if requested
            if not include_private and name.startswith('_'):
                continue
            
            attr = getattr(module, name)
            
            # Only include functions (not classes, imports, etc.)
            if callable(attr) and not inspect.isclass(attr):
                # Check if it's defined in this module (not imported)
                if hasattr(attr, '__module__'):
                    if attr.__module__ == module.__name__:
                        functions[name] = attr
                else:
                    # Include if no module info (likely defined in this file)
                    functions[name] = attr
        
        return functions
    
    def _register_function_as_tool(self, name: str, func: Callable):
        """Register a function as an MCP tool."""
        if not self.server:
            raise ValueError("Server not initialized")
        
        # Get function signature and documentation
        sig = inspect.signature(func)
        doc = func.__doc__ or f"Execute {name}"
        
        # Try to get type hints
        try:
            type_hints = get_type_hints(func)
        except:
            type_hints = {}
        
        # Check if function is async
        is_async = inspect.iscoroutinefunction(func)
        
        # Create a wrapper that handles the conversion
        if is_async:
            async def tool_wrapper(**kwargs):
                # Convert arguments to appropriate types if needed
                converted_args = {}
                for param_name, param in sig.parameters.items():
                    if param_name in kwargs:
                        value = kwargs[param_name]
                        # Try to convert based on type hints
                        if param_name in type_hints:
                            try:
                                param_type = type_hints[param_name]
                                if param_type != Any and not isinstance(value, param_type):
                                    value = param_type(value)
                            except:
                                pass
                        converted_args[param_name] = value
                    elif param.kind == inspect.Parameter.VAR_KEYWORD:
                        # Handle **kwargs
                        for k, v in kwargs.items():
                            if k not in converted_args:
                                converted_args[k] = v
                
                # Call the original function
                result = await func(**converted_args)
                
                # Convert result to JSON-serializable format
                if result is None:
                    return {"success": True}
                elif isinstance(result, (str, int, float, bool, list, dict)):
                    return result
                else:
                    # Try to convert to dict or string
                    if hasattr(result, '__dict__'):
                        return result.__dict__
                    else:
                        return str(result)
        else:
            def tool_wrapper(**kwargs):
                # Convert arguments to appropriate types if needed
                converted_args = {}
                for param_name, param in sig.parameters.items():
                    if param_name in kwargs:
                        value = kwargs[param_name]
                        # Try to convert based on type hints
                        if param_name in type_hints:
                            try:
                                param_type = type_hints[param_name]
                                if param_type != Any and not isinstance(value, param_type):
                                    value = param_type(value)
                            except:
                                pass
                        converted_args[param_name] = value
                    elif param.kind == inspect.Parameter.VAR_KEYWORD:
                        # Handle **kwargs
                        for k, v in kwargs.items():
                            if k not in converted_args:
                                converted_args[k] = v
                
                # Call the original function
                result = func(**converted_args)
                
                # Convert result to JSON-serializable format
                if result is None:
                    return {"success": True}
                elif isinstance(result, (str, int, float, bool, list, dict)):
                    return result
                else:
                    # Try to convert to dict or string
                    if hasattr(result, '__dict__'):
                        return result.__dict__
                    else:
                        return str(result)
        
        # Copy metadata
        tool_wrapper.__name__ = name
        tool_wrapper.__doc__ = doc
        tool_wrapper.__annotations__ = func.__annotations__
        
        # Register with the server
        self.server.add_tool_from_function(tool_wrapper, name=name, description=doc.strip() if doc else f"Execute {name}")


def create_mcp_from_module(
    module_path: str,
    server_name: Optional[str] = None,
    include_private: bool = False,
    auto_run: bool = True,
    check_dependencies: bool = True
) -> QuickMCPServer:
    """
    Convenience function to create and optionally run an MCP server from a module.
    
    Args:
        module_path: Path to Python file or module name
        server_name: Optional server name
        include_private: Include private functions
        auto_run: Automatically run the server
        check_dependencies: Whether to analyze and report missing dependencies
        
    Returns:
        QuickMCPServer instance
    
    Raises:
        MissingDependencyError: If required dependencies are missing
    
    Example:
        ```python
        # Create MCP server from a Python file
        server = create_mcp_from_module("my_utils.py")
        
        # Or from an installed module
        server = create_mcp_from_module("numpy", server_name="numpy-mcp")
        
        # Check dependencies without loading
        try:
            server = create_mcp_from_module("my_utils.py")
        except MissingDependencyError as e:
            print(e.format_error_message())
        ```
    """
    factory = MCPFactory(name=server_name, check_dependencies=check_dependencies)
    server = factory.from_module(module_path, include_private=include_private)
    
    if auto_run:
        server.run()
    
    return server


def create_mcp_from_object(obj: Any, server_name: Optional[str] = None) -> QuickMCPServer:
    """
    Create an MCP server from any Python object.
    
    Args:
        obj: Python object (module, class, instance, or dict of functions)
        server_name: Optional server name
        
    Returns:
        QuickMCPServer instance
    """
    factory = MCPFactory(name=server_name)
    
    if isinstance(obj, dict):
        # Dictionary of functions
        return factory.from_functions(obj, name=server_name)
    elif inspect.isclass(obj):
        # Class
        return factory.from_class(obj)
    elif inspect.ismodule(obj):
        # Module
        return factory.from_module(obj.__file__ or obj.__name__)
    elif hasattr(obj, '__class__') and obj.__class__.__module__ != 'builtins':
        # Instance of a custom class (not built-in types)
        return factory.from_class(obj.__class__)
    else:
        raise ValueError(f"Cannot create MCP server from {type(obj).__name__} object")


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
        def my_function():
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


# Standalone utility functions for dependency analysis
def analyze_dependencies(file_path: str) -> List[MissingDependency]:
    """
    Analyze dependencies of a Python file.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        List of missing dependencies
    """
    analyzer = ImportAnalyzer()
    return analyzer.analyze_file(file_path)


def check_dependencies(file_path: str) -> Dict[str, Any]:
    """
    Check dependencies and return a detailed report.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        Dictionary with dependency analysis results
    """
    factory = MCPFactory(check_dependencies=True)
    return factory.check_dependencies(file_path)


def print_dependency_report(file_path: str) -> None:
    """
    Print a formatted dependency report for a Python file.
    
    Args:
        file_path: Path to Python file
    """
    report = check_dependencies(file_path)
    
    print(f"\nDependency Analysis for: {file_path}")
    print("=" * 60)
    
    if report["total_missing"] == 0:
        print("✅ All dependencies are available!")
        return
    
    print(f"Total missing: {report['total_missing']}")
    print(f"Required missing: {report['required_missing']}")
    print(f"Optional missing: {report['optional_missing']}")
    print(f"Can load module: {'✅ Yes' if report['can_load'] else '❌ No'}")
    
    if report["required_dependencies"]:
        print("\n❌ Required dependencies (will cause import errors):")
        for dep in report["required_dependencies"]:
            print(f"  • {dep.module}")
            if dep.source_line:
                print(f"    Line {dep.line_number}: {dep.source_line}")
            install_pkg = dep.suggested_install or dep.module
            if install_pkg != dep.module:
                print(f"    Install: pip install {install_pkg}")
            else:
                print(f"    Install: pip install {dep.module}")
    
    if report["optional_dependencies"]:
        print("\n⚠️  Optional dependencies (handled gracefully):")
        for dep in report["optional_dependencies"]:
            print(f"  • {dep.module}")
            install_pkg = dep.suggested_install or dep.module
            if install_pkg != dep.module:
                print(f"    Install: pip install {install_pkg}")
            else:
                print(f"    Install: pip install {dep.module}")
    
    if report["install_command"]:
        print(f"\n💡 Quick install command:")
        print(f"   {report['install_command']}")
    
    print()


def get_install_command(file_path: str) -> Optional[str]:
    """
    Get pip install command for missing required dependencies.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        Pip install command or None if no required dependencies are missing
    """
    report = check_dependencies(file_path)
    return report.get("install_command")