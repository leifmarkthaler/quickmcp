#!/usr/bin/env python
"""
Test that QuickMCP servers work with MCP protocol.
"""

import json
import sys
import subprocess
import time

def test_server(server_script):
    """Test a server with basic MCP protocol messages."""
    
    # Start server process
    proc = subprocess.Popen(
        [sys.executable, server_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=0
    )
    
    try:
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-14",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"}
            },
            "id": 1
        }
        
        proc.stdin.write(json.dumps(init_request) + '\n')
        proc.stdin.flush()
        
        # Read response (with timeout)
        start_time = time.time()
        response_lines = []
        
        while time.time() - start_time < 2:  # 2 second timeout
            try:
                proc.stdout.flush()
                line = proc.stdout.readline()
                if line:
                    # Skip non-JSON output (server info messages)
                    line = line.strip()
                    if line.startswith('{'):
                        try:
                            response = json.loads(line)
                            if 'result' in response or 'error' in response:
                                print(f"✓ Server responded to initialize")
                                print(f"  Protocol version: {response.get('result', {}).get('protocolVersion', 'unknown')}")
                                print(f"  Server name: {response.get('result', {}).get('serverInfo', {}).get('name', 'unknown')}")
                                return True
                        except json.JSONDecodeError:
                            pass
            except:
                break
                
        print("✗ No valid response received")
        return False
        
    finally:
        proc.terminate()
        proc.wait(timeout=1)


if __name__ == "__main__":
    print("Testing QuickMCP Server MCP Protocol Compliance")
    print("=" * 50)
    
    servers = [
        ("simple_server.py", "Simple Server"),
        ("math_server.py", "Math Server"),
        ("file_server.py", "File Server"),
    ]
    
    for server_file, server_name in servers:
        print(f"\nTesting {server_name}...")
        try:
            if test_server(server_file):
                print(f"✓ {server_name} works with MCP protocol")
            else:
                print(f"✗ {server_name} failed MCP protocol test")
        except FileNotFoundError:
            print(f"  Server file not found: {server_file}")
        except Exception as e:
            print(f"  Error testing server: {e}")
    
    print("\n" + "=" * 50)
    print("Test complete!")