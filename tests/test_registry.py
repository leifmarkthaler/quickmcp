"""
Test suite for QuickMCP Registry
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys

from quickmcp.registry import (
    ServerRegistration,
    ServerRegistry,
    register_server,
    list_servers,
    export_gleitzeit_config
)


class TestServerRegistration:
    """Test ServerRegistration dataclass."""
    
    def test_basic_registration(self):
        """Test creating basic registration."""
        reg = ServerRegistration(
            name="test-server",
            description="Test server",
            command=["python", "server.py"]
        )
        
        assert reg.name == "test-server"
        assert reg.description == "Test server"
        assert reg.command == ["python", "server.py"]
        assert reg.working_dir is None
        assert reg.tool_prefix is None
    
    def test_full_registration(self):
        """Test registration with all fields."""
        reg = ServerRegistration(
            name="full-server",
            description="Full test server",
            command=["python", "server.py"],
            working_dir="/path/to/dir",
            tool_prefix="test.",
            capabilities={"tools": ["tool1", "tool2"]},
            metadata={"author": "Test Author"}
        )
        
        assert reg.working_dir == "/path/to/dir"
        assert reg.tool_prefix == "test."
        assert reg.capabilities == {"tools": ["tool1", "tool2"]}
        assert reg.metadata == {"author": "Test Author"}
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        reg = ServerRegistration(
            name="test",
            description="desc",
            command=["cmd"],
            tool_prefix="prefix."
        )
        
        data = reg.to_dict()
        
        assert data["name"] == "test"
        assert data["description"] == "desc"
        assert data["command"] == ["cmd"]
        assert data["tool_prefix"] == "prefix."
        assert "working_dir" not in data  # None values excluded
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "name": "test",
            "description": "desc",
            "command": ["cmd"],
            "tool_prefix": "prefix."
        }
        
        reg = ServerRegistration.from_dict(data)
        
        assert reg.name == "test"
        assert reg.description == "desc"
        assert reg.command == ["cmd"]
        assert reg.tool_prefix == "prefix."


class TestServerRegistry:
    """Test ServerRegistry class."""
    
    def test_registry_initialization(self, tmp_path):
        """Test registry initialization."""
        registry_file = tmp_path / "registry.json"
        registry = ServerRegistry(registry_path=registry_file)
        
        assert registry.registry_path == registry_file
        assert len(registry.servers) == 0
    
    def test_registry_default_path(self):
        """Test registry with default path."""
        with patch.dict(os.environ, {"HOME": "/home/test"}):
            with patch("pathlib.Path.mkdir"):
                with patch("pathlib.Path.exists", return_value=False):
                    registry = ServerRegistry()
                    expected_path = Path("/home/test/.quickmcp/registry.json")
                    assert str(registry.registry_path) == str(expected_path)
    
    def test_register_server(self, tmp_path):
        """Test registering a server."""
        registry_file = tmp_path / "registry.json"
        registry = ServerRegistry(registry_path=registry_file)
        
        server = ServerRegistration(
            name="test-server",
            description="Test",
            command=["python", "server.py"]
        )
        
        registry.register(server)
        
        assert "test-server" in registry.servers
        assert registry.servers["test-server"].description == "Test"
        
        # Check file was saved
        assert registry_file.exists()
        with open(registry_file) as f:
            data = json.load(f)
            assert "test-server" in data
    
    def test_unregister_server(self, tmp_path):
        """Test unregistering a server."""
        registry_file = tmp_path / "registry.json"
        registry = ServerRegistry(registry_path=registry_file)
        
        server = ServerRegistration(
            name="test-server",
            description="Test",
            command=["cmd"]
        )
        
        registry.register(server)
        assert "test-server" in registry.servers
        
        result = registry.unregister("test-server")
        assert result is True
        assert "test-server" not in registry.servers
        
        # Try unregistering non-existent
        result = registry.unregister("nonexistent")
        assert result is False
    
    def test_get_server(self, tmp_path):
        """Test getting a server registration."""
        registry_file = tmp_path / "registry.json"
        registry = ServerRegistry(registry_path=registry_file)
        
        server = ServerRegistration(
            name="test-server",
            description="Test",
            command=["cmd"]
        )
        
        registry.register(server)
        
        retrieved = registry.get("test-server")
        assert retrieved is not None
        assert retrieved.name == "test-server"
        
        none_server = registry.get("nonexistent")
        assert none_server is None
    
    def test_list_servers(self, tmp_path):
        """Test listing all servers."""
        registry_file = tmp_path / "registry.json"
        registry = ServerRegistry(registry_path=registry_file)
        
        # Register multiple servers
        for i in range(3):
            server = ServerRegistration(
                name=f"server-{i}",
                description=f"Server {i}",
                command=["cmd"]
            )
            registry.register(server)
        
        servers = registry.list()
        assert len(servers) == 3
        
        names = [s.name for s in servers]
        assert "server-0" in names
        assert "server-1" in names
        assert "server-2" in names
    
    def test_load_existing_registry(self, tmp_path):
        """Test loading existing registry file."""
        registry_file = tmp_path / "registry.json"
        
        # Create registry file manually
        data = {
            "existing-server": {
                "name": "existing-server",
                "description": "Existing",
                "command": ["python", "existing.py"]
            }
        }
        
        with open(registry_file, 'w') as f:
            json.dump(data, f)
        
        # Load registry
        registry = ServerRegistry(registry_path=registry_file)
        
        assert "existing-server" in registry.servers
        assert registry.servers["existing-server"].description == "Existing"
    
    def test_load_corrupted_registry(self, tmp_path):
        """Test loading corrupted registry file."""
        registry_file = tmp_path / "registry.json"
        
        # Create corrupted file
        with open(registry_file, 'w') as f:
            f.write("not valid json{")
        
        # Should handle gracefully
        registry = ServerRegistry(registry_path=registry_file)
        assert len(registry.servers) == 0
    
    def test_to_gleitzeit_config(self, tmp_path):
        """Test converting to Gleitzeit configuration."""
        registry_file = tmp_path / "registry.json"
        registry = ServerRegistry(registry_path=registry_file)
        
        # Register servers
        server1 = ServerRegistration(
            name="server1",
            description="Server 1",
            command=["python", "server1.py"],
            tool_prefix="s1.",
            working_dir="/path/to/server1"
        )
        
        server2 = ServerRegistration(
            name="server2",
            description="Server 2",
            command=["python", "server2.py"],
            metadata={"custom": "value"}
        )
        
        registry.register(server1)
        registry.register(server2)
        
        config = registry.to_gleitzeit_config()
        
        assert "mcp" in config
        assert config["mcp"]["auto_discover"] is True
        assert len(config["mcp"]["servers"]) == 2
        
        # Check server 1
        s1_config = next(s for s in config["mcp"]["servers"] if s["name"] == "server1")
        assert s1_config["connection_type"] == "stdio"
        assert s1_config["command"] == ["python", "server1.py"]
        assert s1_config["tool_prefix"] == "s1."
        assert s1_config["working_dir"] == "/path/to/server1"
        
        # Check server 2
        s2_config = next(s for s in config["mcp"]["servers"] if s["name"] == "server2")
        assert s2_config["custom"] == "value"


class TestAutoDiscovery:
    """Test auto-discovery functionality."""
    
    def test_is_quickmcp_server(self, tmp_path):
        """Test detecting QuickMCP servers."""
        registry = ServerRegistry()
        
        # Create QuickMCP server file
        server_file = tmp_path / "mcp_server.py"
        server_file.write_text("""
