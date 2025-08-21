"""
MakeMCP Autodiscovery - Allow MCP servers to be discovered on the network
"""

import asyncio
import json
import socket
import time
import threading
import logging
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, asdict
import platform
import uuid

logger = logging.getLogger(__name__)

# Default multicast group and port for MCP discovery
MCP_MULTICAST_GROUP = "239.255.41.42"  # Private multicast address
MCP_DISCOVERY_PORT = 42424
MCP_BROADCAST_INTERVAL = 5.0  # seconds
MCP_DISCOVERY_MAGIC = b"MCP_DISCOVER_V1"


@dataclass
class ServerInfo:
    """Information about an MCP server for discovery."""
    id: str
    name: str
    version: str
    description: str
    host: str
    port: int
    transport: str
    capabilities: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> "ServerInfo":
        """Create from JSON string."""
        return cls(**json.loads(data))


class DiscoveryBroadcaster:
    """Broadcasts MCP server information for autodiscovery."""
    
    def __init__(
        self,
        server_info: ServerInfo,
        multicast_group: str = MCP_MULTICAST_GROUP,
        port: int = MCP_DISCOVERY_PORT,
        interval: float = MCP_BROADCAST_INTERVAL,
        enable_broadcast: bool = True,
        enable_multicast: bool = True,
    ):
        """
        Initialize the discovery broadcaster.
        
        Args:
            server_info: Information about the server to broadcast
            multicast_group: Multicast group address
            port: Port for discovery
            interval: Broadcast interval in seconds
            enable_broadcast: Enable UDP broadcast
            enable_multicast: Enable multicast
        """
        self.server_info = server_info
        self.multicast_group = multicast_group
        self.port = port
        self.interval = interval
        self.enable_broadcast = enable_broadcast
        self.enable_multicast = enable_multicast
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._sockets: List[socket.socket] = []
        
        logger.info(f"Discovery broadcaster initialized for {server_info.name}")
    
    def start(self) -> None:
        """Start broadcasting discovery information."""
        if self._running:
            logger.warning("Discovery broadcaster already running")
            return
        
        self._running = True
        self._setup_sockets()
        self._thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self._thread.start()
        logger.info(f"Discovery broadcasting started for {self.server_info.name}")
    
    def stop(self) -> None:
        """Stop broadcasting discovery information."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self._cleanup_sockets()
        logger.info(f"Discovery broadcasting stopped for {self.server_info.name}")
    
    def _setup_sockets(self) -> None:
        """Set up broadcast and multicast sockets."""
        # Broadcast socket
        if self.enable_broadcast:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # Platform-specific reuse port
                if hasattr(socket, 'SO_REUSEPORT'):
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                self._sockets.append(sock)
                logger.debug("Broadcast socket created")
            except Exception as e:
                logger.error(f"Failed to create broadcast socket: {e}")
        
        # Multicast socket
        if self.enable_multicast:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if hasattr(socket, 'SO_REUSEPORT'):
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                # Set multicast TTL
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                # Enable multicast loop (receive own messages)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
                self._sockets.append(sock)
                logger.debug("Multicast socket created")
            except Exception as e:
                logger.error(f"Failed to create multicast socket: {e}")
    
    def _cleanup_sockets(self) -> None:
        """Clean up sockets."""
        for sock in self._sockets:
            try:
                sock.close()
            except:
                pass
        self._sockets.clear()
    
    def _broadcast_loop(self) -> None:
        """Main broadcast loop."""
        while self._running:
            try:
                # Update timestamp
                self.server_info.timestamp = time.time()
                
                # Create discovery packet
                packet = self._create_packet()
                
                # Broadcast
                if self.enable_broadcast:
                    self._send_broadcast(packet)
                
                # Multicast
                if self.enable_multicast:
                    self._send_multicast(packet)
                
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
            
            # Wait for next broadcast
            time.sleep(self.interval)
    
    def _create_packet(self) -> bytes:
        """Create a discovery packet."""
        # Packet format: MAGIC + JSON data
        data = self.server_info.to_json().encode('utf-8')
        return MCP_DISCOVERY_MAGIC + b'\n' + data
    
    def _send_broadcast(self, packet: bytes) -> None:
        """Send broadcast packet."""
        if not self._sockets:
            return
        
        try:
            sock = self._sockets[0]  # Use first socket for broadcast
            sock.sendto(packet, ('<broadcast>', self.port))
            logger.debug(f"Broadcast sent for {self.server_info.name}")
        except Exception as e:
            logger.error(f"Failed to send broadcast: {e}")
    
    def _send_multicast(self, packet: bytes) -> None:
        """Send multicast packet."""
        if len(self._sockets) < 2 and not self.enable_broadcast:
            sock = self._sockets[0]
        elif len(self._sockets) >= 2:
            sock = self._sockets[1]
        else:
            return
        
        try:
            sock.sendto(packet, (self.multicast_group, self.port))
            logger.debug(f"Multicast sent for {self.server_info.name}")
        except Exception as e:
            logger.error(f"Failed to send multicast: {e}")


class DiscoveryListener:
    """Listens for MCP server discovery broadcasts."""
    
    def __init__(
        self,
        callback: Optional[Callable[[ServerInfo], None]] = None,
        multicast_group: str = MCP_MULTICAST_GROUP,
        port: int = MCP_DISCOVERY_PORT,
        timeout: float = 30.0,
    ):
        """
        Initialize the discovery listener.
        
        Args:
            callback: Callback function when server is discovered
            multicast_group: Multicast group address
            port: Port for discovery
            timeout: Timeout for removing stale servers
        """
        self.callback = callback
        self.multicast_group = multicast_group
        self.port = port
        self.timeout = timeout
        
        self._running = False
        self._servers: Dict[str, ServerInfo] = {}
        self._thread: Optional[threading.Thread] = None
        self._socket: Optional[socket.socket] = None
        
        logger.info("Discovery listener initialized")
    
    def start(self) -> None:
        """Start listening for discovery broadcasts."""
        if self._running:
            logger.warning("Discovery listener already running")
            return
        
        self._running = True
        self._setup_socket()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Discovery listener started")
    
    def stop(self) -> None:
        """Stop listening for discovery broadcasts."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self._cleanup_socket()
        logger.info("Discovery listener stopped")
    
    def get_servers(self) -> List[ServerInfo]:
        """Get list of discovered servers."""
        current_time = time.time()
        # Remove stale servers
        stale_ids = [
            sid for sid, info in self._servers.items()
            if current_time - info.timestamp > self.timeout
        ]
        for sid in stale_ids:
            del self._servers[sid]
            logger.debug(f"Removed stale server: {sid}")
        
        return list(self._servers.values())
    
    def _setup_socket(self) -> None:
        """Set up listening socket."""
        try:
            # Create socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, 'SO_REUSEPORT'):
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            
            # Bind to port
            self._socket.bind(('', self.port))
            
            # Join multicast group
            group = socket.inet_aton(self.multicast_group)
            mreq = group + socket.inet_aton('0.0.0.0')
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            # Set timeout for socket operations
            self._socket.settimeout(1.0)
            
            logger.debug(f"Listening socket created on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to create listening socket: {e}")
            raise
    
    def _cleanup_socket(self) -> None:
        """Clean up listening socket."""
        if self._socket:
            try:
                # Leave multicast group
                group = socket.inet_aton(self.multicast_group)
                mreq = group + socket.inet_aton('0.0.0.0')
                self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
            except:
                pass
            
            try:
                self._socket.close()
            except:
                pass
            
            self._socket = None
    
    def _listen_loop(self) -> None:
        """Main listening loop."""
        while self._running:
            try:
                # Receive packet
                data, addr = self._socket.recvfrom(65535)
                
                # Process packet
                self._process_packet(data, addr)
                
            except socket.timeout:
                # Timeout is expected, continue
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"Error in listen loop: {e}")
    
    def _process_packet(self, data: bytes, addr: tuple) -> None:
        """Process a received discovery packet."""
        try:
            # Check magic bytes
            if not data.startswith(MCP_DISCOVERY_MAGIC):
                return
            
            # Extract JSON data
            json_data = data[len(MCP_DISCOVERY_MAGIC) + 1:]
            
            # Parse server info
            server_info = ServerInfo.from_json(json_data.decode('utf-8'))
            
            # Update or add server
            is_new = server_info.id not in self._servers
            self._servers[server_info.id] = server_info
            
            # Call callback for new servers
            if is_new and self.callback:
                self.callback(server_info)
            
            logger.debug(f"Discovered server: {server_info.name} from {addr[0]}")
            
        except Exception as e:
            logger.error(f"Failed to process discovery packet: {e}")


