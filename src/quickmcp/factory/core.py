"""
Core MCP Factory classes for generating MCP servers from Python code.
"""

import ast
import inspect
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import logging

from ..server import QuickMCPServer
from .config import FactoryConfig, DEFAULT_CONFIG
from .import_analyzer import ImportAnalyzer, MissingDependency
from .wrappers import ToolWrapperFactory, MethodToolWrapper
from .errors import (
    MissingDependencyError, ModuleLoadError, FunctionExtractionError, 
    CodeExecutionError, ToolRegistrationError, log_factory_error
)

logger = logging.getLogger(__name__)


class ModuleLoader:
    """Handles safe loading of Python modules."""
    
    def __init__(self, config: Optional[FactoryConfig] = None):
        self.config = config or DEFAULT_CONFIG
    
    def load_module(self, module_path: str):
        """Load a Python module from a file path or module name."""
        if not self.config.allow_code_execution:
            raise CodeExecutionError(
                "Code execution is disabled. Enable 'allow_code_execution' in config to load modules.",
                module_path
            )
        
        if self.config.warn_on_code_execution:
            logger.warning(f"Loading module '{module_path}' will execute its code")
        
        path = Path(module_path)
        
        try:
            if path.exists() and path.suffix == '.py':
                # Load from file
                spec = importlib.util.spec_from_file_location(path.stem, path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[path.stem] = module
                    spec.loader.exec_module(module)
                    return module
                else:
                    raise ModuleLoadError(f"Could not create module spec for {path}", str(path))
            else:
                # Try to import as module name
                return importlib.import_module(module_path)
        
        except ImportError as e:
            raise ModuleLoadError(f"Failed to import module: {e}", module_path, e)
        except Exception as e:
            raise ModuleLoadError(f"Error loading module: {e}", module_path, e)


class FunctionExtractor:
    """Extracts functions from modules and classes."""
    
    def __init__(self, config: Optional[FactoryConfig] = None):
        self.config = config or DEFAULT_CONFIG
    
    def extract_from_module(self, module, include_private: bool = False) -> Dict[str, Callable]:
        """Extract functions from a module."""
        functions = {}
        
        try:
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
            
            logger.info(f"Extracted {len(functions)} functions from module")
            return functions
            
        except Exception as e:
            raise FunctionExtractionError(f"Failed to extract functions from module: {e}") from e
    
    def extract_from_class(self, cls: type, include_private: bool = False) -> Dict[str, Callable]:
        """Extract methods from a class."""
        methods = {}
        
        try:
            # Create an instance if needed
            instance = cls()
            
            for name in dir(instance):
                if name.startswith('__'):
                    continue
                if not include_private and name.startswith('_'):
                    continue
                
                attr = getattr(instance, name)
                if callable(attr) and not inspect.isclass(attr):
                    methods[name] = attr
            
            logger.info(f"Extracted {len(methods)} methods from class {cls.__name__}")
            return methods, instance
            
        except Exception as e:
            raise FunctionExtractionError(f"Failed to extract methods from class {cls.__name__}: {e}") from e
    
    def extract_decorated_functions(self, file_path: str, decorator_name: str = "mcp_tool") -> Dict[str, Callable]:
        """Extract functions decorated with a specific decorator."""
        try:
            # Parse the file to find decorated functions
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            decorated_functions = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                            decorated_functions.append(node.name)
                        elif isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Name) and decorator.func.id == decorator_name:
                                decorated_functions.append(node.name)
            
            # Load the module and extract decorated functions
            loader = ModuleLoader(self.config)
            module = loader.load_module(file_path)
            
            functions = {}
            for func_name in decorated_functions:
                if hasattr(module, func_name):
                    functions[func_name] = getattr(module, func_name)
            
            logger.info(f"Extracted {len(functions)} decorated functions")
            return functions
            
        except Exception as e:
            raise FunctionExtractionError(f"Failed to extract decorated functions: {e}") from e


