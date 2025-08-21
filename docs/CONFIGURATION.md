# MakeMCP Configuration Guide

This guide covers all configuration options available in MakeMCP, including server configuration, factory configuration, and environment variables.

## Table of Contents

- [Factory Configuration](#factory-configuration)
- [Server Configuration](#server-configuration)
- [Discovery Configuration](#discovery-configuration)
- [Environment Variables](#environment-variables)
- [Configuration Files](#configuration-files)

## Factory Configuration

The MCP Factory provides extensive configuration options for controlling behavior, safety, and performance.

### FactoryConfig Class

```python
from makemcp.factory import FactoryConfig

config = FactoryConfig(
    # Dependency checking
    check_dependencies=True,              # Check for missing dependencies before loading
    strict_dependency_checking=False,     # Fail on optional dependencies
    additional_pip_mappings={},           # Custom package name mappings
    additional_stdlib_modules=set(),      # Additional stdlib modules to ignore
    
    # Code execution
    allow_code_execution=True,            # Allow loading Python modules
    warn_on_code_execution=True,          # Show warnings when executing code
    
    # Type conversion
    strict_type_conversion=False,         # Strict type checking
    convert_complex_types=True,           # Handle complex type conversions
    max_conversion_depth=5,               # Maximum nesting depth for conversions
    datetime_format="%Y-%m-%d %H:%M:%S", # Default datetime parsing format
    
    # Performance
    cache_dependency_analysis=True,       # Cache dependency analysis results
    cache_type_conversions=True,          # Cache type conversion results
    
    # Safety limits
    max_result_size=1_000_000,           # Maximum result size in bytes
    max_string_length=100_000,           # Maximum string length
    max_list_length=10_000,              # Maximum list length
    max_dict_keys=1_000,                 # Maximum dictionary keys
    
    # Error handling
    allow_arbitrary_types=False,         # Allow non-JSON-serializable types
    warn_on_optional_missing=True,       # Warn about optional dependencies
    ignore_missing_type_hints=True,      # Continue if type hints are missing
)
```

### Pre-configured Configurations

#### Safe Configuration

For production environments with strict security requirements:

```python
from makemcp.factory import create_safe_config

config = create_safe_config()
# Features:
# - No code execution (allow_code_execution=False)
# - Strict type conversion
# - Small result size limits
# - No arbitrary types
# - All warnings enabled
```

#### Development Configuration

For development and debugging:

```python
from makemcp.factory import create_development_config

config = create_development_config()
# Features:
# - Code execution with warnings
# - Flexible type conversion
# - Larger size limits
# - Detailed error messages
# - Cache enabled for performance
```

#### Permissive Configuration

For maximum compatibility:

```python
from makemcp.factory import create_permissive_config

config = create_permissive_config()
# Features:
# - All features enabled
# - No warnings
# - Large size limits
# - Arbitrary types allowed
# - Minimal restrictions
```

### Configuration Merging

Configurations can be merged and customized:

```python
# Start with a base configuration
base_config = create_safe_config()

# Override specific settings
custom_config = FactoryConfig(
    **base_config.__dict__,
    max_result_size=5_000_000,  # Increase size limit
    cache_dependency_analysis=True  # Enable caching
)
```

## Server Configuration

### MakeMCPServer Options

```python
from makemcp import MakeMCPServer

server = MakeMCPServer(
    name="my-server",              # Server name (required)
    version="1.0.0",               # Server version
    description="My MCP server",   # Server description
    capabilities={                 # Server capabilities
        "tools": True,
        "resources": True,
        "prompts": True
    },
    instructions="Server usage instructions",  # Usage instructions
    enforce_schema=True,           # Enforce parameter schemas
    enable_logging=True,           # Enable debug logging
    log_level="INFO"              # Logging level
)
```

### Transport Configuration

#### Stdio Transport (Default)

```python
server.run(
    transport="stdio",
    # No additional configuration needed
)
```

#### SSE Transport

```python
server.run(
    transport="sse",
    host="localhost",      # Server host
    port=8080,            # Server port
    cors_origins=["*"],   # CORS configuration
    enable_auth=False,    # Authentication (future)
    ssl_cert=None,        # SSL certificate path
    ssl_key=None         # SSL key path
)
```

## Discovery Configuration

### Registry Configuration

```python
from makemcp.registry import Registry

registry = Registry(
    registry_path="~/.makemcp/registry.json",  # Registry file location
    auto_save=True,                            # Auto-save changes
    validate_on_load=True                      # Validate entries on load
)
```

### Network Discovery

```python
from makemcp.autodiscovery import NetworkDiscovery

discovery = NetworkDiscovery(
    multicast_group="239.255.41.42",  # Multicast group
    port=42424,                       # Discovery port
    timeout=5.0,                       # Discovery timeout
    interface="0.0.0.0",              # Network interface
    ttl=1                             # Multicast TTL
)
```

## Environment Variables

MakeMCP respects the following environment variables:

### Core Settings

```bash
# MakeMCP settings
QUICKMCP_HOME="~/.makemcp"          # MakeMCP home directory
QUICKMCP_REGISTRY="~/.makemcp/registry.json"  # Registry location
QUICKMCP_LOG_LEVEL="INFO"            # Logging level
QUICKMCP_DEBUG="false"               # Debug mode

# Factory settings
QUICKMCP_FACTORY_CHECK_DEPS="true"   # Check dependencies
QUICKMCP_FACTORY_ALLOW_EXEC="true"   # Allow code execution
QUICKMCP_FACTORY_CACHE="true"        # Enable caching

# Discovery settings
QUICKMCP_DISCOVERY_ENABLED="true"    # Enable discovery
QUICKMCP_DISCOVERY_PORT="42424"      # Discovery port
QUICKMCP_DISCOVERY_TIMEOUT="5"       # Discovery timeout (seconds)
```

### Package Manager

```bash
# Prefer UV for installations
QUICKMCP_USE_UV="auto"  # auto, true, false
# auto: Detect if uv is available
# true: Always use uv (error if not available)
# false: Always use pip
```

### Development

```bash
# Development settings
QUICKMCP_DEV_MODE="false"           # Development mode
QUICKMCP_TEST_MODE="false"          # Test mode
QUICKMCP_VERBOSE="false"            # Verbose output
```

## Configuration Files

### Project Configuration

Create a `.makemcp.yaml` in your project root:

```yaml
# .makemcp.yaml
server:
  name: "my-project-server"
  version: "1.0.0"
  description: "My project MCP server"

factory:
  check_dependencies: true
  strict_type_conversion: false
  cache_enabled: true
  
  # Custom pip mappings
  pip_mappings:
    cv2: opencv-python
    sklearn: scikit-learn

discovery:
  enabled: true
  port: 42424
  
transport:
  default: stdio
  sse:
    host: localhost
    port: 8080
```

Load configuration:

```python
import yaml
from makemcp.factory import FactoryConfig

# Load from file
with open(".makemcp.yaml") as f:
    config_data = yaml.safe_load(f)

# Create factory config
factory_config = FactoryConfig(**config_data.get("factory", {}))
```

### User Configuration

Global user settings in `~/.makemcp/config.yaml`:

```yaml
# ~/.makemcp/config.yaml
defaults:
  factory:
    check_dependencies: true
    warn_on_code_execution: true
  
  server:
    enable_logging: true
    log_level: INFO
  
  discovery:
    enabled: true

# Package manager preference
package_manager: uv  # or pip

# Development settings
development:
  verbose: true
  debug: false
```

## Configuration Precedence

Configuration is applied in the following order (later overrides earlier):

1. **Default values** - Built-in defaults
2. **User config** - `~/.makemcp/config.yaml`
3. **Project config** - `.makemcp.yaml` in project root
4. **Environment variables** - `QUICKMCP_*` variables
5. **Code configuration** - Explicit configuration in code
6. **Command-line arguments** - CLI flags (highest priority)

Example:

```python
# 1. Defaults
config = FactoryConfig()  # Uses defaults

# 2. User config (if exists)
user_config = load_user_config()
config = merge_configs(config, user_config)

# 3. Project config (if exists)
project_config = load_project_config()
config = merge_configs(config, project_config)

# 4. Environment variables
if os.getenv("QUICKMCP_FACTORY_CHECK_DEPS"):
    config.check_dependencies = os.getenv("QUICKMCP_FACTORY_CHECK_DEPS") == "true"

# 5. Code configuration (overrides all above)
config = FactoryConfig(check_dependencies=False)

# 6. CLI arguments (when using CLI)
# mcp-factory --no-check-deps  # Overrides everything
```

## Best Practices

### Production Configuration

```python
# Production settings
production_config = FactoryConfig(
    # Safety first
    allow_code_execution=False,
    strict_type_conversion=True,
    
    # Resource limits
    max_result_size=100_000,
    max_string_length=10_000,
    
    # No warnings in production
    warn_on_code_execution=False,
    warn_on_optional_missing=False,
    
    # Performance
    cache_dependency_analysis=True,
    cache_type_conversions=True
)
```

### Development Configuration

```python
# Development settings
dev_config = FactoryConfig(
    # Helpful warnings
    warn_on_code_execution=True,
    warn_on_optional_missing=True,
    
    # Flexible for testing
    strict_type_conversion=False,
    allow_arbitrary_types=True,
    
    # Larger limits for debugging
    max_result_size=10_000_000,
    
    # Performance for fast iteration
    cache_dependency_analysis=True
)
```

### Testing Configuration

```python
# Test settings
test_config = FactoryConfig(
    # Strict for tests
    strict_type_conversion=True,
    strict_dependency_checking=True,
    
    # No caching for test isolation
    cache_dependency_analysis=False,
    cache_type_conversions=False,
    
    # Warnings as errors
    warn_on_code_execution=True,
    allow_arbitrary_types=False
)
```

## Troubleshooting

### Configuration Not Applied

Check configuration precedence - CLI arguments override everything:

```python
# This will be overridden by CLI flags
config = FactoryConfig(check_dependencies=True)

# CLI: mcp-factory --no-check-deps
# Result: check_dependencies=False (CLI wins)
```

### Missing Dependencies Not Detected

Ensure dependency checking is enabled:

```python
config = FactoryConfig(
    check_dependencies=True,  # Must be True
    strict_dependency_checking=False  # Optional deps won't fail
)
```

### Type Conversion Errors

Adjust type conversion settings:

```python
config = FactoryConfig(
    strict_type_conversion=False,  # More flexible
    convert_complex_types=True,     # Handle complex types
    ignore_missing_type_hints=True  # Don't fail on missing hints
)
```

### Performance Issues

Enable caching:

```python
config = FactoryConfig(
    cache_dependency_analysis=True,  # Cache dependency results
    cache_type_conversions=True      # Cache conversions
)
```