"""
Tests for the type conversion module.
"""

import pytest
from typing import List, Dict, Optional, Union, Any
from datetime import datetime, date
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

from quickmcp.factory.type_conversion import TypeConverter
from quickmcp.factory.config import FactoryConfig
from quickmcp.factory.errors import TypeConversionError


class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


@dataclass
class Point:
    x: float
    y: float


class TestTypeConverter:
    """Test the TypeConverter class."""
    
    def test_basic_type_conversion(self):
        """Test conversion of basic types."""
        converter = TypeConverter(FactoryConfig())
        
        # String to int
        assert converter.convert_value("42", int) == 42
        
        # String to float
        assert converter.convert_value("3.14", float) == 3.14
        
        # String to bool
        assert converter.convert_value("true", bool) is True
        assert converter.convert_value("false", bool) is False
        assert converter.convert_value("1", bool) is True
        assert converter.convert_value("0", bool) is False
        
        # Int to string
        assert converter.convert_value(42, str) == "42"
        
        # Float to int (with rounding)
        assert converter.convert_value(3.7, int) == 3
    
    def test_none_handling(self):
        """Test handling of None values."""
        converter = TypeConverter(FactoryConfig())
        
        # None for Optional types should pass through
        assert converter.convert_value(None, Optional[str]) is None
        assert converter.convert_value(None, Optional[int]) is None
        
        # None for non-optional types should raise in strict mode
        strict_converter = TypeConverter(FactoryConfig(strict_type_conversion=True))
        with pytest.raises(TypeConversionError):
            strict_converter.convert_value(None, str)
    
    def test_list_conversion(self):
        """Test conversion of list types."""
        converter = TypeConverter(FactoryConfig())
        
        # List of strings to list of ints
        result = converter.convert_value(["1", "2", "3"], List[int])
        assert result == [1, 2, 3]
        
        # Mixed list
        result = converter.convert_value([1, "2", 3.0], List[int])
        assert result == [1, 2, 3]
        
        # Empty list
        result = converter.convert_value([], List[str])
        assert result == []
        
        # Non-list to list
        result = converter.convert_value("hello", List[str])
        assert result == ["hello"]
    
    def test_dict_conversion(self):
        """Test conversion of dict types."""
        converter = TypeConverter(FactoryConfig())
        
        # String keys to int keys
        result = converter.convert_value({"1": "a", "2": "b"}, Dict[int, str])
        assert result == {1: "a", 2: "b"}
        
        # Value conversion
        result = converter.convert_value({"a": "1", "b": "2"}, Dict[str, int])
        assert result == {"a": 1, "b": 2}
        
        # Both key and value conversion
        result = converter.convert_value({"1": "10", "2": "20"}, Dict[int, int])
        assert result == {1: 10, 2: 20}
    
    def test_union_conversion(self):
        """Test conversion of Union types."""
        converter = TypeConverter(FactoryConfig())
        
        # Union[str, int]
        assert converter.convert_value("hello", Union[str, int]) == "hello"
        assert converter.convert_value(42, Union[str, int]) == 42
        assert converter.convert_value("42", Union[int, str]) == 42  # Tries int first
        
        # Union with None (Optional)
        assert converter.convert_value(None, Union[str, None]) is None
        assert converter.convert_value("test", Union[str, None]) == "test"
    
    def test_enum_conversion(self):
        """Test conversion of enum types."""
        converter = TypeConverter(FactoryConfig())
        
        # String to enum
        result = converter.convert_value("red", Color)
        assert result == Color.RED
        
        # Case insensitive in non-strict mode
        result = converter.convert_value("GREEN", Color)
        assert result == Color.GREEN
        
        # Invalid enum value
        with pytest.raises(TypeConversionError):
            converter.convert_value("yellow", Color)
    
    def test_datetime_conversion(self):
        """Test conversion of datetime types."""
        converter = TypeConverter(FactoryConfig())
        
        # ISO format string to datetime
        result = converter.convert_value("2024-01-15T10:30:00", datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        
        # Date string to date
        result = converter.convert_value("2024-01-15", date)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        
        # Timestamp to datetime
        timestamp = 1705320600  # 2024-01-15 10:30:00 UTC
        result = converter.convert_value(timestamp, datetime)
        assert isinstance(result, datetime)
    
    def test_path_conversion(self):
        """Test conversion of Path types."""
        converter = TypeConverter(FactoryConfig())
        
        # String to Path
        result = converter.convert_value("/home/user/file.txt", Path)
        assert isinstance(result, Path)
        assert str(result) == "/home/user/file.txt"
        
        # Path to Path (no conversion needed)
        path = Path("/tmp/test")
        result = converter.convert_value(path, Path)
        assert result == path
    
    def test_dataclass_conversion(self):
        """Test conversion of dataclass types."""
        converter = TypeConverter(FactoryConfig())
        
        # Dict to dataclass
        result = converter.convert_value({"x": 1.0, "y": 2.0}, Point)
        assert isinstance(result, Point)
        assert result.x == 1.0
        assert result.y == 2.0
        
        # Dict with type conversion
        result = converter.convert_value({"x": "3.5", "y": 4}, Point)
        assert result.x == 3.5
        assert result.y == 4.0
    
    def test_any_type(self):
        """Test handling of Any type."""
        converter = TypeConverter(FactoryConfig())
        
        # Any type should pass through unchanged
        assert converter.convert_value("test", Any) == "test"
        assert converter.convert_value(42, Any) == 42
        assert converter.convert_value([1, 2, 3], Any) == [1, 2, 3]
        assert converter.convert_value({"a": 1}, Any) == {"a": 1}
    
    def test_strict_mode(self):
        """Test strict type conversion mode."""
        strict_converter = TypeConverter(FactoryConfig(
            strict_type_conversion=True,
            allow_type_coercion=False
        ))
        
        # Should not coerce string to int
        with pytest.raises(TypeConversionError):
            strict_converter.convert_value("42", int)
        
        # Should not coerce float to int
        with pytest.raises(TypeConversionError):
            strict_converter.convert_value(3.14, int)
        
        # Exact type match should work
        assert strict_converter.convert_value(42, int) == 42
        assert strict_converter.convert_value("hello", str) == "hello"
    
    def test_complex_nested_types(self):
        """Test conversion of complex nested types."""
        converter = TypeConverter(FactoryConfig())
        
        # List of dicts
        data = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"}
        ]
        result = converter.convert_value(data, List[Dict[str, Union[str, int]]])
        assert result[0]["age"] == "30"  # Stays as string due to Union
        
        # Dict of lists
        data = {"numbers": ["1", "2", "3"], "letters": ["a", "b", "c"]}
        result = converter.convert_value(data, Dict[str, List[str]])
        assert result == {"numbers": ["1", "2", "3"], "letters": ["a", "b", "c"]}
    
    def test_custom_type_handler(self):
        """Test adding custom type handlers."""
        # Use strict config that doesn't allow type coercion
        converter = TypeConverter(FactoryConfig(
            strict_type_conversion=True,
            allow_type_coercion=False
        ))
        
        # Add a custom handler for a specific type
        class CustomType:
            def __init__(self, value):
                self.value = value
        
        def custom_handler(value, target_type):
            if target_type is CustomType:
                return CustomType(str(value))
            return value
        
        # This would need support in TypeConverter for custom handlers
        # For now, test that unknown types raise appropriate errors
        with pytest.raises(TypeConversionError):
            converter.convert_value("test", CustomType)
    
    def test_type_hint_caching(self):
        """Test that type hints are cached properly."""
        config = FactoryConfig(cache_type_hints=True)
        converter = TypeConverter(config)
        
        # Convert same type multiple times
        for _ in range(3):
            result = converter.convert_value(["1", "2", "3"], List[int])
            assert result == [1, 2, 3]
        
        # Caching should make subsequent conversions faster
        # (This is more of a performance test, hard to verify in unit test)
    
    def test_error_handling(self):
        """Test error handling and messages."""
        converter = TypeConverter(FactoryConfig(verbose_errors=True))
        
        # Invalid conversion should have helpful error message
        with pytest.raises(TypeConversionError) as exc_info:
            converter.convert_value("not-a-number", int)
        assert "int" in str(exc_info.value)
        
        # Invalid enum value
        with pytest.raises(TypeConversionError) as exc_info:
            converter.convert_value("purple", Color)
        assert "Color" in str(exc_info.value)
    
    def test_bytes_conversion(self):
        """Test conversion of bytes types."""
        converter = TypeConverter(FactoryConfig())
        
        # String to bytes
        result = converter.convert_value("hello", bytes)
        assert result == b"hello"
        
        # Bytes to string
        result = converter.convert_value(b"world", str)
        assert result == "world"
        
        # List of ints to bytes
        result = converter.convert_value([72, 101, 108, 108, 111], bytes)
        assert result == b"Hello"
    
    def test_set_conversion(self):
        """Test conversion of set types."""
        converter = TypeConverter(FactoryConfig())
        
        # List to set
        from typing import Set
        result = converter.convert_value([1, 2, 2, 3], Set[int])
        assert result == {1, 2, 3}
        
        # String values to int set
        result = converter.convert_value(["1", "2", "2", "3"], Set[int])
        assert result == {1, 2, 3}
    
    def test_tuple_conversion(self):
        """Test conversion of tuple types."""
        converter = TypeConverter(FactoryConfig())
        
        from typing import Tuple
        
        # List to tuple
        result = converter.convert_value([1, 2, 3], Tuple[int, int, int])
        assert result == (1, 2, 3)
        
        # Mixed types in tuple
        result = converter.convert_value(["1", 2.5, True], Tuple[int, float, bool])
        assert result == (1, 2.5, True)
        
        # Variable length tuple
        result = converter.convert_value([1, 2, 3, 4], Tuple[int, ...])
        assert result == (1, 2, 3, 4)


