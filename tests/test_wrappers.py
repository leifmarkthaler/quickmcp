"""
Tests for the wrappers module.
"""

import pytest
import asyncio
import inspect
from typing import List, Dict, Optional, Any
from unittest.mock import Mock, MagicMock, patch

from makemcp.factory.wrappers import (
    SyncToolWrapper,
    AsyncToolWrapper,
    MethodToolWrapper,
    ToolWrapperFactory
)
from makemcp.factory.config import FactoryConfig


class TestSyncToolWrapper:
    """Test the SyncToolWrapper class."""
    
    def test_basic_sync_wrapper(self):
        """Test basic synchronous function wrapping."""
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b
        
        config = FactoryConfig()
        tool_wrapper = SyncToolWrapper(add, "add", config)
        
        # Test execution
        result = tool_wrapper.wrapper(a=5, b=3)
        assert result == 8
        
        # Test with string arguments (should be converted)
        result = tool_wrapper.wrapper(a="10", b="20")
        assert result == 30
    
    def test_sync_wrapper_preserves_metadata(self):
        """Test that wrapper preserves function metadata."""
        def sample_func(x: int) -> int:
            """Sample function docstring."""
            return x * 2
        
        config = FactoryConfig()
        tool_wrapper = SyncToolWrapper(sample_func, "sample_func", config)
        
        assert tool_wrapper.wrapper.__name__ == "sample_func"
        assert tool_wrapper.wrapper.__doc__ == "Sample function docstring."
        assert tool_wrapper.func == sample_func
    
    def test_sync_wrapper_with_defaults(self):
        """Test sync wrapper with default arguments."""
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"
        
        config = FactoryConfig()
        tool_wrapper = SyncToolWrapper(greet, "greet", config)
        
        # With all arguments
        assert tool_wrapper.wrapper(name="Alice", greeting="Hi") == "Hi, Alice!"
        
        # Using default
        assert tool_wrapper.wrapper(name="Bob") == "Hello, Bob!"
    
    def test_sync_wrapper_error_handling(self):
        """Test error handling in sync wrapper."""
        def divide(a: int, b: int) -> float:
            return a / b
        
        config = FactoryConfig(verbose_errors=True)
        tool_wrapper = SyncToolWrapper(divide, "divide", config)
        
        # Normal execution
        assert tool_wrapper.wrapper(a=10, b=2) == 5.0
        
        # Division by zero should return error dict
        result = tool_wrapper.wrapper(a=10, b=0)
        assert "error" in result
        assert result["error_type"] == "ZeroDivisionError"
    
    def test_sync_wrapper_with_kwargs(self):
        """Test sync wrapper with **kwargs."""
        def process(**kwargs) -> Dict[str, Any]:
            return kwargs
        
        config = FactoryConfig()
        tool_wrapper = SyncToolWrapper(process, "process", config)
        
        result = tool_wrapper.wrapper(name="test", value=42, active=True)
        assert result == {"name": "test", "value": 42, "active": True}


class TestAsyncToolWrapper:
    """Test the AsyncToolWrapper class."""
    
    @pytest.mark.asyncio
    async def test_basic_async_wrapper(self):
        """Test basic asynchronous function wrapping."""
        async def async_add(a: int, b: int) -> int:
            """Add two numbers asynchronously."""
            await asyncio.sleep(0.01)
            return a + b
        
        config = FactoryConfig()
        tool_wrapper = AsyncToolWrapper(async_add, "async_add", config)
        
        # Test execution
        result = await tool_wrapper.wrapper(a=5, b=3)
        assert result == 8
        
        # Test with string arguments (should be converted)
        result = await tool_wrapper.wrapper(a="10", b="20")
        assert result == 30
    
    @pytest.mark.asyncio
    async def test_async_wrapper_preserves_metadata(self):
        """Test that async wrapper preserves function metadata."""
        async def async_func(x: int) -> int:
            """Async function docstring."""
            await asyncio.sleep(0.01)
            return x * 2
        
        config = FactoryConfig()
        tool_wrapper = AsyncToolWrapper(async_func, "async_func", config)
        
        assert tool_wrapper.wrapper.__name__ == "async_func"
        assert tool_wrapper.wrapper.__doc__ == "Async function docstring."
        assert asyncio.iscoroutinefunction(tool_wrapper.wrapper)
        assert tool_wrapper.func == async_func
    
    @pytest.mark.asyncio
    async def test_async_wrapper_error_handling(self):
        """Test error handling in async wrapper."""
        async def async_divide(a: int, b: int) -> float:
            await asyncio.sleep(0.01)
            return a / b
        
        config = FactoryConfig(verbose_errors=True)
        tool_wrapper = AsyncToolWrapper(async_divide, "async_divide", config)
        
        # Normal execution
        result = await tool_wrapper.wrapper(a=10, b=2)
        assert result == 5.0
        
        # Division by zero should return error dict
        result = await tool_wrapper.wrapper(a=10, b=0)
        assert "error" in result
        assert result["error_type"] == "ZeroDivisionError"


