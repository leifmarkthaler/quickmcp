# QuickMCP Factory Documentation

The QuickMCP Factory is a powerful system for automatically generating MCP servers from existing Python code. It provides intelligent dependency analysis, safe type conversion, and flexible configuration options.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Core Features](#core-features)
- [Configuration](#configuration)
- [Dependency Management](#dependency-management)
- [Type Conversion](#type-conversion)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)
- [Architecture](#architecture)

## Overview

The MCP Factory allows you to:
- 🔄 **Automatically convert** Python modules, classes, and functions into MCP servers
- ⚡ **Preserve async/await** patterns - async functions remain async
- 🔍 **Analyze dependencies** before loading modules
- 🛡️ **Safe type conversion** with validation
- ⚙️ **Flexible configuration** for different use cases
- 📦 **Smart dependency detection** with install suggestions

## Quick Start

### Basic Usage

```python
from quickmcp.factory import create_mcp_from_module

# Create server from a Python file
server = create_mcp_from_module("my_utils.py")
server.run()
```

### CLI Usage

```bash
# Generate server from Python file
mcp-factory my_utils.py --name utils-server

# With specific transport
mcp-factory my_utils.py --transport sse --port 8080

# Include private functions
mcp-factory my_utils.py --include-private
```

## Core Features

### 1. Multiple Source Types

#### From Module/File

```python
from quickmcp.factory import MCPFactory

factory = MCPFactory(name="my-server")

# From Python file
server = factory.from_module("path/to/utils.py")

# From installed module
server = factory.from_module("numpy")

# Include private functions (starting with _)
server = factory.from_module("utils.py", include_private=True)
```

#### From Class

```python
class DataProcessor:
    def __init__(self):
        self.counter = 0
    
    def process(self, data: str) -> str:
        self.counter += 1
        return data.upper()
    
    async def async_process(self, data: str) -> str:
        await asyncio.sleep(0.1)
        return data.lower()

# Create server from class
factory = MCPFactory()
server = factory.from_class(DataProcessor)
```

#### From Functions Dictionary

```python
def add(a: int, b: int) -> int:
    return a + b

async def fetch(url: str) -> dict:
    # Async function
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return {"status": response.status}

functions = {
    "add_numbers": add,
    "fetch_url": fetch
}

factory = MCPFactory()
server = factory.from_functions(functions)
```

#### From Decorated Functions

```python
from quickmcp.factory import mcp_tool

@mcp_tool
def important_function(x: int) -> int:
    """This will be exposed as a tool."""
    return x * 2

@mcp_tool(name="custom_name", description="Custom description")
async def another_function(data: str) -> str:
    """Custom metadata for this tool."""
    return data.upper()

def not_exposed():
    """This won't be exposed (no decorator)."""
    pass

# Only decorated functions become tools
server = factory.from_file_with_decorators("my_file.py")
```

### 2. Full Async Support

The factory preserves the async nature of functions:

```python
# Mixed async/sync module
import asyncio
import aiohttp

async def fetch_data(url: str) -> dict:
    """Async function - remains async in MCP server."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return {
                "url": url,
                "status": response.status,
                "content": await response.text()
            }

def process_data(data: dict) -> str:
    """Sync function - remains sync in MCP server."""
    return json.dumps(data, indent=2)

async def parallel_fetch(urls: list) -> list:
    """Async function using gather."""
    tasks = [fetch_data(url) for url in urls]
    return await asyncio.gather(*tasks)

# All functions work correctly with factory
factory = MCPFactory()
server = factory.from_module(__file__)
# fetch_data and parallel_fetch remain async
# process_data remains sync
```

## Configuration

### Configuration System

The factory uses a powerful configuration system for fine-grained control:

```python
from quickmcp.factory import FactoryConfig, MCPFactory

# Create custom configuration
config = FactoryConfig(
    # Dependency checking
    check_dependencies=True,           # Check for missing dependencies
    strict_dependency_checking=False,  # Don't fail on optional deps
    
    # Code execution
    allow_code_execution=True,         # Allow module loading
    warn_on_code_execution=True,       # Warn when executing code
    
    # Type conversion
    strict_type_conversion=False,      # Flexible type conversion
    convert_complex_types=True,        # Handle complex types
    max_conversion_depth=5,            # Max nesting for conversions
    
    # Performance
    cache_dependency_analysis=True,    # Cache dependency results
    cache_type_conversions=True,       # Cache type conversions
    
    # Safety
    max_result_size=1_000_000,        # Max size for results (bytes)
    allow_arbitrary_types=False,      # Don't allow arbitrary types
    
    # Optional dependencies
    warn_on_optional_missing=True,    # Warn about optional deps
)

factory = MCPFactory(config=config)
```

### Pre-configured Configurations

```python
from quickmcp.factory import (
    create_safe_config,
    create_development_config,
    create_permissive_config
)

# Safe configuration (restrictive)
safe_config = create_safe_config()
# - No code execution
# - Strict type checking
# - Limited result sizes

# Development configuration (balanced)
dev_config = create_development_config()
# - Warnings enabled
# - Flexible type conversion
# - Good for debugging

# Permissive configuration (flexible)
perm_config = create_permissive_config()
# - Allow everything
# - No warnings
# - Maximum compatibility

factory = MCPFactory(config=safe_config)
```

### Convenience Factory Functions

```python
from quickmcp.factory import (
    create_safe_factory,
    create_factory_for_development,
    create_factory_with_config
)

# Pre-configured factories
safe_factory = create_safe_factory()
dev_factory = create_factory_for_development()

# Custom configuration
custom_factory = create_factory_with_config(
    check_dependencies=False,
    strict_type_conversion=True
)
```

## Dependency Management

### Intelligent Dependency Analysis

The factory analyzes Python files to detect missing dependencies:

```python
from quickmcp.factory import analyze_dependencies, check_dependencies

# Analyze a file
missing = analyze_dependencies("my_module.py")
for dep in missing:
    print(f"{dep.module}: {dep.import_type}")
    if dep.suggested_install:
        print(f"  Install: {dep.suggested_install}")

# Get detailed report
report = check_dependencies("my_module.py")
print(f"Can load: {report['can_load']}")
print(f"Required missing: {report['required_missing']}")
print(f"Optional missing: {report['optional_missing']}")
```

### Dependency Categories

The factory distinguishes between:

1. **Required Dependencies** - Will cause import failures
2. **Optional Dependencies** - Handled gracefully in try/except blocks
3. **Development Dependencies** - Testing/linting tools

```python
# Example module with different dependency types
import numpy  # Required - will fail if missing

try:
    import pandas  # Optional - handled gracefully
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

import pytest  # Development dependency (detected automatically)

def process_data(data):
    if HAS_PANDAS:
        return pandas.DataFrame(data)
    return data
```

### UV Integration

When `uv` is installed, all dependency commands use it automatically:

```python
# Factory detects missing dependencies
try:
    server = factory.from_module("my_module.py")
except MissingDependencyError as e:
    print(e.format_error_message())
    # Output:
    # Missing dependencies:
    # ❌ Required: numpy, scipy
    # 💡 Quick install: uv pip install numpy scipy
    
    # Get install commands
    commands = e.get_install_commands()
    print(commands["required"])  # "uv pip install numpy scipy"
```

### Print Dependency Report

```python
from quickmcp.factory import print_dependency_report

print_dependency_report("my_module.py")
# Output:
# Dependency Analysis for: my_module.py
# ====================================
# Total missing: 3
# Required missing: 1
# Optional missing: 2
# 
# ❌ Required dependencies:
#   • numpy
#     Install: uv pip install numpy
# 
# ⚠️ Optional dependencies:
#   • pandas
#     Install: uv pip install pandas
```

## Type Conversion

### Safe Type Conversion System

The factory includes a sophisticated type conversion system:

```python
from quickmcp.factory import TypeConverter

converter = TypeConverter()

# Basic conversions
result = converter.convert_value("123", int)  # 123
result = converter.convert_value("true", bool)  # True
result = converter.convert_value("3.14", float)  # 3.14

# Container types
result = converter.convert_value(["1", "2"], List[int])  # [1, 2]
result = converter.convert_value({"a": "1"}, Dict[str, int])  # {"a": 1}

# Complex types
from datetime import datetime
result = converter.convert_value("2024-01-01", datetime)
# datetime(2024, 1, 1)

from pathlib import Path
result = converter.convert_value("/home/user", Path)
# Path("/home/user")
```

### Supported Type Conversions

- **Basic Types**: int, float, str, bool
- **Containers**: List, Dict, Set, Tuple
- **Optional/Union**: Optional[T], Union[T1, T2]
- **DateTime**: datetime, date, time
- **Path**: pathlib.Path
- **JSON**: Automatic serialization of complex objects

## Error Handling

### Comprehensive Error Types

```python
from quickmcp.factory import (
    MissingDependencyError,
    ModuleLoadError,
    TypeConversionError,
    FunctionExtractionError,
    ToolRegistrationError,
    CodeExecutionError,
    SafetyError
)

try:
    server = factory.from_module("my_module.py")
except MissingDependencyError as e:
    # Missing required dependencies
    print(f"Missing: {e.required_dependencies}")
    print(f"Install: {e.get_install_commands()}")
except ModuleLoadError as e:
    # Failed to load module
    print(f"Module: {e.module_path}")
    print(f"Error: {e.original_error}")
except TypeConversionError as e:
    # Type conversion failed
    print(f"Value: {e.value}")
    print(f"Target type: {e.target_type}")
```

### Error Message Formatting

```python
from quickmcp.factory import handle_factory_error

try:
    server = factory.from_module("my_module.py")
except Exception as e:
    # Format error with context
    error_msg = handle_factory_error(e, "Loading module")
    print(error_msg)
```

## Advanced Usage

### Custom Import Mappings

```python
config = FactoryConfig(
    additional_pip_mappings={
        "cv2": "opencv-python",
        "sklearn": "scikit-learn"
    },
    additional_stdlib_modules={"mylib", "customlib"}
)
```

### Selective Function Exposure

```python
# Use patterns to include/exclude functions
factory = MCPFactory()

# Custom filter function
def should_expose(name: str, func: Callable) -> bool:
    # Only expose functions starting with "api_"
    return name.startswith("api_")

# Apply filter when extracting
module = factory.module_loader.load_module("my_module.py")
functions = {}
for name in dir(module):
    attr = getattr(module, name)
    if callable(attr) and should_expose(name, attr):
        functions[name] = attr

server = factory.from_functions(functions)
```

### Method Wrapping for Classes

```python
class StatefulProcessor:
    def __init__(self):
        self.state = {}
    
    def process(self, key: str, value: Any) -> None:
        """Stateful processing."""
        self.state[key] = value
    
    def get_state(self) -> dict:
        """Get current state."""
        return self.state.copy()

# Factory maintains instance state
factory = MCPFactory()
server = factory.from_class(StatefulProcessor)
# Both methods share the same instance
```

## Architecture

### Modular Design

The factory is organized into focused modules:

```
quickmcp/factory/
├── __init__.py          # Public API
├── config.py            # Configuration system
├── core.py              # Core factory classes
├── import_analyzer.py   # Dependency analysis
├── type_conversion.py   # Type conversion system
├── wrappers.py          # Function/method wrappers
├── errors.py            # Error handling
└── utils.py             # Utility functions
```

### Key Components

1. **MCPFactory**: Main factory class
2. **ModuleLoader**: Safe module loading with execution control
3. **FunctionExtractor**: Extract functions from modules/classes
4. **ImportAnalyzer**: Analyze dependencies with AST parsing
5. **TypeConverter**: Safe type conversion with validation
6. **ToolWrapper**: Wrap functions for MCP compatibility
7. **Configuration**: Flexible behavior control

### Processing Pipeline

```
1. Dependency Analysis (if enabled)
   ├── Parse AST
   ├── Detect imports
   └── Classify as required/optional

2. Module Loading
   ├── Check execution permission
   ├── Load module/class
   └── Handle import errors

3. Function Extraction
   ├── Discover functions/methods
   ├── Filter based on criteria
   └── Extract metadata

4. Tool Registration
   ├── Create wrappers
   ├── Convert types
   └── Register with server

5. Server Creation
   └── Return configured MCP server
```

## Best Practices

1. **Always check dependencies** before deployment
2. **Use configuration** appropriate for your environment
3. **Test async functions** to ensure they work correctly
4. **Handle errors gracefully** with proper error messages
5. **Document decorated functions** for better tool descriptions
6. **Use type hints** for automatic schema generation
7. **Validate with tests** before exposing as MCP server

## Migration from Old Factory

If you were using the old monolithic factory:

```python
# Old way (still works)
from quickmcp.factory_old import MCPFactory

# New way (recommended)
from quickmcp.factory import MCPFactory, FactoryConfig

# With configuration
config = FactoryConfig(check_dependencies=True)
factory = MCPFactory(config=config)
```

The new factory is fully backward compatible but provides better error handling, configuration, and performance.