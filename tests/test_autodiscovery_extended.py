"""
Extended tests for autodiscovery module to improve coverage.
"""

import pytest
import json
import socket
import struct
import time
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta

from quickmcp.autodiscovery import (
    ServerInfo,
    DiscoveryPacket,
    DiscoveryBroadcaster,
    DiscoveryListener,
    AutoDiscovery,
    discover_servers
)


class TestDiscoveryPacket:
    """Test DiscoveryPacket creation and parsing."""
    
    def test_create_packet(self):
        """Test creating a discovery packet."""
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080,
            protocol="http"
        )
        
        packet = DiscoveryPacket.create(server_info)
        
        assert packet.magic == b"MCPD"
        assert packet.version == 1
        assert packet.server_info == server_info
    
    def test_to_bytes(self):
        """Test converting packet to bytes."""
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080
        )
        
        packet = DiscoveryPacket.create(server_info)
        data = packet.to_bytes()
        
        assert isinstance(data, bytes)
        assert data.startswith(b"MCPD")
        assert len(data) > 8  # Magic (4) + version (2) + length (2) + JSON data
    
    def test_from_bytes_valid(self):
        """Test parsing valid packet from bytes."""
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080
        )
        
        packet = DiscoveryPacket.create(server_info)
        data = packet.to_bytes()
        
        parsed = DiscoveryPacket.from_bytes(data)
        
        assert parsed is not None
        assert parsed.magic == b"MCPD"
        assert parsed.server_info.name == "test-server"
        assert parsed.server_info.port == 8080
    
    def test_from_bytes_invalid_magic(self):
        """Test parsing packet with invalid magic."""
        data = b"XXXX" + struct.pack('!HH', 1, 10) + b'{"test": 1}'
        
        parsed = DiscoveryPacket.from_bytes(data)
        assert parsed is None
    
    def test_from_bytes_invalid_json(self):
        """Test parsing packet with invalid JSON."""
        data = b"MCPD" + struct.pack('!HH', 1, 10) + b'not json'
        
        parsed = DiscoveryPacket.from_bytes(data)
        assert parsed is None
    
    def test_from_bytes_truncated(self):
        """Test parsing truncated packet."""
        data = b"MCPD" + struct.pack('!H', 1)  # Missing length and data
        
        parsed = DiscoveryPacket.from_bytes(data)
        assert parsed is None


class TestDiscoveryBroadcasterExtended:
    """Extended tests for DiscoveryBroadcaster."""
    
    def test_broadcaster_send_packet(self):
        """Test sending discovery packet."""
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080
        )
        
        broadcaster = DiscoveryBroadcaster(server_info)
        
        with patch.object(broadcaster, '_sock') as mock_sock:
            broadcaster._send_packet()
            
            mock_sock.sendto.assert_called_once()
            call_args = mock_sock.sendto.call_args[0]
            data = call_args[0]
            addr = call_args[1]
            
            assert data.startswith(b"MCPD")
            assert addr == (broadcaster.MULTICAST_GROUP, broadcaster.MULTICAST_PORT)
    
    def test_broadcaster_run_loop(self):
        """Test broadcaster run loop."""
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080
        )
        
        broadcaster = DiscoveryBroadcaster(server_info, interval=0.1)
        
        with patch.object(broadcaster, '_send_packet') as mock_send:
            # Start broadcaster
            broadcaster.start()
            
            # Let it run for a short time
            time.sleep(0.25)
            
            # Stop broadcaster
            broadcaster.stop()
            
            # Should have sent at least 2 packets
            assert mock_send.call_count >= 2
    
    def test_broadcaster_socket_error(self):
        """Test broadcaster handling socket errors."""
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080
        )
        
        broadcaster = DiscoveryBroadcaster(server_info)
        
        with patch.object(broadcaster, '_sock') as mock_sock:
            mock_sock.sendto.side_effect = socket.error("Test error")
            
            with patch('quickmcp.autodiscovery.logger') as mock_logger:
                broadcaster._send_packet()
                
                mock_logger.error.assert_called()


class TestDiscoveryListenerExtended:
    """Extended tests for DiscoveryListener."""
    
    def test_listener_receive_packet(self):
        """Test receiving and processing packet."""
        listener = DiscoveryListener()
        
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="192.168.1.100",
            port=8080
        )
        
        packet = DiscoveryPacket.create(server_info)
        data = packet.to_bytes()
        
        with patch.object(listener, '_sock') as mock_sock:
            mock_sock.recvfrom.return_value = (data, ('192.168.1.100', 12345))
            
            listener._receive_packet()
            
            servers = listener.get_servers()
            assert len(servers) == 1
            assert servers[0].name == "test-server"
    
    def test_listener_ignore_invalid_packet(self):
        """Test listener ignores invalid packets."""
        listener = DiscoveryListener()
        
        with patch.object(listener, '_sock') as mock_sock:
            mock_sock.recvfrom.return_value = (b"invalid data", ('192.168.1.100', 12345))
            
            listener._receive_packet()
            
            servers = listener.get_servers()
            assert len(servers) == 0
    
    def test_listener_remove_stale_servers(self):
        """Test removing stale servers."""
        listener = DiscoveryListener(timeout=1)  # 1 second timeout
        
        # Add a server
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="192.168.1.100",
            port=8080
        )
        
        # Manually add to simulate received server
        listener._servers["192.168.1.100:8080"] = (server_info, time.time() - 2)  # 2 seconds ago
        
        # Get servers should remove stale ones
        servers = listener.get_servers()
        assert len(servers) == 0
    
    def test_listener_update_existing_server(self):
        """Test updating existing server info."""
        listener = DiscoveryListener()
        
        # First packet
        server_info1 = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="192.168.1.100",
            port=8080
        )
        
        packet1 = DiscoveryPacket.create(server_info1)
        
        # Second packet with updated version
        server_info2 = ServerInfo(
            name="test-server",
            version="2.0.0",
            host="192.168.1.100",
            port=8080
        )
        
        packet2 = DiscoveryPacket.create(server_info2)
        
        with patch.object(listener, '_sock') as mock_sock:
            # Receive first packet
            mock_sock.recvfrom.return_value = (packet1.to_bytes(), ('192.168.1.100', 12345))
            listener._receive_packet()
            
            # Receive second packet
            mock_sock.recvfrom.return_value = (packet2.to_bytes(), ('192.168.1.100', 12345))
            listener._receive_packet()
            
            servers = listener.get_servers()
            assert len(servers) == 1
            assert servers[0].version == "2.0.0"
    
    def test_listener_socket_timeout(self):
        """Test listener handling socket timeout."""
        listener = DiscoveryListener()
        
        with patch.object(listener, '_sock') as mock_sock:
            mock_sock.recvfrom.side_effect = socket.timeout()
            
            # Should not crash
            listener._receive_packet()
            
            servers = listener.get_servers()
            assert len(servers) == 0