class TestMethodToolWrapper:
    """Test the MethodToolWrapper class."""
    
    def test_method_wrapper(self):
        """Test wrapping class methods."""
        class Calculator:
            def __init__(self, base: int = 0):
                self.base = base
            
            def add(self, a: int, b: int) -> int:
                """Add two numbers with base."""
                return self.base + a + b
            
            def multiply(self, x: int, y: int) -> int:
                """Multiply two numbers."""
                return x * y
        
        config = FactoryConfig()
        
        # Create instance
        calc = Calculator(base=10)
        
        # Wrap method
        tool_wrapper = MethodToolWrapper(calc.add, calc, "add", config)
        
        # Test execution
        result = tool_wrapper.wrapper(a=5, b=3)
        assert result == 18  # 10 (base) + 5 + 3
        
        # Test with type conversion
        result = tool_wrapper.wrapper(a="7", b="8")
        assert result == 25  # 10 + 7 + 8
    
    @pytest.mark.asyncio
    async def test_async_method_wrapper(self):
        """Test wrapping async class methods."""
        class AsyncProcessor:
            def __init__(self, prefix: str = ""):
                self.prefix = prefix
            
            async def process(self, data: str) -> str:
                """Process data asynchronously."""
                await asyncio.sleep(0.01)
                return f"{self.prefix}: {data}"
        
        config = FactoryConfig()
        
        # Create instance
        processor = AsyncProcessor(prefix="Result")
        
        # Wrap async method
        tool_wrapper = MethodToolWrapper(processor.process, processor, "process", config)
        
        # Should preserve async nature
        assert asyncio.iscoroutinefunction(tool_wrapper.wrapper)
        
        # Test execution
        result = await tool_wrapper.wrapper(data="test data")
        assert result == "Result: test data"
    
    def test_method_wrapper_preserves_self(self):
        """Test that method wrapper preserves self reference."""
        class Counter:
            def __init__(self):
                self.count = 0
            
            def increment(self, amount: int = 1) -> int:
                """Increment counter."""
                self.count += amount
                return self.count
        
        config = FactoryConfig()
        
        counter = Counter()
        tool_wrapper = MethodToolWrapper(counter.increment, counter, "increment", config)
        
        # Multiple calls should maintain state
        assert tool_wrapper.wrapper(amount=5) == 5
        assert tool_wrapper.wrapper(amount=3) == 8
        assert tool_wrapper.wrapper() == 9  # Using default
        assert counter.count == 9


