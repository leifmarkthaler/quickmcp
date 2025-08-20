#!/usr/bin/env python
"""
QuickMCP Factory CLI - Generate MCP servers from Python code
"""

import argparse
import sys
from pathlib import Path

from .factory import MCPFactory, create_mcp_from_module, MissingDependencyError, print_dependency_report


def main():
    """Main entry point for mcp-factory CLI."""
    parser = argparse.ArgumentParser(
        description="Generate MCP servers from Python code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create MCP server from a Python file
  mcp-factory my_utils.py
  
  # Check dependencies before creating server
  mcp-factory my_utils.py --check-deps
  
  # Create with custom name
  mcp-factory my_utils.py --name "utils-server"
  
  # Include private functions
  mcp-factory my_utils.py --include-private
  
  # Ignore missing dependencies and try to load anyway
  mcp-factory my_utils.py --ignore-missing-deps
  
  # Export server info instead of running
  mcp-factory my_utils.py --info
  
  # Run on specific port (SSE mode)
  mcp-factory my_utils.py --transport sse --port 8080
        """
    )
    
    parser.add_argument(
        "module",
        help="Python module/file to convert to MCP server"
    )
    
    parser.add_argument(
        "--name",
        help="Server name (defaults to module name + '-mcp')"
    )
    
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Server version (default: 1.0.0)"
    )
    
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="Include private functions (starting with _)"
    )
    
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport type (default: stdio)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for SSE transport (default: 8080)"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show server info instead of running"
    )
    
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List all tools that would be created"
    )
    
    parser.add_argument(
        "--filter",
        help="Filter functions by pattern (e.g., 'calc*')"
    )
    
    parser.add_argument(
        "--exclude",
        help="Exclude functions by pattern (e.g., 'test_*')"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies before creating server"
    )
    
    parser.add_argument(
        "--ignore-missing-deps",
        action="store_true",
        help="Ignore missing dependencies and try to load anyway"
    )
    
    args = parser.parse_args()
    
    try:
        # Check dependencies first if requested
        if args.check_deps:
            print_dependency_report(args.module)
            return 0
        
        # Create the factory
        check_dependencies = not args.ignore_missing_deps
        factory = MCPFactory(name=args.name, version=args.version, check_dependencies=check_dependencies)
        
        # Create server from module
        server = factory.from_module(
            args.module,
            include_private=args.include_private
        )
        
        # Apply filters if specified
        if args.filter or args.exclude:
            import fnmatch
            original_tools = server._tools.copy()
            
            for tool_name in list(server._tools.keys()):
                # Apply include filter
                if args.filter and not fnmatch.fnmatch(tool_name, args.filter):
                    del server._tools[tool_name]
                    if tool_name in server._tool_metadata:
                        del server._tool_metadata[tool_name]
                
                # Apply exclude filter
                if args.exclude and fnmatch.fnmatch(tool_name, args.exclude):
                    if tool_name in server._tools:
                        del server._tools[tool_name]
                    if tool_name in server._tool_metadata:
                        del server._tool_metadata[tool_name]
        
        # Handle info/list modes
        if args.info or args.list_tools:
            print(f"Server: {server.name}")
            print(f"Version: {server.version}")
            print(f"Description: {server.description}")
            print(f"Tools: {len(server.list_tools())}")
            
            if args.list_tools:
                print("\nAvailable tools:")
                for tool_name in sorted(server.list_tools()):
                    tool_func = server._tools.get(tool_name)
                    if tool_func and tool_func.__doc__:
                        desc = tool_func.__doc__.strip().split('\n')[0]
                        print(f"  - {tool_name}: {desc}")
                    else:
                        print(f"  - {tool_name}")
            
            return 0
        
        # Run the server
        print(f"Starting MCP server '{server.name}' with {len(server.list_tools())} tools")
        print(f"Transport: {args.transport}")
        
        if args.transport == "sse":
            print(f"URL: http://localhost:{args.port}/sse")
            server.run(transport="sse", port=args.port)
        else:
            print("Running in stdio mode...")
            server.run(transport="stdio")
        
    except KeyboardInterrupt:
        print("\nShutdown requested")
        return 0
    except MissingDependencyError as e:
        print("❌ Missing Dependencies Detected:", file=sys.stderr)
        print(e.format_error_message(), file=sys.stderr)
        print("\n💡 Tip: Use --ignore-missing-deps to try loading anyway", file=sys.stderr)
        print("💡 Tip: Use --check-deps to analyze dependencies without loading", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())