class TestAutoDiscoveryExtended:
    """Extended tests for AutoDiscovery class."""
    
    def test_autodiscovery_context_manager(self):
        """Test using AutoDiscovery as context manager."""
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080
        )
        
        with patch('quickmcp.autodiscovery.DiscoveryBroadcaster') as mock_broadcaster_class:
            mock_broadcaster = MagicMock()
            mock_broadcaster_class.return_value = mock_broadcaster
            
            with AutoDiscovery(server_info) as discovery:
                assert discovery is not None
                mock_broadcaster.start.assert_called_once()
            
            mock_broadcaster.stop.assert_called_once()
    
    def test_autodiscovery_update_capabilities(self):
        """Test updating server capabilities."""
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080
        )
        
        discovery = AutoDiscovery(server_info)
        
        new_capabilities = {
            "tools": ["tool1", "tool2"],
            "resources": ["resource1"]
        }
        
        discovery.update_capabilities(new_capabilities)
        
        assert discovery.server_info.capabilities == new_capabilities
        assert discovery._broadcaster.server_info.capabilities == new_capabilities
    
    def test_autodiscovery_enabled_disabled(self):
        """Test autodiscovery enable/disable states."""
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080
        )
        
        # Test disabled
        discovery = AutoDiscovery(server_info, enabled=False)
        
        with patch('quickmcp.autodiscovery.DiscoveryBroadcaster') as mock_broadcaster_class:
            discovery.start()
            mock_broadcaster_class.assert_not_called()
        
        # Test enabled
        discovery = AutoDiscovery(server_info, enabled=True)
        
        with patch('quickmcp.autodiscovery.DiscoveryBroadcaster') as mock_broadcaster_class:
            mock_broadcaster = MagicMock()
            mock_broadcaster_class.return_value = mock_broadcaster
            
            discovery.start()
            mock_broadcaster.start.assert_called_once()


class TestDiscoverServersFunction:
    """Test the discover_servers function."""
    
    def test_discover_servers_basic(self):
        """Test basic server discovery."""
        with patch('quickmcp.autodiscovery.DiscoveryListener') as mock_listener_class:
            mock_listener = MagicMock()
            mock_listener.get_servers.return_value = [
                ServerInfo(
                    name="server1",
                    version="1.0.0",
                    host="192.168.1.100",
                    port=8080
                ),
                ServerInfo(
                    name="server2",
                    version="2.0.0",
                    host="192.168.1.101",
                    port=8081
                )
            ]
            mock_listener_class.return_value = mock_listener
            
            servers = discover_servers(duration=1)
            
            assert len(servers) == 2
            assert servers[0].name == "server1"
            assert servers[1].name == "server2"
    
    def test_discover_servers_with_listener_error(self):
        """Test discovery with listener errors."""
        with patch('quickmcp.autodiscovery.DiscoveryListener') as mock_listener_class:
            mock_listener = MagicMock()
            mock_listener.start.side_effect = Exception("Test error")
            mock_listener_class.return_value = mock_listener
            
            with patch('quickmcp.autodiscovery.logger') as mock_logger:
                servers = discover_servers(duration=0.1)
                
                mock_logger.error.assert_called()
                assert len(servers) == 0


class TestServerInfoExtended:
    """Extended tests for ServerInfo class."""
    
    def test_server_info_with_metadata(self):
        """Test ServerInfo with metadata."""
        metadata = {
            "author": "Test Author",
            "description": "Test server",
            "tags": ["test", "demo"]
        }
        
        server_info = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080,
            metadata=metadata
        )
        
        assert server_info.metadata == metadata
        
        # Test JSON serialization
        json_data = server_info.to_json()
        parsed = ServerInfo.from_json(json_data)
        
        assert parsed.metadata == metadata
    
    def test_server_info_equality(self):
        """Test ServerInfo equality comparison."""
        server1 = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080
        )
        
        server2 = ServerInfo(
            name="test-server",
            version="1.0.0",
            host="localhost",
            port=8080
        )
        
        server3 = ServerInfo(
            name="other-server",
            version="1.0.0",
            host="localhost",
            port=8080
        )
        
        assert server1 == server2
        assert server1 != server3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])