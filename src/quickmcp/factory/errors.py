"""
Error handling and custom exceptions for MCP Factory.
"""

from typing import List, Dict, Any
import logging

from .import_analyzer import MissingDependency

logger = logging.getLogger(__name__)


class FactoryError(Exception):
    """Base exception for all factory-related errors."""
    pass


class ConfigurationError(FactoryError):
    """Raised when there's an issue with factory configuration."""
    pass


class ModuleLoadError(FactoryError):
    """Raised when a module cannot be loaded."""
    def __init__(self, message: str, module_path: str, original_error: Exception = None):
        super().__init__(message)
        self.module_path = module_path
        self.original_error = original_error


class FunctionExtractionError(FactoryError):
    """Raised when functions cannot be extracted from a module or class."""
    pass


class ToolRegistrationError(FactoryError):
    """Raised when a tool cannot be registered."""
    def __init__(self, message: str, tool_name: str, original_error: Exception = None):
        super().__init__(message)
        self.tool_name = tool_name
        self.original_error = original_error


class TypeConversionError(FactoryError):
    """Raised when type conversion fails."""
    def __init__(self, message: str, value: Any, target_type: type, parameter_name: str = None):
        super().__init__(message)
        self.value = value
        self.target_type = target_type
        self.parameter_name = parameter_name


class MissingDependencyError(ImportError, FactoryError):
    """Raised when required dependencies are missing."""
    
    def __init__(self, message: str, missing_dependencies: List[MissingDependency], module_path: str = None):
        super().__init__(message)
        self.missing_dependencies = missing_dependencies
        self.module_path = module_path
    
    @property
    def required_dependencies(self) -> List[MissingDependency]:
        """Get only the required (non-optional) dependencies."""
        return [dep for dep in self.missing_dependencies if dep.import_type != "optional"]
    
    @property
    def optional_dependencies(self) -> List[MissingDependency]:
        """Get only the optional dependencies."""
        return [dep for dep in self.missing_dependencies if dep.import_type == "optional"]
    
    @property
    def dev_dependencies(self) -> List[MissingDependency]:
        """Get only the development dependencies."""
        return [dep for dep in self.missing_dependencies if dep.is_dev_dependency]
    
    def format_error_message(self, include_dev_deps: bool = True) -> str:
        """Format a detailed error message with installation suggestions."""
        lines = [str(self)]
        
        if not self.missing_dependencies:
            return lines[0]
        
        if self.module_path:
            lines.append(f"\nModule: {self.module_path}")
        
        lines.append("\nMissing dependencies:")
        
        # Group dependencies
        required = self.required_dependencies
        optional = self.optional_dependencies
        dev_deps = self.dev_dependencies if include_dev_deps else []
        
        if required:
            lines.append("\n❌ Required dependencies (will cause import errors):")
            for dep in required:
                lines.append(f"  • {dep.module}")
                if dep.source_line and dep.line_number:
                    lines.append(f"    Line {dep.line_number}: {dep.source_line}")
                
                install_cmd = self._get_install_command(dep)
                lines.append(f"    Install: {install_cmd}")
        
        if optional:
            lines.append("\n⚠️  Optional dependencies (handled gracefully):")
            for dep in optional:
                lines.append(f"  • {dep.module}")
                install_cmd = self._get_install_command(dep)
                lines.append(f"    Install: {install_cmd}")
        
        if dev_deps and include_dev_deps:
            lines.append("\n🛠️  Development dependencies:")
            for dep in dev_deps:
                lines.append(f"  • {dep.module}")
                install_cmd = self._get_install_command(dep)
                lines.append(f"    Install: {install_cmd}")
        
        # Generate installation commands
        import shutil
        use_uv = shutil.which('uv') is not None
        cmd = "uv pip install" if use_uv else "pip install"
        
        if required:
            required_installs = [dep.suggested_install or dep.module for dep in required]
            lines.append(f"\n💡 Quick install (required): {cmd} {' '.join(set(required_installs))}")
        
        if optional and not required:
            optional_installs = [dep.suggested_install or dep.module for dep in optional]
            lines.append(f"\n💡 Quick install (optional): {cmd} {' '.join(set(optional_installs))}")
        
        return "\n".join(lines)
    
    def _get_install_command(self, dep: MissingDependency, use_uv: bool = None) -> str:
        """Get the install command for a dependency."""
        import shutil
        
        # Auto-detect uv if not specified
        if use_uv is None:
            use_uv = shutil.which('uv') is not None
        
        pkg = dep.suggested_install or dep.module
        cmd = "uv pip install" if use_uv else "pip install"
        return f"{cmd} {pkg}"
    
    def get_install_commands(self, include_optional: bool = False, include_dev: bool = False, use_uv: bool = None) -> Dict[str, str]:
        """Get install commands for different dependency types."""
        import shutil
        
        # Auto-detect uv if not specified
        if use_uv is None:
            use_uv = shutil.which('uv') is not None
        
        cmd = "uv pip install" if use_uv else "pip install"
        commands = {}
        
        # Required dependencies
        required = self.required_dependencies
        if required:
            packages = set(dep.suggested_install or dep.module for dep in required)
            commands["required"] = f"{cmd} {' '.join(packages)}"
        
        # Optional dependencies
        if include_optional:
            optional = self.optional_dependencies
            if optional:
                packages = set(dep.suggested_install or dep.module for dep in optional)
                commands["optional"] = f"{cmd} {' '.join(packages)}"
        
        # Development dependencies
        if include_dev:
            dev_deps = self.dev_dependencies
            if dev_deps:
                packages = set(dep.suggested_install or dep.module for dep in dev_deps)
                commands["dev"] = f"{cmd} {' '.join(packages)}"
        
        return commands


