"""
Tests for QuickMCP autodiscovery functionality
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, MagicMock
from makemcp.autodiscovery import (
    ServerInfo,
    DiscoveryBroadcaster,
    DiscoveryListener,
    AutoDiscovery,
    discover_servers,
    MCP_DISCOVERY_MAGIC
)
from makemcp import MakeMCPServer


class TestServerInfo:
    """Test ServerInfo dataclass."""
    
    def test_create_server_info(self):
        """Test creating ServerInfo instance."""
        info = ServerInfo(
            id="test-id",
            name="test-server",
            version="1.0.0",
            description="Test server",
            host="localhost",
            port=8080,
            transport="sse",
            capabilities={"tools": ["test"]},
            metadata={"key": "value"},
            timestamp=time.time()
        )
        
        assert info.id == "test-id"
        assert info.name == "test-server"
        assert info.version == "1.0.0"
        assert info.transport == "sse"
        assert info.capabilities["tools"] == ["test"]
    
    def test_server_info_to_json(self):
        """Test converting ServerInfo to JSON."""
        info = ServerInfo(
            id="test-id",
            name="test-server",
            version="1.0.0",
            description="Test server",
            host="localhost",
            port=8080,
            transport="sse",
            capabilities={},
            metadata={},
            timestamp=1234567890.0
        )
        
        json_str = info.to_json()
        data = json.loads(json_str)
        
        assert data["id"] == "test-id"
        assert data["name"] == "test-server"
        assert data["timestamp"] == 1234567890.0
    
    def test_server_info_from_json(self):
        """Test creating ServerInfo from JSON."""
        json_str = json.dumps({
            "id": "test-id",
            "name": "test-server",
            "version": "1.0.0",
            "description": "Test server",
            "host": "localhost",
            "port": 8080,
            "transport": "sse",
            "capabilities": {"tools": ["test"]},
            "metadata": {"key": "value"},
            "timestamp": 1234567890.0
        })
        
        info = ServerInfo.from_json(json_str)
        
        assert info.id == "test-id"
        assert info.name == "test-server"
        assert info.capabilities["tools"] == ["test"]


class TestDiscoveryBroadcaster:
    """Test DiscoveryBroadcaster functionality."""
    
    def test_create_broadcaster(self):
        """Test creating DiscoveryBroadcaster."""
        info = ServerInfo(
            id="test-id",
            name="test-server",
            version="1.0.0",
            description="Test",
            host="localhost",
            port=8080,
            transport="sse",
            capabilities={},
            metadata={},
            timestamp=time.time()
        )
        
        broadcaster = DiscoveryBroadcaster(info)
        
        assert broadcaster.server_info == info
        assert broadcaster.port == 42424
        assert broadcaster.interval == 5.0
    
    @patch('socket.socket')
    def test_broadcaster_start_stop(self, mock_socket):
        """Test starting and stopping broadcaster."""
        info = ServerInfo(
            id="test-id",
            name="test-server",
            version="1.0.0",
            description="Test",
            host="localhost",
            port=8080,
            transport="sse",
            capabilities={},
            metadata={},
            timestamp=time.time()
        )
        
        broadcaster = DiscoveryBroadcaster(info, interval=0.1)
        
        # Mock socket
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        # Start broadcaster
        broadcaster.start()
        assert broadcaster._running
        
        # Give it time to broadcast
        time.sleep(0.2)
        
        # Stop broadcaster
        broadcaster.stop()
        assert not broadcaster._running
    
    def test_create_packet(self):
        """Test packet creation."""
        info = ServerInfo(
            id="test-id",
            name="test-server",
            version="1.0.0",
            description="Test",
            host="localhost",
            port=8080,
            transport="sse",
            capabilities={},
            metadata={},
            timestamp=1234567890.0
        )
        
        broadcaster = DiscoveryBroadcaster(info)
        packet = broadcaster._create_packet()
        
        assert packet.startswith(MCP_DISCOVERY_MAGIC)
        assert b"test-server" in packet


class TestDiscoveryListener:
    """Test DiscoveryListener functionality."""
    
    def test_create_listener(self):
        """Test creating DiscoveryListener."""
        callback = Mock()
        listener = DiscoveryListener(callback=callback)
        
        assert listener.callback == callback
        assert listener.port == 42424
        assert listener.timeout == 30.0
    
    def test_process_valid_packet(self):
        """Test processing a valid discovery packet."""
        discovered = []
        
        def callback(info):
            discovered.append(info)
        
        listener = DiscoveryListener(callback=callback)
        
        # Create a valid packet
        server_info = ServerInfo(
            id="test-id",
            name="test-server",
            version="1.0.0",
            description="Test",
            host="localhost",
            port=8080,
            transport="sse",
            capabilities={},
            metadata={},
            timestamp=time.time()
        )
        
        packet = MCP_DISCOVERY_MAGIC + b'\n' + server_info.to_json().encode('utf-8')
        
        # Process packet
        listener._process_packet(packet, ("127.0.0.1", 12345))
        
        # Check callback was called
        assert len(discovered) == 1
        assert discovered[0].name == "test-server"
    
    def test_process_invalid_packet(self):
        """Test processing an invalid packet."""
        discovered = []
        
        def callback(info):
            discovered.append(info)
        
        listener = DiscoveryListener(callback=callback)
        
        # Invalid packet (wrong magic)
        packet = b"INVALID" + b'\n' + b'{"name": "test"}'
        
        # Process packet - should be ignored
        listener._process_packet(packet, ("127.0.0.1", 12345))
        
        # Callback should not be called
        assert len(discovered) == 0
    
    def test_get_servers_removes_stale(self):
        """Test that get_servers removes stale entries."""
        listener = DiscoveryListener(timeout=1.0)
        
        # Add a server
        old_info = ServerInfo(
            id="old-server",
            name="old",
            version="1.0.0",
            description="Old",
            host="localhost",
            port=8080,
            transport="sse",
            capabilities={},
            metadata={},
            timestamp=time.time() - 2.0  # Old timestamp
        )
        
        new_info = ServerInfo(
            id="new-server",
            name="new",
            version="1.0.0",
            description="New",
            host="localhost",
            port=8081,
            transport="sse",
            capabilities={},
            metadata={},
            timestamp=time.time()  # Current timestamp
        )
        
        listener._servers = {
            "old-server": old_info,
            "new-server": new_info
        }
        
        # Get servers - should remove old one
        servers = listener.get_servers()
        
        assert len(servers) == 1
        assert servers[0].name == "new"


class TestAutoDiscovery:
    """Test AutoDiscovery high-level interface."""
    
    def test_create_autodiscovery(self):
        """Test creating AutoDiscovery instance."""
        discovery = AutoDiscovery(
            server_name="test-server",
            server_version="1.0.0",
            server_description="Test",
            transport="sse",
            host="localhost",
            port=8080
        )
        
        assert discovery.server_info.name == "test-server"
        assert discovery.server_info.transport == "sse"
        assert discovery.server_info.port == 8080
    
    def test_update_capabilities(self):
        """Test updating server capabilities."""
        discovery = AutoDiscovery(
            server_name="test-server",
            server_version="1.0.0"
        )
        
        discovery.update_capabilities(
            tools=["tool1", "tool2"],
            resources=["resource1"],
            prompts=["prompt1", "prompt2", "prompt3"]
        )
        
        caps = discovery.server_info.capabilities
        assert caps["tool_count"] == 2
        assert caps["resource_count"] == 1
        assert caps["prompt_count"] == 3
        assert caps["tools"] == ["tool1", "tool2"]
    
    @patch('makemcp.autodiscovery.DiscoveryBroadcaster')
    def test_context_manager(self, mock_broadcaster_class):
        """Test using AutoDiscovery as context manager."""
        mock_broadcaster = Mock()
        mock_broadcaster_class.return_value = mock_broadcaster
        
        with AutoDiscovery("test-server") as discovery:
            # Should start broadcaster
            mock_broadcaster.start.assert_called_once()
        
        # Should stop broadcaster on exit
        mock_broadcaster.stop.assert_called_once()


class TestMakeMCPServerIntegration:
    """Test MakeMCPServer autodiscovery integration."""
    
    def test_server_with_autodiscovery_enabled(self):
        """Test server with autodiscovery enabled."""
        server = MakeMCPServer(
            name="test-server",
            version="1.0.0",
            enable_autodiscovery=True,
            discovery_metadata={"test": "value"}
        )
        
        assert server.enable_autodiscovery is True
        assert server.discovery_metadata == {"test": "value"}
        assert server._autodiscovery is None
    
    def test_server_with_autodiscovery_disabled(self):
        """Test server with autodiscovery disabled."""
        server = MakeMCPServer(
            name="test-server",
            version="1.0.0",
            enable_autodiscovery=False
        )
        
        assert server.enable_autodiscovery is False
        assert server._autodiscovery is None
    
    @patch('makemcp.server.AutoDiscovery')
    def test_start_autodiscovery(self, mock_autodiscovery_class):
        """Test starting autodiscovery."""
        mock_autodiscovery = Mock()
        mock_autodiscovery_class.return_value = mock_autodiscovery
        
        server = MakeMCPServer(
            name="test-server",
            enable_autodiscovery=True
        )
        
        # Add some tools
        @server.tool()
        def test_tool():
            return "test"
        
        # Start autodiscovery
        server.start_autodiscovery(transport="sse", host="localhost", port=8080)
        
        # Check AutoDiscovery was created
        mock_autodiscovery_class.assert_called_once_with(
            server_name="test-server",
            server_version="1.0.0",
            server_description="test-server MCP Server",
            transport="sse",
            host="localhost",
            port=8080,
            metadata={}
        )
        
        # Check capabilities were updated
        mock_autodiscovery.update_capabilities.assert_called_once()
        
        # Check broadcasting started
        mock_autodiscovery.start.assert_called_once()
    
    def test_stop_autodiscovery(self):
        """Test stopping autodiscovery."""
        server = MakeMCPServer(
            name="test-server",
            enable_autodiscovery=True
        )
        
        # Create mock autodiscovery
        mock_autodiscovery = Mock()
        server._autodiscovery = mock_autodiscovery
        
        # Stop autodiscovery
        server.stop_autodiscovery()
        
        # Check it was stopped
        mock_autodiscovery.stop.assert_called_once()
        assert server._autodiscovery is None


@pytest.mark.asyncio
class TestDiscoverServers:
    """Test the discover_servers convenience function."""
    
    @patch('makemcp.autodiscovery.DiscoveryListener')
    async def test_discover_servers(self, mock_listener_class):
        """Test discovering servers."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener
        
        # Mock some servers
        test_servers = [
            ServerInfo(
                id="server1",
                name="Server 1",
                version="1.0.0",
                description="Test",
                host="localhost",
                port=8080,
                transport="sse",
                capabilities={},
                metadata={},
                timestamp=time.time()
            ),
            ServerInfo(
                id="server2",
                name="Server 2",
                version="2.0.0",
                description="Test",
                host="localhost",
                port=8081,
                transport="stdio",
                capabilities={},
                metadata={},
                timestamp=time.time()
            )
        ]
        
        mock_listener.get_servers.return_value = test_servers
        
        # Discover servers
        servers = await discover_servers(timeout=0.1)
        
        # Check listener was started and stopped
        mock_listener.start.assert_called_once()
        mock_listener.stop.assert_called_once()
        
        # Check servers returned
        assert len(servers) == 2
        assert servers[0].name == "Server 1"
        assert servers[1].name == "Server 2"