class TestToolWrapperFactory:
    """Test the ToolWrapperFactory class."""
    
    def test_create_sync_wrapper(self):
        """Test creating wrapper for sync function."""
        def sync_func(x: int) -> int:
            return x * 2
        
        factory = ToolWrapperFactory()
        wrapper = factory.create_wrapper(sync_func, "sync_func")
        
        assert isinstance(wrapper, SyncToolWrapper)
        assert not asyncio.iscoroutinefunction(wrapper.wrapper)
    
    def test_create_async_wrapper(self):
        """Test creating wrapper for async function."""
        async def async_func(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2
        
        factory = ToolWrapperFactory()
        wrapper = factory.create_wrapper(async_func, "async_func")
        
        assert isinstance(wrapper, AsyncToolWrapper)
        assert asyncio.iscoroutinefunction(wrapper.wrapper)
    
    def test_create_method_wrapper(self):
        """Test creating wrapper for class method."""
        class TestClass:
            def method(self, x: int) -> int:
                return x * 2
        
        obj = TestClass()
        factory = ToolWrapperFactory()
        wrapper = factory.create_method_wrapper(obj.method, obj, "method")
        
        assert isinstance(wrapper, MethodToolWrapper)
        assert wrapper.instance == obj
    
    def test_factory_with_config(self):
        """Test factory with custom configuration."""
        from makemcp.factory.config import create_safe_config
        
        def func(x: int) -> int:
            return x * 2
        
        config = create_safe_config()
        factory = ToolWrapperFactory(config)
        wrapper = factory.create_wrapper(func, "func")
        
        assert wrapper.config == config
        assert wrapper.config.strict_type_conversion is True
    
    def test_wrapper_selection_logic(self):
        """Test that correct wrapper type is selected."""
        factory = ToolWrapperFactory()
        
        # Sync function
        def sync_func():
            pass
        
        # Async function
        async def async_func():
            pass
        
        # Class with methods
        class TestClass:
            def sync_method(self):
                pass
            
            async def async_method(self):
                pass
        
        obj = TestClass()
        
        # Test wrapper types
        assert isinstance(factory.create_wrapper(sync_func, "sync"), SyncToolWrapper)
        assert isinstance(factory.create_wrapper(async_func, "async"), AsyncToolWrapper)
        assert isinstance(factory.create_method_wrapper(obj.sync_method, obj, "sync_method"), MethodToolWrapper)
        assert isinstance(factory.create_method_wrapper(obj.async_method, obj, "async_method"), MethodToolWrapper)


class TestWrapperTypeConversion:
    """Test type conversion in wrappers."""
    
    def test_sync_wrapper_type_conversion(self):
        """Test type conversion in sync wrapper."""
        def typed_func(
            num: int,
            text: str,
            items: List[int],
            data: Optional[Dict[str, str]] = None
        ) -> Dict[str, Any]:
            return {
                "num": num,
                "text": text,
                "items": items,
                "data": data
            }
        
        config = FactoryConfig()
        tool_wrapper = SyncToolWrapper(typed_func, "typed_func", config)
        
        result = tool_wrapper.wrapper(
            num="42",
            text=123,
            items=["1", "2", "3"],
            data={"key": 100}
        )
        
        assert result["num"] == 42
        assert result["text"] == "123"
        assert result["items"] == [1, 2, 3]
        assert result["data"]["key"] == "100"
    
    def test_strict_type_conversion(self):
        """Test strict type conversion mode."""
        from makemcp.factory.config import create_safe_config
        
        def func(x: int) -> int:
            return x * 2
        
        # Strict config
        config = create_safe_config()
        tool_wrapper = SyncToolWrapper(func, "func", config)
        
        # Should handle type conversion failure gracefully
        result = tool_wrapper.wrapper(x="not_a_number")
        assert "error" in result


class TestWrapperErrorHandling:
    """Test error handling in wrappers."""
    
    def test_verbose_error_mode(self):
        """Test verbose error reporting."""
        def failing_func():
            raise ValueError("Test error")
        
        config = FactoryConfig(verbose_errors=True)
        tool_wrapper = SyncToolWrapper(failing_func, "failing", config)
        
        result = tool_wrapper.wrapper()
        assert "error" in result
        assert "Test error" in result["error"]
        assert result["error_type"] == "ValueError"
        assert result["tool"] == "failing"
    
    def test_non_verbose_error_mode(self):
        """Test non-verbose error reporting."""
        def failing_func():
            raise ValueError("Test error")
        
        config = FactoryConfig(verbose_errors=False)
        tool_wrapper = SyncToolWrapper(failing_func, "failing", config)
        
        result = tool_wrapper.wrapper()
        assert result == {"error": "Tool execution failed"}
        assert "Test error" not in str(result)
    
    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test error handling in async wrapper."""
        async def async_failing():
            await asyncio.sleep(0.01)
            raise RuntimeError("Async error")
        
        config = FactoryConfig(verbose_errors=True)
        tool_wrapper = AsyncToolWrapper(async_failing, "async_failing", config)
        
        result = await tool_wrapper.wrapper()
        assert "error" in result
        assert "Async error" in result["error"]
        assert result["error_type"] == "RuntimeError"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])