from quickmcp import QuickMCPServer

server = QuickMCPServer("test")
""")
        
        assert registry._is_quickmcp_server(server_file) is True
        
        # Create non-MCP file
        other_file = tmp_path / "other.py"
        other_file.write_text("""
def main():
    print("Hello")
""")
        
        assert registry._is_quickmcp_server(other_file) is False
    
    def test_extract_server_info_with_info_flag(self, tmp_path):
        """Test extracting server info via --info flag."""
        server_file = tmp_path / "server.py"
        server_file.write_text("""
import sys
import json

if "--info" in sys.argv:
    info = {
        "name": "test-server",
        "description": "Test server",
        "capabilities": {"tools": ["tool1", "tool2"]}
    }
    print(json.dumps(info))
    sys.exit(0)
""")
        
        registry = ServerRegistry()
        info = registry._extract_server_info(server_file)
        
        assert info is not None
        assert info.name == "test-server"
        assert info.description == "Test server"
        assert info.capabilities == {"tools": ["tool1", "tool2"]}
    
    def test_extract_server_info_fallback(self, tmp_path):
        """Test fallback when --info doesn't work."""
        server_file = tmp_path / "server.py"
        server_file.write_text("""
# QuickMCP server without --info support
from quickmcp import QuickMCPServer
""")
        
        registry = ServerRegistry()
        
        with patch('subprocess.run') as mock_run:
            # Simulate failure
            mock_run.return_value = MagicMock(returncode=1)
            
            info = registry._extract_server_info(server_file)
            
            assert info is not None
            assert info.name == "server"  # From filename
            assert "server.py" in info.description
    
    def test_auto_discover(self, tmp_path):
        """Test auto-discovering servers."""
        # Create test directory structure
        servers_dir = tmp_path / "servers"
        servers_dir.mkdir()
        
        # Create QuickMCP server
        (servers_dir / "mcp1.py").write_text("""
from quickmcp import QuickMCPServer
server = QuickMCPServer("mcp1")
""")
        
        # Create another server
        (servers_dir / "mcp2.py").write_text("""
from quickmcp import QuickMCPServer
server = QuickMCPServer("mcp2")
""")
        
        # Create non-MCP file
        (servers_dir / "util.py").write_text("""
def utility():
    pass
""")
        
        registry = ServerRegistry()
        
        # Mock the extract_server_info to avoid subprocess calls
        def mock_extract(path):
            return ServerRegistration(
                name=path.stem,
                description=f"Server from {path.name}",
                command=["python", str(path)]
            )
        
        with patch.object(registry, '_extract_server_info', side_effect=mock_extract):
            discovered = registry.auto_discover([servers_dir])
        
        assert len(discovered) == 2
        
        names = [s.name for s in discovered]
        assert "mcp1" in names
        assert "mcp2" in names


