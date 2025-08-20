"""
QuickMCP Server Registry - Register and discover QuickMCP servers
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import subprocess
import sys


@dataclass
class ServerRegistration:
    """Registration info for a QuickMCP server."""
    name: str
    description: str
    command: List[str]  # Command to run the server
    working_dir: Optional[str] = None
    tool_prefix: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServerRegistration":
        """Create from dictionary."""
        return cls(**data)


class ServerRegistry:
    """Registry for QuickMCP servers that can be launched via stdio."""
    
    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize the server registry.
        
        Args:
            registry_path: Path to registry file (defaults to ~/.quickmcp/registry.json)
        """
        if registry_path is None:
            home = Path.home()
            registry_dir = home / ".quickmcp"
            registry_dir.mkdir(exist_ok=True)
            registry_path = registry_dir / "registry.json"
        
        self.registry_path = Path(registry_path)
        self.servers: Dict[str, ServerRegistration] = {}
        self.load()
    
    def load(self) -> None:
        """Load the registry from disk."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    self.servers = {
                        name: ServerRegistration.from_dict(info)
                        for name, info in data.items()
                    }
            except Exception as e:
                print(f"Warning: Could not load registry: {e}", file=sys.stderr)
                self.servers = {}
        else:
            self.servers = {}
    
    def save(self) -> None:
        """Save the registry to disk."""
        try:
            with open(self.registry_path, 'w') as f:
                data = {
                    name: server.to_dict()
                    for name, server in self.servers.items()
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save registry: {e}", file=sys.stderr)
    
    def register(self, server: ServerRegistration) -> None:
        """
        Register a server.
        
        Args:
            server: Server registration info
        """
        self.servers[server.name] = server
        self.save()
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a server.
        
        Args:
            name: Server name
            
        Returns:
            True if server was unregistered, False if not found
        """
        if name in self.servers:
            del self.servers[name]
            self.save()
            return True
        return False
    
    def get(self, name: str) -> Optional[ServerRegistration]:
        """
        Get a server registration.
        
        Args:
            name: Server name
            
        Returns:
            Server registration or None if not found
        """
        return self.servers.get(name)
    
    def list(self) -> List[ServerRegistration]:
        """
        List all registered servers.
        
        Returns:
            List of server registrations
        """
        return list(self.servers.values())
    
    def to_gleitzeit_config(self) -> Dict[str, Any]:
        """
        Convert registry to Gleitzeit MCP configuration format.
        
        Returns:
            Configuration dictionary for Gleitzeit
        """
        servers = []
        for server in self.servers.values():
            config = {
                "name": server.name,
                "connection_type": "stdio",
                "command": server.command,
                "auto_start": True,
            }
            
            if server.working_dir:
                config["working_dir"] = server.working_dir
            
            if server.tool_prefix:
                config["tool_prefix"] = server.tool_prefix
            
            if server.metadata:
                config.update(server.metadata)
            
            servers.append(config)
        
        return {
            "mcp": {
                "auto_discover": True,
                "servers": servers
            }
        }
    
    def auto_discover(self, search_paths: Optional[List[Path]] = None) -> List[ServerRegistration]:
        """
        Auto-discover QuickMCP servers in the filesystem.
        
        Args:
            search_paths: Paths to search (defaults to current directory and common locations)
            
        Returns:
            List of discovered servers
        """
        if search_paths is None:
            search_paths = [
                Path.cwd(),
                Path.home() / "quickmcp",
                Path.home() / "mcp-servers",
                Path("/usr/local/share/quickmcp"),
            ]
        
        discovered = []
        
        for base_path in search_paths:
            if not base_path.exists():
                continue
            
            # Look for Python files that might be QuickMCP servers
            for py_file in base_path.rglob("*.py"):
                if self._is_quickmcp_server(py_file):
                    # Extract server info from the file
                    info = self._extract_server_info(py_file)
                    if info:
                        discovered.append(info)
        
        return discovered
    
    def _is_quickmcp_server(self, file_path: Path) -> bool:
        """Check if a Python file is a QuickMCP server."""
        try:
            with open(file_path, 'r') as f:
                content = f.read(1000)  # Read first 1000 chars
                return "QuickMCPServer" in content or "from quickmcp import" in content
        except:
            return False
    
    def _extract_server_info(self, file_path: Path) -> Optional[ServerRegistration]:
        """Extract server information from a Python file."""
        try:
            # Try to run the file with --info flag to get metadata
            result = subprocess.run(
                [sys.executable, str(file_path), "--info"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                # Parse JSON output
                info = json.loads(result.stdout)
                return ServerRegistration(
                    name=info.get("name", file_path.stem),
                    description=info.get("description", ""),
                    command=[sys.executable, str(file_path)],
                    working_dir=str(file_path.parent),
                    capabilities=info.get("capabilities"),
                    metadata=info.get("metadata")
                )
        except:
            pass
        
        # Fallback: create basic registration
        return ServerRegistration(
            name=file_path.stem,
            description=f"QuickMCP server: {file_path.name}",
            command=[sys.executable, str(file_path)],
            working_dir=str(file_path.parent)
        )


def register_server(
    name: str,
    command: List[str],
    description: str = "",
    working_dir: Optional[str] = None,
    tool_prefix: Optional[str] = None,
    **metadata
) -> None:
    """
    Convenience function to register a server.
    
    Args:
        name: Server name
        command: Command to run the server
        description: Server description
        working_dir: Working directory
        tool_prefix: Tool prefix for Gleitzeit
        **metadata: Additional metadata
    """
    registry = ServerRegistry()
    server = ServerRegistration(
        name=name,
        description=description,
        command=command,
        working_dir=working_dir,
        tool_prefix=tool_prefix,
        metadata=metadata if metadata else None
    )
    registry.register(server)
    print(f"Registered server: {name}")


def list_servers() -> List[ServerRegistration]:
    """
    List all registered servers.
    
    Returns:
        List of server registrations
    """
    registry = ServerRegistry()
    return registry.list()


def export_gleitzeit_config(output_path: Optional[Path] = None) -> None:
    """
    Export registry as Gleitzeit configuration.
    
    Args:
        output_path: Output path (defaults to stdout)
    """
    registry = ServerRegistry()
    config = registry.to_gleitzeit_config()
    
    import yaml
    yaml_str = yaml.dump(config, default_flow_style=False)
    
    if output_path:
        with open(output_path, 'w') as f:
            f.write(yaml_str)
        print(f"Exported configuration to {output_path}")
    else:
        print(yaml_str)