#!/usr/bin/env python
"""
Advanced QuickMCP features demonstration.
Shows configuration, dependency management, type conversion, and error handling.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickmcp import QuickMCPServer
from quickmcp.factory import (
    MCPFactory,
    FactoryConfig,
    create_safe_config,
    create_development_config,
    MissingDependencyError,
    TypeConversionError,
    print_dependency_report,
    mcp_tool
)


# Example 1: Advanced type handling
@mcp_tool
def handle_complex_types(
    text: str,
    number: Union[int, float],
    items: List[str],
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
    path: Optional[Path] = None
) -> Dict[str, Any]:
    """Demonstrate complex type handling."""
    result = {
        "text": text.upper(),
        "number": number * 2,
        "items_count": len(items),
        "items_reversed": list(reversed(items))
    }
    
    if metadata:
        result["metadata"] = metadata
    
    if timestamp:
        result["timestamp"] = timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)
    
    if path:
        result["path"] = str(path)
        result["path_exists"] = Path(path).exists()
    
    return result


# Example 2: Configuration demonstration
def demo_configurations():
    """Show different configuration options."""
    print("=" * 60)
    print("Configuration Examples")
    print("=" * 60)
    
    # Safe configuration (restrictive)
    print("\n1. Safe Configuration (Production)")
    safe_config = create_safe_config()
    print(f"   - Code execution: {safe_config.allow_code_execution}")
    print(f"   - Strict types: {safe_config.strict_type_conversion}")
    print(f"   - Max result size: {safe_config.max_result_size:,} bytes")
    
    # Development configuration (balanced)
    print("\n2. Development Configuration")
    dev_config = create_development_config()
    print(f"   - Warnings enabled: {dev_config.warn_on_code_execution}")
    print(f"   - Cache enabled: {dev_config.cache_dependency_analysis}")
    print(f"   - Flexible types: {not dev_config.strict_type_conversion}")
    
    # Custom configuration
    print("\n3. Custom Configuration")
    custom_config = FactoryConfig(
        check_dependencies=True,
        max_result_size=10_000_000,  # 10MB
        additional_pip_mappings={
            "cv2": "opencv-python",
            "sklearn": "scikit-learn"
        },
        cache_dependency_analysis=True,
        datetime_format="%Y-%m-%d %H:%M:%S"
    )
    print(f"   - Custom result limit: {custom_config.max_result_size:,} bytes")
    print(f"   - Custom pip mappings: {len(custom_config.additional_pip_mappings)}")
    print(f"   - DateTime format: {custom_config.datetime_format}")
    
    return custom_config


# Example 3: Dependency analysis
def demo_dependency_analysis():
    """Demonstrate dependency analysis features."""
    print("\n" + "=" * 60)
    print("Dependency Analysis")
    print("=" * 60)
    
    # Create a test module with various dependency patterns
    test_code = '''
# Required imports
import json
import os
from pathlib import Path

# Optional imports (handled gracefully)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Development dependencies
import pytest  # Usually only for testing

def process_data(data):
    """Process data with optional dependencies."""
    if HAS_NUMPY:
        return np.array(data)
    elif HAS_PANDAS:
        return pd.Series(data)
    else:
        return list(data)
'''
    
    # Write to temp file
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        print(f"\nAnalyzing: {temp_file}")
        print_dependency_report(temp_file)
        
        # Try to create factory
        print("\nAttempting to create server...")
        factory = MCPFactory()
        try:
            server = factory.from_module(temp_file)
            print("✅ Server created (all required deps available)")
        except MissingDependencyError as e:
            print("❌ Missing dependencies detected:")
            print(e.format_error_message())
            
            # Show install commands
            commands = e.get_install_commands(include_optional=True)
            if commands:
                print("\n💡 Install commands:")
                for dep_type, cmd in commands.items():
                    print(f"   {dep_type}: {cmd}")
    
    finally:
        Path(temp_file).unlink()


# Example 4: Type conversion with validation
class DataValidator:
    """Example class with type validation."""
    
    def __init__(self):
        self.validated_count = 0
    
    def validate_email(self, email: str) -> Dict[str, Any]:
        """Validate an email address."""
        self.validated_count += 1
        
        # Simple validation
        is_valid = "@" in email and "." in email.split("@")[-1]
        
        return {
            "email": email,
            "valid": is_valid,
            "domain": email.split("@")[-1] if "@" in email else None,
            "validated_at": datetime.now().isoformat()
        }
    
    def validate_number_range(
        self, 
        value: Union[int, float],
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """Validate a number is within range."""
        self.validated_count += 1
        
        result = {
            "value": value,
            "in_range": True,
            "messages": []
        }
        
        if min_value is not None and value < min_value:
            result["in_range"] = False
            result["messages"].append(f"Value {value} is below minimum {min_value}")
        
        if max_value is not None and value > max_value:
            result["in_range"] = False
            result["messages"].append(f"Value {value} is above maximum {max_value}")
        
        return result
    
    def get_stats(self) -> Dict[str, int]:
        """Get validation statistics."""
        return {"validated_count": self.validated_count}


# Example 5: Error handling patterns
def demo_error_handling():
    """Demonstrate error handling patterns."""
    print("\n" + "=" * 60)
    print("Error Handling Patterns")
    print("=" * 60)
    
    # Pattern 1: Handle missing dependencies
    print("\n1. Missing Dependencies:")
    try:
        from quickmcp.factory import MCPFactory
        factory = MCPFactory()
        
        # This would fail if numpy is missing
        code = "import numpy\ndef calc(x): return numpy.mean(x)"
        
        # Simulate module creation
        print("   Checking dependencies before loading...")
        # In real use, this would be factory.from_module()
        
    except MissingDependencyError as e:
        print(f"   Caught: {e.__class__.__name__}")
        print(f"   Missing: {e.required_dependencies}")
    
    # Pattern 2: Type conversion errors
    print("\n2. Type Conversion:")
    try:
        from quickmcp.factory import TypeConverter
        converter = TypeConverter()
        
        # Valid conversion
        result = converter.convert_value("123", int)
        print(f"   ✅ '123' -> {result} (type: {type(result).__name__})")
        
        # Invalid conversion (would fail in strict mode)
        try:
            result = converter.convert_value("not-a-number", int)
        except TypeConversionError as e:
            print(f"   ❌ Failed to convert: {e}")
    
    except Exception as e:
        print(f"   Error: {e}")
    
    # Pattern 3: Safe configuration
    print("\n3. Safe Configuration:")
    safe_config = create_safe_config()
    print(f"   - Code execution disabled: {not safe_config.allow_code_execution}")
    print(f"   - Strict validation: {safe_config.strict_type_conversion}")
    print(f"   - Limited result size: {safe_config.max_result_size:,} bytes")


# Example 6: Performance optimization
def demo_performance_features():
    """Show performance optimization features."""
    print("\n" + "=" * 60)
    print("Performance Features")
    print("=" * 60)
    
    # Caching configuration
    config = FactoryConfig(
        cache_dependency_analysis=True,  # Cache dependency results
        cache_type_conversions=True,     # Cache type conversions
        max_cache_size=1000              # Limit cache size
    )
    
    print("\n1. Caching enabled:")
    print(f"   - Dependency analysis: {config.cache_dependency_analysis}")
    print(f"   - Type conversions: {config.cache_type_conversions}")
    
    # Result size limits
    print("\n2. Size limits:")
    print(f"   - Max result: {config.max_result_size:,} bytes")
    print(f"   - Max string: {config.max_string_length:,} chars")
    print(f"   - Max list: {config.max_list_length:,} items")
    
    # UV integration for fast installs
    import shutil
    print("\n3. Package manager:")
    if shutil.which('uv'):
        print("   ✅ UV detected - 10-100x faster installations")
    else:
        print("   ℹ️  UV not detected - using standard pip")
        print("   💡 Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")


def main():
    """Run all demonstrations."""
    print("QuickMCP Advanced Features")
    print("=" * 60)
    print("\nThis example demonstrates:")
    print("  - Configuration system")
    print("  - Dependency analysis")
    print("  - Type conversion")
    print("  - Error handling")
    print("  - Performance features")
    print()
    
    # Run demonstrations
    custom_config = demo_configurations()
    demo_dependency_analysis()
    demo_error_handling()
    demo_performance_features()
    
    # Create server with validator class
    print("\n" + "=" * 60)
    print("Creating Server with Custom Configuration")
    print("=" * 60)
    
    factory = MCPFactory(name="advanced-server", config=custom_config)
    server = factory.from_class(DataValidator)
    
    print(f"\nServer created: {server.name}")
    print(f"Tools available:")
    for tool in server.list_tools():
        print(f"  - {tool}")
    
    # Also add the complex type handler
    server2 = factory.from_file_with_decorators(__file__)
    print(f"\nDecorated functions added:")
    for tool in server2.list_tools():
        print(f"  - {tool}")
    
    print("\n" + "=" * 60)
    print("Advanced Features Demo Complete!")
    print("=" * 60)
    
    if "--run" in sys.argv:
        print("\nStarting server with advanced configuration...")
        server.run()


if __name__ == "__main__":
    main()