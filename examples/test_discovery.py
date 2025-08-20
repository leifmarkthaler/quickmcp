#!/usr/bin/env python
"""
Test the QuickMCP discovery system.
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickmcp import ServerRegistry, register_server, list_servers


def test_registration():
    """Test server registration."""
    print("Testing server registration...")
    
    # Register example servers
    register_server(
        name="example-math",
        command=["python", "examples/math_server.py"],
        description="Mathematical operations server",
        tool_prefix="math."
    )
    
    register_server(
        name="example-file",
        command=["python", "examples/file_server.py"],
        description="File system operations server",
        tool_prefix="file."
    )
    
    register_server(
        name="example-simple",
        command=["python", "examples/simple_server.py"],
        description="Simple example server",
        tool_prefix="simple."
    )
    
    print("✓ Registered 3 example servers")


def test_listing():
    """Test listing servers."""
    print("\nListing registered servers...")
    servers = list_servers()
    
    for server in servers:
        print(f"  - {server.name}: {server.description}")
        print(f"    Command: {' '.join(server.command)}")
        if server.tool_prefix:
            print(f"    Tool prefix: {server.tool_prefix}")


def test_export():
    """Test exporting to Gleitzeit config."""
    print("\nExporting Gleitzeit configuration...")
    
    registry = ServerRegistry()
    config = registry.to_gleitzeit_config()
    
    print("Generated config:")
    print("-" * 60)
    import yaml
    print(yaml.dump(config, default_flow_style=False))
    print("-" * 60)


def test_discovery():
    """Test filesystem discovery."""
    print("\nTesting filesystem discovery...")
    
    registry = ServerRegistry()
    search_paths = [Path(__file__).parent]  # Search in examples directory
    
    discovered = registry.auto_discover(search_paths)
    
    print(f"Discovered {len(discovered)} servers:")
    for server in discovered:
        print(f"  - {server.name}: {server.description}")


def main():
    """Run all tests."""
    print("QuickMCP Discovery System Test")
    print("=" * 60)
    
    test_registration()
    test_listing()
    test_export()
    test_discovery()
    
    print("\n" + "=" * 60)
    print("All tests completed!")


if __name__ == "__main__":
    main()