class AutoDiscovery:
    """High-level autodiscovery interface for MakeMCP servers."""
    
    def __init__(
        self,
        server_name: str,
        server_version: str = "1.0.0",
        server_description: str = "",
        transport: str = "stdio",
        host: str = "localhost",
        port: int = 8000,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize autodiscovery for a server.
        
        Args:
            server_name: Name of the server
            server_version: Version of the server
            server_description: Description of the server
            transport: Transport type (stdio, sse, http)
            host: Host for network transports
            port: Port for network transports
            metadata: Additional metadata
        """
        self.server_id = str(uuid.uuid4())
        self.server_info = ServerInfo(
            id=self.server_id,
            name=server_name,
            version=server_version,
            description=server_description,
            host=host if transport != "stdio" else platform.node(),
            port=port if transport != "stdio" else 0,
            transport=transport,
            capabilities={},
            metadata=metadata or {},
            timestamp=time.time()
        )
        
        self.broadcaster = DiscoveryBroadcaster(self.server_info)
        logger.info(f"AutoDiscovery initialized for {server_name}")
    
    def update_capabilities(self, tools: List[str], resources: List[str], prompts: List[str]) -> None:
        """Update server capabilities."""
        self.server_info.capabilities = {
            "tools": tools,
            "resources": resources,
            "prompts": prompts,
            "tool_count": len(tools),
            "resource_count": len(resources),
            "prompt_count": len(prompts),
        }
    
    def start(self) -> None:
        """Start autodiscovery broadcasting."""
        self.broadcaster.start()
    
    def stop(self) -> None:
        """Stop autodiscovery broadcasting."""
        self.broadcaster.stop()
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Convenience function for discovering servers
async def discover_servers(timeout: float = 5.0) -> List[ServerInfo]:
    """
    Discover MCP servers on the network.
    
    Args:
        timeout: Discovery timeout in seconds
    
    Returns:
        List of discovered servers
    """
    discovered = []
    
    def on_discovered(server_info: ServerInfo):
        discovered.append(server_info)
    
    listener = DiscoveryListener(callback=on_discovered)
    listener.start()
    
    # Wait for discovery
    await asyncio.sleep(timeout)
    
    listener.stop()
    
    # Also get any servers that were already discovered
    return listener.get_servers()


# CLI tool for discovery
def discovery_cli():
    """Command-line tool for testing discovery."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server Discovery Tool")
    parser.add_argument("command", choices=["listen", "broadcast"], help="Command to run")
    parser.add_argument("--name", default="test-server", help="Server name (for broadcast)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (for broadcast)")
    parser.add_argument("--transport", default="stdio", help="Transport type (for broadcast)")
    parser.add_argument("--timeout", type=float, default=30.0, help="Discovery timeout")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    if args.command == "listen":
        print("Listening for MCP servers...")
        
        def on_discovered(server_info: ServerInfo):
            print(f"\n=== Discovered Server ===")
            print(f"Name: {server_info.name}")
            print(f"Version: {server_info.version}")
            print(f"Transport: {server_info.transport}")
            print(f"Host: {server_info.host}")
            print(f"Port: {server_info.port}")
            print(f"Capabilities: {server_info.capabilities}")
            print("=" * 25)
        
        listener = DiscoveryListener(callback=on_discovered, timeout=args.timeout)
        listener.start()
        
        try:
            while True:
                time.sleep(1)
                servers = listener.get_servers()
                if servers:
                    print(f"\rActive servers: {len(servers)}", end="", flush=True)
        except KeyboardInterrupt:
            print("\nStopping listener...")
            listener.stop()
    
    elif args.command == "broadcast":
        print(f"Broadcasting server: {args.name}")
        
        server_info = ServerInfo(
            id=str(uuid.uuid4()),
            name=args.name,
            version="1.0.0",
            description="Test MCP server",
            host=platform.node(),
            port=args.port,
            transport=args.transport,
            capabilities={"tools": ["test_tool"], "resources": [], "prompts": []},
            metadata={},
            timestamp=time.time()
        )
        
        broadcaster = DiscoveryBroadcaster(server_info)
        broadcaster.start()
        
        try:
            while True:
                time.sleep(1)
                print(".", end="", flush=True)
        except KeyboardInterrupt:
            print("\nStopping broadcaster...")
            broadcaster.stop()


if __name__ == "__main__":
    discovery_cli()