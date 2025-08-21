#!/usr/bin/env python
"""
Discovery client for finding QuickMCP servers on the network.

This tool listens for MCP server announcements and displays
discovered servers in real-time.
"""

import asyncio
import json
from datetime import datetime
from mcplite.autodiscovery import DiscoveryListener, discover_servers
import argparse
import logging


def format_server_info(server_info):
    """Format server information for display."""
    lines = [
        "\n" + "=" * 60,
        f"🔍 Discovered MCP Server",
        "=" * 60,
        f"Name:        {server_info.name}",
        f"Version:     {server_info.version}",
        f"Description: {server_info.description}",
        f"ID:          {server_info.id[:8]}...",
        f"Transport:   {server_info.transport}",
    ]
    
    if server_info.transport != "stdio":
        lines.append(f"Host:        {server_info.host}")
        lines.append(f"Port:        {server_info.port}")
        lines.append(f"URL:         http://{server_info.host}:{server_info.port}")
    else:
        lines.append(f"Host:        {server_info.host}")
    
    if server_info.capabilities:
        caps = server_info.capabilities
        lines.append(f"\nCapabilities:")
        if "tool_count" in caps:
            lines.append(f"  Tools:     {caps['tool_count']}")
        if "resource_count" in caps:
            lines.append(f"  Resources: {caps['resource_count']}")
        if "prompt_count" in caps:
            lines.append(f"  Prompts:   {caps['prompt_count']}")
    
    if server_info.metadata:
        lines.append(f"\nMetadata:")
        for key, value in server_info.metadata.items():
            lines.append(f"  {key}: {value}")
    
    timestamp = datetime.fromtimestamp(server_info.timestamp)
    lines.append(f"\nLast seen:   {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    
    return "\n".join(lines)


async def discover_once(timeout: float = 5.0):
    """Discover servers once and display them."""
    print(f"🔍 Discovering MCP servers for {timeout} seconds...")
    
    servers = await discover_servers(timeout=timeout)
    
    if not servers:
        print("\n❌ No MCP servers discovered on the network")
        print("\nMake sure:")
        print("  - QuickMCP servers are running with autodiscovery enabled")
        print("  - Firewall allows UDP port 42424")
        print("  - You're on the same network as the servers")
    else:
        print(f"\n✅ Found {len(servers)} server(s):")
        for server_info in servers:
            print(format_server_info(server_info))


def continuous_discovery():
    """Continuously discover and monitor servers."""
    print("🔍 Continuously monitoring for MCP servers...")
    print("Press Ctrl+C to stop\n")
    
    discovered = set()
    
    def on_discovered(server_info):
        """Callback when a new server is discovered."""
        if server_info.id not in discovered:
            discovered.add(server_info.id)
            print(format_server_info(server_info))
            print(f"\n📊 Total servers discovered: {len(discovered)}")
    
    listener = DiscoveryListener(callback=on_discovered)
    listener.start()
    
    try:
        while True:
            # Periodically show active servers
            import time
            time.sleep(10)
            
            active_servers = listener.get_servers()
            if active_servers:
                print(f"\n📊 Active servers: {len(active_servers)}")
                for server in active_servers:
                    print(f"  - {server.name} ({server.transport})")
    except KeyboardInterrupt:
        print("\n\nStopping discovery...")
    finally:
        listener.stop()


def export_servers(output_file: str, timeout: float = 5.0):
    """Export discovered servers to JSON file."""
    print(f"🔍 Discovering servers for {timeout} seconds...")
    
    async def discover_and_export():
        servers = await discover_servers(timeout=timeout)
        
        if not servers:
            print("❌ No servers discovered")
            return
        
        # Convert to serializable format
        server_data = []
        for server in servers:
            server_dict = {
                "id": server.id,
                "name": server.name,
                "version": server.version,
                "description": server.description,
                "host": server.host,
                "port": server.port,
                "transport": server.transport,
                "capabilities": server.capabilities,
                "metadata": server.metadata,
                "timestamp": server.timestamp
            }
            server_data.append(server_dict)
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(server_data, f, indent=2)
        
        print(f"✅ Exported {len(servers)} server(s) to {output_file}")
    
    asyncio.run(discover_and_export())


def main():
    parser = argparse.ArgumentParser(
        description="Discover QuickMCP servers on the network"
    )
    parser.add_argument(
        "mode", 
        nargs="?",
        default="once",
        choices=["once", "continuous", "export"],
        help="Discovery mode (default: once)"
    )
    parser.add_argument(
        "--timeout", 
        type=float, 
        default=5.0,
        help="Discovery timeout in seconds (default: 5.0)"
    )
    parser.add_argument(
        "--output", 
        default="discovered_servers.json",
        help="Output file for export mode (default: discovered_servers.json)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s - %(message)s"
        )
    
    print("=" * 60)
    print("QuickMCP Server Discovery Tool")
    print("=" * 60)
    
    if args.mode == "once":
        asyncio.run(discover_once(timeout=args.timeout))
    elif args.mode == "continuous":
        continuous_discovery()
    elif args.mode == "export":
        export_servers(args.output, timeout=args.timeout)


if __name__ == "__main__":
    main()