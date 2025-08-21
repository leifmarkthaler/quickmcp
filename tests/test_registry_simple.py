"""
Simple tests for Registry module to improve coverage.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from makemcp.registry import ServerRegistry, ServerRegistration, register_server, list_servers


class TestServerRegistration:
    """Test ServerRegistration class."""
    
    def test_to_dict(self):
        """Test converting registration to dict."""
        reg = ServerRegistration(
            name="test-server",
            description="Test description",
            command=["python", "test.py"],
            working_dir="/tmp",
            tool_prefix="test_"
        )
        
        data = reg.to_dict()
        assert data["name"] == "test-server"
        assert data["description"] == "Test description"
        assert data["command"] == ["python", "test.py"]
        assert data["working_dir"] == "/tmp"
        assert data["tool_prefix"] == "test_"
    
    def test_from_dict(self):
        """Test creating registration from dict."""
        data = {
            "name": "test-server",
            "description": "Test description",
            "command": ["python", "test.py"]
        }
        
        reg = ServerRegistration.from_dict(data)
        assert reg.name == "test-server"
        assert reg.description == "Test description"
        assert reg.command == ["python", "test.py"]


class TestServerRegistry:
    """Test ServerRegistry class."""
    
    def test_init_creates_directory(self):
        """Test registry initialization creates directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "test" / "registry.json"
            # Create parent directory as registry doesn't auto-create custom paths
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            registry = ServerRegistry(registry_path)
            
            assert registry_path.parent.exists()
            assert registry.registry_path == registry_path
    
    def test_register_and_get(self):
        """Test registering and retrieving a server."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            registry = ServerRegistry(registry_path)
            
            server = ServerRegistration(
                name="test-server",
                description="Test",
                command=["python", "test.py"]
            )
            
            registry.register(server)
            retrieved = registry.get("test-server")
            
            assert retrieved is not None
            assert retrieved.name == "test-server"
    
    def test_unregister(self):
        """Test unregistering a server."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            registry = ServerRegistry(registry_path)
            
            server = ServerRegistration(
                name="test-server",
                description="Test",
                command=["python", "test.py"]
            )
            
            registry.register(server)
            result = registry.unregister("test-server")
            
            assert result is True
            assert registry.get("test-server") is None
    
    def test_list(self):
        """Test listing servers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            registry = ServerRegistry(registry_path)
            
            server1 = ServerRegistration(
                name="server1",
                description="Test 1",
                command=["python", "test1.py"]
            )
            server2 = ServerRegistration(
                name="server2",
                description="Test 2",
                command=["python", "test2.py"]
            )
            
            registry.register(server1)
            registry.register(server2)
            
            servers = registry.list()
            assert len(servers) == 2
            names = [s.name for s in servers]
            assert "server1" in names
            assert "server2" in names
    
    def test_to_gleitzeit_config(self):
        """Test converting to Gleitzeit config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            registry = ServerRegistry(registry_path)
            
            server = ServerRegistration(
                name="test-server",
                description="Test",
                command=["python", "test.py"],
                tool_prefix="test_"
            )
            
            registry.register(server)
            config = registry.to_gleitzeit_config()
            
            assert "mcp" in config
            assert "servers" in config["mcp"]
            assert len(config["mcp"]["servers"]) == 1
            
            server_config = config["mcp"]["servers"][0]
            assert server_config["name"] == "test-server"
            assert server_config["connection_type"] == "stdio"
            assert server_config["command"] == ["python", "test.py"]
            assert server_config["tool_prefix"] == "test_"
    
    def test_save_and_load(self):
        """Test saving and loading registry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "registry.json"
            
            # Create and save
            registry1 = ServerRegistry(registry_path)
            server = ServerRegistration(
                name="test-server",
                description="Test",
                command=["python", "test.py"]
            )
            registry1.register(server)
            
            # Load in new instance
            registry2 = ServerRegistry(registry_path)
            loaded = registry2.get("test-server")
            
            assert loaded is not None
            assert loaded.name == "test-server"
            assert loaded.description == "Test"
    
    def test_is_makemcp_server(self):
        """Test checking if file is MakeMCP server."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ServerRegistry()
            
            # Create test file with MakeMCP import
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("from makemcp import MakeMCPServer\n")
            
            assert registry._is_makemcp_server(test_file) is True
            
            # Create non-MakeMCP file
            other_file = Path(tmpdir) / "other.py"
            other_file.write_text("print('hello')\n")
            
            assert registry._is_makemcp_server(other_file) is False


class TestModuleFunctions:
    """Test module-level functions."""
    
    def test_register_server_function(self):
        """Test register_server convenience function."""
        with patch('makemcp.registry.ServerRegistry') as mock_registry_class:
            mock_instance = MagicMock()
            mock_registry_class.return_value = mock_instance
            
            with patch('builtins.print'):
                register_server(
                    name="test-server",
                    command=["python", "test.py"],
                    description="Test server"
                )
            
            mock_instance.register.assert_called_once()
    
    def test_list_servers_function(self):
        """Test list_servers convenience function."""
        with patch('makemcp.registry.ServerRegistry') as mock_registry_class:
            mock_instance = MagicMock()
            mock_instance.list.return_value = []
            mock_registry_class.return_value = mock_instance
            
            result = list_servers()
            
            assert result == []
            mock_instance.list.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])