class TestHelperFunctions:
    """Test module-level helper functions."""
    
    def test_register_server_function(self, tmp_path):
        """Test register_server helper function."""
        with patch('quickmcp.registry.ServerRegistry') as MockRegistry:
            mock_instance = MagicMock()
            MockRegistry.return_value = mock_instance
            
            register_server(
                name="test",
                command=["python", "test.py"],
                description="Test server",
                tool_prefix="test."
            )
            
            # Check that register was called
            mock_instance.register.assert_called_once()
            
            # Check the registration object
            call_args = mock_instance.register.call_args[0][0]
            assert call_args.name == "test"
            assert call_args.command == ["python", "test.py"]
            assert call_args.description == "Test server"
            assert call_args.tool_prefix == "test."
    
    def test_list_servers_function(self):
        """Test list_servers helper function."""
        with patch('quickmcp.registry.ServerRegistry') as MockRegistry:
            mock_instance = MagicMock()
            mock_instance.list.return_value = [
                ServerRegistration("s1", "Server 1", ["cmd1"]),
                ServerRegistration("s2", "Server 2", ["cmd2"])
            ]
            MockRegistry.return_value = mock_instance
            
            servers = list_servers()
            
            assert len(servers) == 2
            assert servers[0].name == "s1"
            assert servers[1].name == "s2"
    
    @patch('builtins.print')
    def test_export_gleitzeit_config_to_stdout(self, mock_print):
        """Test exporting config to stdout."""
        with patch('quickmcp.registry.ServerRegistry') as MockRegistry:
            mock_instance = MagicMock()
            mock_instance.to_gleitzeit_config.return_value = {"mcp": {"servers": []}}
            MockRegistry.return_value = mock_instance
            
            with patch('yaml.dump', return_value="mcp:\n  servers: []"):
                export_gleitzeit_config()
            
            # Should print to stdout
            mock_print.assert_called_with("mcp:\n  servers: []")
    
    @patch('builtins.print')
    def test_export_gleitzeit_config_to_file(self, mock_print, tmp_path):
        """Test exporting config to file."""
        output_file = tmp_path / "config.yaml"
        
        with patch('quickmcp.registry.ServerRegistry') as MockRegistry:
            mock_instance = MagicMock()
            mock_instance.to_gleitzeit_config.return_value = {"mcp": {"servers": []}}
            MockRegistry.return_value = mock_instance
            
            with patch('yaml.dump', return_value="mcp:\n  servers: []"):
                export_gleitzeit_config(output_path=output_file)
                
                # Check file was created
                assert output_file.exists()
                
                # Check print message
                mock_print.assert_called_with(f"Exported configuration to {output_file}")


class TestIntegration:
    """Integration tests for registry system."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow of registry operations."""
        registry_file = tmp_path / "registry.json"
        
        # Create registry
        registry = ServerRegistry(registry_path=registry_file)
        
        # Register multiple servers
        servers_data = [
            ("server1", "Server One", ["python", "s1.py"], "s1."),
            ("server2", "Server Two", ["python", "s2.py"], "s2."),
            ("server3", "Server Three", ["python", "s3.py"], "s3.")
        ]
        
        for name, desc, cmd, prefix in servers_data:
            server = ServerRegistration(
                name=name,
                description=desc,
                command=cmd,
                tool_prefix=prefix
            )
            registry.register(server)
        
        # List servers
        servers = registry.list()
        assert len(servers) == 3
        
        # Get specific server
        server2 = registry.get("server2")
        assert server2.description == "Server Two"
        
        # Unregister one
        registry.unregister("server1")
        assert len(registry.list()) == 2
        
        # Export config
        config = registry.to_gleitzeit_config()
        assert len(config["mcp"]["servers"]) == 2
        
        # Reload registry from file
        new_registry = ServerRegistry(registry_path=registry_file)
        assert len(new_registry.list()) == 2
        assert new_registry.get("server1") is None
        assert new_registry.get("server2") is not None
    
    def test_concurrent_registry_access(self, tmp_path):
        """Test concurrent access to registry (basic test)."""
        registry_file = tmp_path / "registry.json"
        
        # Create first registry instance
        registry1 = ServerRegistry(registry_path=registry_file)
        
        # Register server
        server = ServerRegistration("test", "Test", ["cmd"])
        registry1.register(server)
        
        # Create second registry instance
        registry2 = ServerRegistry(registry_path=registry_file)
        
        # Should see the registered server
        assert registry2.get("test") is not None
        
        # Modify from second instance
        registry2.unregister("test")
        
        # Reload first instance
        registry1.load()
        assert registry1.get("test") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])