class SafetyError(FactoryError):
    """Raised when a safety check fails."""
    pass


class CodeExecutionError(SafetyError):
    """Raised when code execution is attempted but not allowed."""
    def __init__(self, message: str, module_path: str):
        super().__init__(message)
        self.module_path = module_path


def handle_factory_error(error: Exception, context: str = "", verbose: bool = True) -> str:
    """Handle and format factory errors consistently."""
    if isinstance(error, MissingDependencyError):
        return error.format_error_message()
    
    elif isinstance(error, ToolRegistrationError):
        msg = f"Failed to register tool '{error.tool_name}'"
        if context:
            msg = f"{context}: {msg}"
        if error.original_error and verbose:
            msg = f"{msg}: {error.original_error}"
        return msg
    
    elif isinstance(error, ModuleLoadError):
        msg = f"Failed to load module '{error.module_path}'"
        if context:
            msg = f"{context}: {msg}"
        if error.original_error and verbose:
            msg = f"{msg}: {error.original_error}"
        return msg
    
    elif isinstance(error, TypeConversionError):
        msg = f"Type conversion failed"
        if error.parameter_name:
            msg = f"{msg} for parameter '{error.parameter_name}'"
        msg = f"{msg}: cannot convert {type(error.value).__name__} to {error.target_type.__name__}"
        if context:
            msg = f"{context}: {msg}"
        return msg
    
    elif isinstance(error, FactoryError):
        msg = str(error)
        if context:
            msg = f"{context}: {msg}"
        return msg
    
    else:
        # Generic error handling
        error_type = type(error).__name__
        msg = f"{error_type}: {error}"
        if context:
            msg = f"{context}: {msg}"
        return msg


def log_factory_error(error: Exception, context: str = "", level: int = logging.ERROR):
    """Log factory errors with appropriate detail level."""
    message = handle_factory_error(error, context, verbose=True)
    
    if isinstance(error, (MissingDependencyError, ConfigurationError)):
        # These are expected errors that users should see
        logger.log(level, message)
    else:
        # Unexpected errors should include traceback
        logger.log(level, message, exc_info=True)