class MCPFactory:
    """Factory for creating MCP servers from Python code."""
    
    def __init__(self, name: Optional[str] = None, version: str = "1.0.0", config: Optional[FactoryConfig] = None):
        """
        Initialize the MCP factory.
        
        Args:
            name: Server name (defaults to module name)
            version: Server version
            config: Factory configuration
        """
        self.name = name
        self.version = version
        self.config = config or DEFAULT_CONFIG
        
        # Initialize components
        self.import_analyzer = ImportAnalyzer(self.config)
        self.module_loader = ModuleLoader(self.config)
        self.function_extractor = FunctionExtractor(self.config)
        self.wrapper_factory = ToolWrapperFactory(self.config)
        
        self.server: Optional[QuickMCPServer] = None
    
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
        if self.config.check_dependencies and Path(module_path).exists():
            try:
                missing_deps = self.import_analyzer.analyze_file(module_path)
            except Exception as e:
                logger.warning(f"Dependency analysis failed: {e}")
        
        # Check for required missing dependencies
        if missing_deps:
            required_deps = [dep for dep in missing_deps if dep.import_type != "optional"]
            if required_deps:
                raise MissingDependencyError(
                    f"Cannot load module '{module_path}' due to missing dependencies",
                    missing_deps, module_path
                )
        
        # Load the module
        try:
            module = self.module_loader.load_module(module_path)
        except ModuleLoadError as e:
            # If we have dependency analysis, enhance the error
            if missing_deps:
                raise MissingDependencyError(
                    f"Failed to load module '{module_path}' due to missing dependencies",
                    missing_deps, module_path
                ) from e
            raise
        
        # Extract functions
        functions = self.function_extractor.extract_from_module(module, include_private)
        
        # Create server
        module_name = module.__name__ if hasattr(module, '__name__') else Path(module_path).stem
        server_name = self.name or f"{module_name}-mcp"
        server_description = module.__doc__ or f"MCP server for {module_name}"
        
        self.server = QuickMCPServer(
            name=server_name,
            version=self.version,
            description=server_description.strip()
        )
        
        # Register functions as tools
        for func_name, func in functions.items():
            self._register_tool(func_name, func)
        
        # Report optional dependencies
        if missing_deps and self.config.warn_on_optional_missing:
            optional_deps = [dep for dep in missing_deps if dep.import_type == "optional"]
            if optional_deps:
                logger.info(f"Note: {len(optional_deps)} optional dependencies not installed: " +
                          ", ".join([dep.module for dep in optional_deps]))
        
        logger.info(f"Created MCP server '{server_name}' with {len(functions)} tools")
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
            self._register_tool(func_name, func)
        
        logger.info(f"Created MCP server '{server_name}' with {len(functions)} tools")
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
        
        # Extract methods and instance
        methods, instance = self.function_extractor.extract_from_class(cls, include_private)
        
        # Register methods as tools
        for method_name, method in methods.items():
            try:
                wrapper = self.wrapper_factory.create_method_wrapper(method, instance, method_name)
                self.server.add_tool_from_function(
                    wrapper.wrapper,
                    name=method_name,
                    description=wrapper.doc.strip() if wrapper.doc else f"Execute {method_name}"
                )
            except Exception as e:
                error = ToolRegistrationError(f"Failed to register method '{method_name}': {e}", method_name, e)
                log_factory_error(error, f"Class {class_name}")
                if self.config.strict_type_conversion:
                    raise error
        
        logger.info(f"Created MCP server '{server_name}' with {len(methods)} method tools")
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
        # Extract decorated functions
        functions = self.function_extractor.extract_decorated_functions(file_path, decorator_name)
        
        # Create server
        module_name = Path(file_path).stem
        server_name = self.name or f"{module_name}-mcp"
        
        self.server = QuickMCPServer(
            name=server_name,
            version=self.version,
            description=f"MCP server for {module_name}"
        )
        
        # Register functions as tools
        for func_name, func in functions.items():
            self._register_tool(func_name, func)
        
        logger.info(f"Created MCP server '{server_name}' with {len(functions)} decorated tools")
        return self.server
    
    def _register_tool(self, name: str, func: Callable):
        """Register a function as an MCP tool."""
        if not self.server:
            raise ToolRegistrationError("Server not initialized", name)
        
        try:
            wrapper = self.wrapper_factory.create_wrapper(func, name)
            self.server.add_tool_from_function(
                wrapper.wrapper,
                name=name,
                description=wrapper.doc.strip() if wrapper.doc else f"Execute {name}"
            )
        except Exception as e:
            error = ToolRegistrationError(f"Failed to register tool '{name}': {e}", name, e)
            log_factory_error(error, f"Tool registration")
            if self.config.strict_type_conversion:
                raise error
    
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
        dev_deps = [dep for dep in missing_deps if dep.is_dev_dependency]
        
        return {
            "file": module_path,
            "total_missing": len(missing_deps),
            "required_missing": len(required),
            "optional_missing": len(optional),
            "dev_missing": len(dev_deps),
            "required_dependencies": required,
            "optional_dependencies": optional,
            "dev_dependencies": dev_deps,
            "can_load": len(required) == 0,
            "install_command": self._generate_install_command(required) if required else None
        }
    
    def _generate_install_command(self, dependencies: List[MissingDependency]) -> str:
        """Generate a pip install command for missing dependencies."""
        packages = []
        for dep in dependencies:
            packages.append(dep.suggested_install or dep.module)
        return f"pip install {' '.join(set(packages))}"  # Remove duplicates