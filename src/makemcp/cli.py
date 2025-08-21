#!/usr/bin/env python
"""
MakeMCP CLI - Command line interface for MakeMCP
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional, List

from .registry import ServerRegistry, ServerRegistration, register_server
from .autodiscovery import discover_servers


def cmd_register(args):
    """Register a MakeMCP server."""
    command = args.command.split() if isinstance(args.command, str) else args.command
    
    register_server(
        name=args.name,
        command=command,
        description=args.description or "",
        working_dir=args.working_dir,
        tool_prefix=args.tool_prefix
    )
    print(f"✓ Registered server: {args.name}")


def cmd_unregister(args):
    """Unregister a MakeMCP server."""
    registry = ServerRegistry()
    if registry.unregister(args.name):
        print(f"✓ Unregistered server: {args.name}")
    else:
        print(f"✗ Server not found: {args.name}")
        sys.exit(1)


def cmd_list(args):
    """List registered MakeMCP servers."""
    registry = ServerRegistry()
    servers = registry.list()
    
    if not servers:
        print("No servers registered.")
        return
    
    print(f"Registered MakeMCP servers ({len(servers)}):")
    print("-" * 60)
    
    for server in servers:
        print(f"\n{server.name}")
        print(f"  Description: {server.description}")
        print(f"  Command: {' '.join(server.command)}")
        if server.working_dir:
            print(f"  Working Dir: {server.working_dir}")
        if server.tool_prefix:
            print(f"  Tool Prefix: {server.tool_prefix}")
        if server.capabilities:
            tools = server.capabilities.get("tools", [])
            resources = server.capabilities.get("resources", [])
            prompts = server.capabilities.get("prompts", [])
            if tools:
                print(f"  Tools: {', '.join(tools[:3])}{' ...' if len(tools) > 3 else ''}")
            if resources:
                print(f"  Resources: {', '.join(resources[:3])}{' ...' if len(resources) > 3 else ''}")
            if prompts:
                print(f"  Prompts: {', '.join(prompts[:3])}{' ...' if len(prompts) > 3 else ''}")


def cmd_discover(args):
    """Discover MakeMCP servers."""
    print("Discovering MakeMCP servers...")
    
    # Discover in filesystem
    if args.scan_filesystem:
        registry = ServerRegistry()
        search_paths = [Path(p) for p in args.paths] if args.paths else None
        discovered = registry.auto_discover(search_paths)
        
        print(f"\nFound {len(discovered)} servers in filesystem:")
        for server in discovered:
            print(f"  - {server.name}: {server.description}")
            if args.auto_register:
                registry.register(server)
                print(f"    ✓ Registered")
    
    # Discover on network
    if args.scan_network:
        import asyncio
        
        async def discover():
            return await discover_servers(timeout=args.timeout)
        
        network_servers = asyncio.run(discover())
        
        print(f"\nFound {len(network_servers)} servers on network:")
        for server in network_servers:
            print(f"  - {server.name} ({server.transport})")
            print(f"    Host: {server.host}:{server.port}")
            print(f"    Description: {server.description}")


def cmd_export(args):
    """Export registry as Gleitzeit configuration."""
    registry = ServerRegistry()
    config = registry.to_gleitzeit_config()
    
    if args.format == "yaml":
        import yaml
        output = yaml.dump(config, default_flow_style=False)
    else:
        output = json.dumps(config, indent=2)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"✓ Exported configuration to {args.output}")
    else:
        print(output)


def cmd_info(args):
    """Show information about a registered server."""
    registry = ServerRegistry()
    server = registry.get(args.name)
    
    if not server:
        print(f"✗ Server not found: {args.name}")
        sys.exit(1)
    
    print(f"Server: {server.name}")
    print(f"Description: {server.description}")
    print(f"Command: {' '.join(server.command)}")
    
    if server.working_dir:
        print(f"Working Directory: {server.working_dir}")
    
    if server.tool_prefix:
        print(f"Tool Prefix: {server.tool_prefix}")
    
    if server.capabilities:
        print("\nCapabilities:")
        for key, value in server.capabilities.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} items")
                for item in value[:5]:
                    print(f"    - {item}")
                if len(value) > 5:
                    print(f"    ... and {len(value) - 5} more")
            else:
                print(f"  {key}: {value}")
    
    if server.metadata:
        print("\nMetadata:")
        for key, value in server.metadata.items():
            print(f"  {key}: {value}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MakeMCP CLI - Manage and discover MCP servers"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Register command
    register_parser = subparsers.add_parser("register", help="Register a server")
    register_parser.add_argument("name", help="Server name")
    register_parser.add_argument("command", help="Command to run the server")
    register_parser.add_argument("-d", "--description", help="Server description")
    register_parser.add_argument("-w", "--working-dir", help="Working directory")
    register_parser.add_argument("-p", "--tool-prefix", help="Tool prefix for Gleitzeit")
    register_parser.set_defaults(func=cmd_register)
    
    # Unregister command
    unregister_parser = subparsers.add_parser("unregister", help="Unregister a server")
    unregister_parser.add_argument("name", help="Server name")
    unregister_parser.set_defaults(func=cmd_unregister)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List registered servers")
    list_parser.set_defaults(func=cmd_list)
    
    # Discover command
    discover_parser = subparsers.add_parser("discover", help="Discover servers")
    discover_parser.add_argument(
        "--scan-filesystem", action="store_true",
        help="Scan filesystem for MakeMCP servers"
    )
    discover_parser.add_argument(
        "--scan-network", action="store_true",
        help="Scan network for running servers"
    )
    discover_parser.add_argument(
        "--auto-register", action="store_true",
        help="Automatically register discovered servers"
    )
    discover_parser.add_argument(
        "--paths", nargs="+",
        help="Paths to search for servers"
    )
    discover_parser.add_argument(
        "--timeout", type=float, default=5.0,
        help="Network discovery timeout in seconds"
    )
    discover_parser.set_defaults(func=cmd_discover)
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export configuration")
    export_parser.add_argument(
        "-o", "--output", help="Output file (defaults to stdout)"
    )
    export_parser.add_argument(
        "-f", "--format", choices=["json", "yaml"], default="yaml",
        help="Output format"
    )
    export_parser.set_defaults(func=cmd_export)
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show server information")
    info_parser.add_argument("name", help="Server name")
    info_parser.set_defaults(func=cmd_info)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()