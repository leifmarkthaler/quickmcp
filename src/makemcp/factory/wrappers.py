"""
Tool wrappers for converting Python functions to MCP tools.
"""

import asyncio
import inspect
import logging
from typing import Any, Callable, Dict, get_type_hints, Optional
from abc import ABC, abstractmethod

from .config import FactoryConfig, DEFAULT_CONFIG
from .type_conversion import TypeConverter
from .errors import ToolRegistrationError, TypeConversionError, log_factory_error

logger = logging.getLogger(__name__)


class ToolWrapper(ABC):
    """Abstract base class for tool wrappers."""
    
    def __init__(self, func: Callable, name: str, config: Optional[FactoryConfig] = None):
        self.func = func
        self.name = name
        self.config = config or DEFAULT_CONFIG
        self.type_converter = TypeConverter(config)
        
        # Extract function metadata
        self.signature = inspect.signature(func)
        self.doc = func.__doc__ or f"Execute {name}"
        self.type_hints = self._get_type_hints_safely()
        
        # Create the wrapper function
        self.wrapper = self._create_wrapper()
        
        # Copy metadata to wrapper
        self.wrapper.__name__ = name
        self.wrapper.__doc__ = self.doc
        self.wrapper.__annotations__ = getattr(func, '__annotations__', {})
    
    def _get_type_hints_safely(self) -> Dict[str, Any]:
        """Get type hints with error handling."""
        try:
            if self.config.cache_type_hints:
                # In a real implementation, you'd cache this
                pass
            return get_type_hints(self.func)
        except NameError as e:
            logger.debug(f"Type hints unavailable for {self.name}: {e}")
            return {}
        except ModuleNotFoundError as e:
            logger.debug(f"Module not found for type hints in {self.name}: {e}")
            return {}
        except Exception as e:
            logger.warning(f"Unexpected error getting type hints for {self.name}: {e}")
            return {}
    
    @abstractmethod
    def _create_wrapper(self) -> Callable:
        """Create the actual wrapper function."""
        pass
    
    def _convert_arguments(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Convert arguments to appropriate types."""
        converted_args = {}
        
        for param_name, param in self.signature.parameters.items():
            if param_name in kwargs:
                value = kwargs[param_name]
                
                # Try to convert based on type hints
                if param_name in self.type_hints:
                    try:
                        target_type = self.type_hints[param_name]
                        converted_value = self.type_converter.convert_value(value, target_type, param_name)
                        converted_args[param_name] = converted_value
                    except TypeConversionError as e:
                        if self.config.strict_type_conversion:
                            raise ToolRegistrationError(
                                f"Type conversion failed for parameter '{param_name}' in tool '{self.name}': {e}",
                                self.name, e
                            )
                        else:
                            logger.warning(f"Type conversion failed for {param_name}, using original value: {e}")
                            converted_args[param_name] = value
                else:
                    # No type hint, use as-is
                    converted_args[param_name] = value
            
            elif param.kind == inspect.Parameter.VAR_KEYWORD:
                # Handle **kwargs - add any remaining arguments
                for k, v in kwargs.items():
                    if k not in converted_args:
                        converted_args[k] = v
        
        return converted_args
    
    def _convert_result(self, result: Any) -> Any:
        """Convert result to JSON-serializable format."""
        if result is None:
            return {"success": True}
        elif isinstance(result, (str, int, float, bool, list, dict)):
            return result
        elif hasattr(result, '__dict__'):
            # Try to convert to dict
            try:
                return result.__dict__
            except Exception as e:
                logger.debug(f"Failed to convert result to dict: {e}")
                return str(result)
        else:
            return str(result)


class SyncToolWrapper(ToolWrapper):
    """Wrapper for synchronous functions."""
    
    def _create_wrapper(self) -> Callable:
        """Create a synchronous wrapper."""
        
        def sync_wrapper(**kwargs):
            try:
                # Convert arguments
                converted_args = self._convert_arguments(kwargs)
                
                # Call the original function
                result = self.func(**converted_args)
                
                # Convert result
                return self._convert_result(result)
                
            except Exception as e:
                error_msg = f"Error executing tool '{self.name}': {e}"
                log_factory_error(e, f"Tool '{self.name}'", logging.ERROR)
                
                if self.config.verbose_errors:
                    return {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "tool": self.name
                    }
                else:
                    return {"error": "Tool execution failed"}
        
        return sync_wrapper


class AsyncToolWrapper(ToolWrapper):
    """Wrapper for asynchronous functions."""
    
    def _create_wrapper(self) -> Callable:
        """Create an asynchronous wrapper."""
        
        async def async_wrapper(**kwargs):
            try:
                # Convert arguments
                converted_args = self._convert_arguments(kwargs)
                
                # Call the original async function
                result = await self.func(**converted_args)
                
                # Convert result
                return self._convert_result(result)
                
            except Exception as e:
                error_msg = f"Error executing async tool '{self.name}': {e}"
                log_factory_error(e, f"Async tool '{self.name}'", logging.ERROR)
                
                if self.config.verbose_errors:
                    return {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "tool": self.name
                    }
                else:
                    return {"error": "Tool execution failed"}
        
        return async_wrapper


class MethodToolWrapper(ToolWrapper):
    """Wrapper for instance methods."""
    
    def __init__(self, method: Callable, instance: Any, name: str, config: Optional[FactoryConfig] = None):
        self.instance = instance
        super().__init__(method, name, config)
    
    def _create_wrapper(self) -> Callable:
        """Create a wrapper that handles the instance method."""
        
        # Check if the method is async
        if inspect.iscoroutinefunction(self.func):
            return self._create_async_method_wrapper()
        else:
            return self._create_sync_method_wrapper()
    
    def _create_sync_method_wrapper(self) -> Callable:
        """Create a synchronous method wrapper."""
        
        def sync_method_wrapper(**kwargs):
            try:
                # Convert arguments
                converted_args = self._convert_arguments(kwargs)
                
                # Call the method on the instance
                result = self.func(**converted_args)
                
                # Convert result
                return self._convert_result(result)
                
            except Exception as e:
                error_msg = f"Error executing method tool '{self.name}': {e}"
                log_factory_error(e, f"Method tool '{self.name}'", logging.ERROR)
                
                if self.config.verbose_errors:
                    return {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "tool": self.name,
                        "method": True
                    }
                else:
                    return {"error": "Method execution failed"}
        
        return sync_method_wrapper
    
    def _create_async_method_wrapper(self) -> Callable:
        """Create an asynchronous method wrapper."""
        
        async def async_method_wrapper(**kwargs):
            try:
                # Convert arguments
                converted_args = self._convert_arguments(kwargs)
                
                # Call the async method on the instance
                result = await self.func(**converted_args)
                
                # Convert result
                return self._convert_result(result)
                
            except Exception as e:
                error_msg = f"Error executing async method tool '{self.name}': {e}"
                log_factory_error(e, f"Async method tool '{self.name}'", logging.ERROR)
                
                if self.config.verbose_errors:
                    return {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "tool": self.name,
                        "method": True
                    }
                else:
                    return {"error": "Method execution failed"}
        
        return async_method_wrapper


class ToolWrapperFactory:
    """Factory for creating appropriate tool wrappers."""
    
    def __init__(self, config: Optional[FactoryConfig] = None):
        self.config = config or DEFAULT_CONFIG
    
    def create_wrapper(self, func: Callable, name: str) -> ToolWrapper:
        """Create an appropriate wrapper for the given function."""
        if inspect.iscoroutinefunction(func):
            return AsyncToolWrapper(func, name, self.config)
        else:
            return SyncToolWrapper(func, name, self.config)
    
    def create_method_wrapper(self, method: Callable, instance: Any, name: str) -> ToolWrapper:
        """Create an appropriate wrapper for the given method."""
        return MethodToolWrapper(method, instance, name, self.config)


def create_tool_wrapper(func: Callable, name: str, config: Optional[FactoryConfig] = None) -> Callable:
    """
    Convenience function to create a tool wrapper.
    
    Args:
        func: The function to wrap
        name: The name for the tool
        config: Optional configuration
        
    Returns:
        The wrapped function ready to use as an MCP tool
    """
    factory = ToolWrapperFactory(config)
    wrapper = factory.create_wrapper(func, name)
    return wrapper.wrapper