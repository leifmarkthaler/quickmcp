"""
Safe type conversion system for MCP Factory.
"""

import json
import logging
from typing import Any, Dict, Type, Union, get_origin, get_args, Optional
from datetime import datetime, date
from pathlib import Path
from decimal import Decimal

from .config import FactoryConfig, DEFAULT_CONFIG
from .errors import TypeConversionError

logger = logging.getLogger(__name__)


class TypeConverter:
    """Safe type conversion with validation and error handling."""
    
    def __init__(self, config: Optional[FactoryConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self._conversion_cache: Dict[tuple, Any] = {}
    
    def convert_value(self, value: Any, target_type: Type, parameter_name: str = None) -> Any:
        """
        Safely convert a value to the target type.
        
        Args:
            value: The value to convert
            target_type: The target type to convert to
            parameter_name: Name of the parameter (for error messages)
            
        Returns:
            The converted value
            
        Raises:
            TypeConversionError: If conversion fails or is unsafe
        """
        # If value is already the correct type, return as-is
        if isinstance(value, target_type):
            return value
        
        # Handle None values
        if value is None:
            if self._is_optional_type(target_type):
                return None
            elif self.config.strict_type_conversion:
                raise TypeConversionError(
                    f"Cannot convert None to non-optional type {target_type.__name__}",
                    value, target_type, parameter_name
                )
            else:
                return None
        
        # Use cached conversion if available
        cache_key = (type(value), target_type, value if isinstance(value, (str, int, float, bool)) else None)
        if cache_key in self._conversion_cache:
            return self._conversion_cache[cache_key]
        
        try:
            converted = self._convert_value_impl(value, target_type, parameter_name)
            
            # Cache simple conversions
            if isinstance(value, (str, int, float, bool)):
                self._conversion_cache[cache_key] = converted
            
            return converted
            
        except Exception as e:
            if isinstance(e, TypeConversionError):
                raise
            else:
                raise TypeConversionError(
                    f"Failed to convert {type(value).__name__} to {target_type.__name__}: {e}",
                    value, target_type, parameter_name
                ) from e
    
    def _convert_value_impl(self, value: Any, target_type: Type, parameter_name: str = None) -> Any:
        """Internal implementation of value conversion."""
        
        # Handle basic types
        if target_type in (str, int, float, bool):
            return self._convert_basic_type(value, target_type)
        
        # Handle container types
        elif target_type in (list, tuple, set):
            return self._convert_container_type(value, target_type)
        
        elif target_type == dict:
            return self._convert_dict_type(value)
        
        # Handle special types
        elif target_type == Path:
            return self._convert_path_type(value)
        
        elif target_type in (datetime, date):
            return self._convert_datetime_type(value, target_type)
        
        elif target_type == Decimal:
            return self._convert_decimal_type(value)
        
        # Handle Union types (including Optional)
        elif self._is_union_type(target_type):
            return self._convert_union_type(value, target_type, parameter_name)
        
        # Handle generic types (List[int], Dict[str, str], etc.)
        elif hasattr(target_type, '__origin__'):
            return self._convert_generic_type(value, target_type, parameter_name)
        
        # For other types, only allow conversion if explicitly enabled
        elif self.config.allow_type_coercion:
            try:
                return target_type(value)
            except Exception as e:
                raise TypeConversionError(
                    f"Type coercion failed: {e}",
                    value, target_type, parameter_name
                )
        
        else:
            raise TypeConversionError(
                f"No safe conversion available from {type(value).__name__} to {target_type.__name__}",
                value, target_type, parameter_name
            )
    
    def _convert_basic_type(self, value: Any, target_type: Type) -> Any:
        """Convert to basic types (str, int, float, bool)."""
        
        if target_type == str:
            return str(value)
        
        elif target_type == int:
            if isinstance(value, (int, bool)):
                return int(value)
            elif isinstance(value, float):
                if value.is_integer():
                    return int(value)
                elif self.config.strict_type_conversion:
                    raise TypeConversionError(f"Float {value} is not an integer", value, target_type)
                else:
                    return int(value)  # Truncate
            elif isinstance(value, str):
                try:
                    return int(value)
                except ValueError:
                    # Try parsing as float first, then convert to int
                    try:
                        float_val = float(value)
                        return int(float_val)
                    except ValueError:
                        raise TypeConversionError(f"Cannot parse '{value}' as integer", value, target_type)
            else:
                raise TypeConversionError(f"Cannot convert {type(value).__name__} to int", value, target_type)
        
        elif target_type == float:
            if isinstance(value, (int, float, bool)):
                return float(value)
            elif isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    raise TypeConversionError(f"Cannot parse '{value}' as float", value, target_type)
            else:
                raise TypeConversionError(f"Cannot convert {type(value).__name__} to float", value, target_type)
        
        elif target_type == bool:
            if isinstance(value, bool):
                return value
            elif isinstance(value, (int, float)):
                return bool(value)
            elif isinstance(value, str):
                lower_val = value.lower().strip()
                if lower_val in ('true', '1', 'yes', 'on', 'enabled'):
                    return True
                elif lower_val in ('false', '0', 'no', 'off', 'disabled', ''):
                    return False
                else:
                    raise TypeConversionError(f"Cannot parse '{value}' as boolean", value, target_type)
            else:
                return bool(value)
    
    def _convert_container_type(self, value: Any, target_type: Type) -> Any:
        """Convert to container types (list, tuple, set)."""
        
        if target_type == list:
            if isinstance(value, (list, tuple, set)):
                return list(value)
            elif isinstance(value, str):
                # Try to parse as JSON array
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                except (json.JSONDecodeError, TypeError):
                    pass
                # Fall back to splitting by common delimiters
                for delimiter in [',', ';', '|', ' ']:
                    if delimiter in value:
                        return [item.strip() for item in value.split(delimiter) if item.strip()]
                return [value]  # Single item list
            else:
                return [value]  # Single item list
        
        elif target_type == tuple:
            result = self._convert_container_type(value, list)
            return tuple(result)
        
        elif target_type == set:
            result = self._convert_container_type(value, list)
            return set(result)
    
    def _convert_dict_type(self, value: Any) -> dict:
        """Convert to dict type."""
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            # Try to parse as key=value pairs
            if '=' in value:
                result = {}
                for pair in value.split(','):
                    if '=' in pair:
                        key, val = pair.split('=', 1)
                        result[key.strip()] = val.strip()
                return result
        
        raise TypeConversionError(f"Cannot convert {type(value).__name__} to dict", value, dict)
    
    def _convert_path_type(self, value: Any) -> Path:
        """Convert to Path type."""
        if isinstance(value, Path):
            return value
        elif isinstance(value, str):
            return Path(value)
        else:
            return Path(str(value))
    
    def _convert_datetime_type(self, value: Any, target_type: Type) -> Union[datetime, date]:
        """Convert to datetime or date types."""
        if isinstance(value, target_type):
            return value
        elif isinstance(value, str):
            # Try common datetime formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    parsed = datetime.strptime(value, fmt)
                    if target_type == date:
                        return parsed.date()
                    return parsed
                except ValueError:
                    continue
            
            raise TypeConversionError(f"Cannot parse '{value}' as {target_type.__name__}", value, target_type)
        else:
            raise TypeConversionError(f"Cannot convert {type(value).__name__} to {target_type.__name__}", value, target_type)
    
    def _convert_decimal_type(self, value: Any) -> Decimal:
        """Convert to Decimal type."""
        if isinstance(value, Decimal):
            return value
        elif isinstance(value, (int, float)):
            return Decimal(str(value))  # Convert via string to avoid float precision issues
        elif isinstance(value, str):
            try:
                return Decimal(value)
            except Exception:
                raise TypeConversionError(f"Cannot parse '{value}' as Decimal", value, Decimal)
        else:
            raise TypeConversionError(f"Cannot convert {type(value).__name__} to Decimal", value, Decimal)
    
    def _is_union_type(self, target_type: Type) -> bool:
        """Check if the target type is a Union type."""
        return get_origin(target_type) is Union
    
    def _is_optional_type(self, target_type: Type) -> bool:
        """Check if the target type is Optional (Union[T, None])."""
        if not self._is_union_type(target_type):
            return False
        
        args = get_args(target_type)
        return len(args) == 2 and type(None) in args
    
    def _convert_union_type(self, value: Any, target_type: Type, parameter_name: str = None) -> Any:
        """Convert to Union type by trying each possibility."""
        args = get_args(target_type)
        
        # Handle Optional[T] specially
        if self._is_optional_type(target_type):
            non_none_type = next(arg for arg in args if arg is not type(None))
            return self.convert_value(value, non_none_type, parameter_name)
        
        # Try each type in the union
        last_error = None
        for union_type in args:
            try:
                return self.convert_value(value, union_type, parameter_name)
            except TypeConversionError as e:
                last_error = e
                continue
        
        # If none worked, raise the last error
        raise last_error or TypeConversionError(
            f"Cannot convert to any type in Union {target_type}",
            value, target_type, parameter_name
        )
    
    def _convert_generic_type(self, value: Any, target_type: Type, parameter_name: str = None) -> Any:
        """Convert to generic types like List[int], Dict[str, int], etc."""
        origin = get_origin(target_type)
        args = get_args(target_type)
        
        if origin == list and args:
            # Convert to List[T]
            item_type = args[0]
            list_value = self.convert_value(value, list, parameter_name)
            return [self.convert_value(item, item_type, f"{parameter_name}[{i}]") for i, item in enumerate(list_value)]
        
        elif origin == dict and len(args) == 2:
            # Convert to Dict[K, V]
            key_type, value_type = args
            dict_value = self.convert_value(value, dict, parameter_name)
            return {
                self.convert_value(k, key_type, f"{parameter_name}[key]"): 
                self.convert_value(v, value_type, f"{parameter_name}[{k}]")
                for k, v in dict_value.items()
            }
        
        elif origin == tuple and args:
            # Convert to Tuple[T, ...]
            tuple_value = self.convert_value(value, tuple, parameter_name)
            if len(args) == len(tuple_value):
                return tuple(
                    self.convert_value(item, arg_type, f"{parameter_name}[{i}]")
                    for i, (item, arg_type) in enumerate(zip(tuple_value, args))
                )
        
        # Fall back to converting to the origin type
        return self.convert_value(value, origin, parameter_name)
    
    def clear_cache(self):
        """Clear the conversion cache."""
        self._conversion_cache.clear()
        logger.debug("Cleared type conversion cache")