class TestTypeConverterIntegration:
    """Integration tests for TypeConverter with factory."""
    
    def test_with_factory_config(self):
        """Test TypeConverter with different factory configurations."""
        from quickmcp.factory.config import create_safe_config, create_permissive_config
        
        # Safe config should be strict
        safe_converter = TypeConverter(create_safe_config())
        assert safe_converter.config.strict_type_conversion is True
        
        # Permissive config should be flexible
        perm_converter = TypeConverter(create_permissive_config())
        assert perm_converter.config.strict_type_conversion is False
        assert perm_converter.config.allow_type_coercion is True
    
    def test_json_serialization(self):
        """Test that converted values are JSON-serializable."""
        import json
        converter = TypeConverter(FactoryConfig())
        
        # Convert various types and ensure they're JSON-serializable
        test_cases = [
            ({"a": 1, "b": 2}, Dict[str, int]),
            ([1, 2, 3], List[int]),
            ("test", str),
            (42, int),
            (3.14, float),
            (True, bool),
        ]
        
        for value, type_hint in test_cases:
            converted = converter.convert_value(value, type_hint)
            # Should not raise
            json.dumps(converted)
    
    def test_with_function_signatures(self):
        """Test type conversion with actual function signatures."""
        import inspect
        converter = TypeConverter(FactoryConfig())
        
        def sample_func(
            name: str,
            age: int,
            scores: List[float],
            metadata: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            return {
                "name": name,
                "age": age,
                "scores": scores,
                "metadata": metadata
            }
        
        sig = inspect.signature(sample_func)
        
        # Test converting arguments
        args = {
            "name": "Alice",
            "age": "25",
            "scores": ["98.5", "87.3", "92.1"],
            "metadata": {"level": "5", "active": "true"}
        }
        
        converted_args = {}
        for param_name, param in sig.parameters.items():
            if param_name in args:
                converted_args[param_name] = converter.convert_value(
                    args[param_name],
                    param.annotation
                )
        
        assert converted_args["name"] == "Alice"
        assert converted_args["age"] == 25
        assert converted_args["scores"] == [98.5, 87.3, 92.1]
        assert converted_args["metadata"]["level"] == "5"  # Any type preserves original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])