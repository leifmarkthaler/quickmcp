"""
Tests for the CLI module.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call
import sys
from io import StringIO

from quickmcp.cli import (
    main,
    register_server,
    unregister_server,
    list_servers,
    show_server_info,
    discover_servers,
    export_config
)


class TestCLIRegister:
    """Test the register command."""
    
    def test_register_server_success(self):
        """Test successful server registration."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_registry.return_value = mock_instance
            
            result = register_server("test-server", "python test.py")
            
            mock_instance.register.assert_called_once_with(
                "test-server", 
                "python test.py"
            )
            assert result == 0
    
    def test_register_server_with_description(self):
        """Test server registration with description."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_registry.return_value = mock_instance
            
            result = register_server(
                "test-server", 
                "python test.py",
                description="Test server"
            )
            
            mock_instance.register.assert_called_once_with(
                "test-server",
                "python test.py",
                description="Test server"
            )
            assert result == 0
    
    def test_register_server_error(self):
        """Test server registration with error."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.register.side_effect = Exception("Registration failed")
            mock_registry.return_value = mock_instance
            
            with patch('quickmcp.cli.logger') as mock_logger:
                result = register_server("test-server", "python test.py")
                
                mock_logger.error.assert_called()
                assert result == 1


class TestCLIUnregister:
    """Test the unregister command."""
    
    def test_unregister_server_success(self):
        """Test successful server unregistration."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_registry.return_value = mock_instance
            
            result = unregister_server("test-server")
            
            mock_instance.unregister.assert_called_once_with("test-server")
            assert result == 0
    
    def test_unregister_server_not_found(self):
        """Test unregistering non-existent server."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.unregister.side_effect = KeyError("Server not found")
            mock_registry.return_value = mock_instance
            
            with patch('quickmcp.cli.logger') as mock_logger:
                result = unregister_server("nonexistent")
                
                mock_logger.error.assert_called()
                assert result == 1


class TestCLIList:
    """Test the list command."""
    
    def test_list_servers_empty(self):
        """Test listing when no servers registered."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.list.return_value = []
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print') as mock_print:
                result = list_servers()
                
                mock_print.assert_called_with("No servers registered")
                assert result == 0
    
    def test_list_servers_with_entries(self):
        """Test listing registered servers."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.list.return_value = [
                {
                    "name": "server1",
                    "command": "python server1.py",
                    "description": "First server"
                },
                {
                    "name": "server2", 
                    "command": "python server2.py",
                    "description": None
                }
            ]
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print') as mock_print:
                result = list_servers()
                
                # Check that servers are printed
                calls = mock_print.call_args_list
                assert any("server1" in str(call) for call in calls)
                assert any("server2" in str(call) for call in calls)
                assert result == 0
    
    def test_list_servers_verbose(self):
        """Test verbose listing."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.list.return_value = [
                {
                    "name": "server1",
                    "command": "python server1.py",
                    "created_at": "2024-01-01T00:00:00"
                }
            ]
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print') as mock_print:
                result = list_servers(verbose=True)
                
                # Check verbose output includes timestamps
                calls = mock_print.call_args_list
                assert any("2024-01-01" in str(call) for call in calls)
                assert result == 0


class TestCLIInfo:
    """Test the info command."""
    
    def test_show_server_info_success(self):
        """Test showing server info."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.get.return_value = {
                "name": "test-server",
                "command": "python test.py",
                "description": "Test server",
                "created_at": "2024-01-01T00:00:00"
            }
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print') as mock_print:
                result = show_server_info("test-server")
                
                mock_instance.get.assert_called_once_with("test-server")
                calls = mock_print.call_args_list
                assert any("test-server" in str(call) for call in calls)
                assert result == 0
    
    def test_show_server_info_not_found(self):
        """Test showing info for non-existent server."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.get.return_value = None
            mock_registry.return_value = mock_instance
            
            with patch('quickmcp.cli.logger') as mock_logger:
                result = show_server_info("nonexistent")
                
                mock_logger.error.assert_called_with("Server 'nonexistent' not found")
                assert result == 1


class TestCLIDiscover:
    """Test the discover command."""
    
    def test_discover_filesystem(self):
        """Test filesystem discovery."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.discover_filesystem.return_value = [
                "/path/to/server1.py",
                "/path/to/server2.py"
            ]
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print') as mock_print:
                result = discover_servers(scan_filesystem=True)
                
                mock_instance.discover_filesystem.assert_called_once()
                calls = mock_print.call_args_list
                assert any("server1.py" in str(call) for call in calls)
                assert result == 0
    
    def test_discover_network(self):
        """Test network discovery."""
        with patch('quickmcp.cli.discover_servers_network') as mock_discover:
            mock_discover.return_value = [
                {
                    "name": "network-server",
                    "host": "localhost",
                    "port": 8080
                }
            ]
            
            with patch('builtins.print') as mock_print:
                result = discover_servers(scan_network=True)
                
                mock_discover.assert_called_once()
                calls = mock_print.call_args_list
                assert any("network-server" in str(call) for call in calls)
                assert result == 0
    
    def test_discover_both(self):
        """Test both filesystem and network discovery."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.discover_filesystem.return_value = ["/path/server.py"]
            mock_registry.return_value = mock_instance
            
            with patch('quickmcp.cli.discover_servers_network') as mock_discover:
                mock_discover.return_value = [{"name": "net-server"}]
                
                with patch('builtins.print') as mock_print:
                    result = discover_servers(
                        scan_filesystem=True,
                        scan_network=True
                    )
                    
                    assert mock_instance.discover_filesystem.called
                    assert mock_discover.called
                    assert result == 0


class TestCLIExport:
    """Test the export command."""
    
    def test_export_yaml(self):
        """Test exporting to YAML format."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.export_gleitzeit.return_value = {
                "servers": {
                    "test-server": {
                        "command": "python test.py"
                    }
                }
            }
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print') as mock_print:
                with patch('quickmcp.cli.yaml') as mock_yaml:
                    result = export_config(format="yaml")
                    
                    mock_yaml.dump.assert_called_once()
                    assert result == 0
    
    def test_export_json(self):
        """Test exporting to JSON format."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.export_gleitzeit.return_value = {
                "servers": {"test": {}}
            }
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print') as mock_print:
                result = export_config(format="json")
                
                calls = mock_print.call_args_list
                # Check JSON output was printed
                assert any("{" in str(call) for call in calls)
                assert result == 0
    
    def test_export_to_file(self):
        """Test exporting to a file."""
        with patch('quickmcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.export_gleitzeit.return_value = {"servers": {}}
            mock_registry.return_value = mock_instance
            
            with patch('builtins.open', mock_open()) as mock_file:
                result = export_config(
                    format="json",
                    output="config.json"
                )
                
                mock_file.assert_called_once_with("config.json", "w")
                handle = mock_file()
                handle.write.assert_called()
                assert result == 0


class TestCLIMain:
    """Test the main CLI entry point."""
    
    def test_main_register(self):
        """Test main with register command."""
        test_args = ["quickmcp", "register", "test-server", "python test.py"]
        
        with patch('sys.argv', test_args):
            with patch('quickmcp.cli.register_server') as mock_register:
                mock_register.return_value = 0
                
                result = main()
                
                mock_register.assert_called_once_with(
                    "test-server",
                    "python test.py",
                    description=None
                )
                assert result == 0
    
    def test_main_list(self):
        """Test main with list command."""
        test_args = ["quickmcp", "list"]
        
        with patch('sys.argv', test_args):
            with patch('quickmcp.cli.list_servers') as mock_list:
                mock_list.return_value = 0
                
                result = main()
                
                mock_list.assert_called_once()
                assert result == 0
    
    def test_main_help(self):
        """Test main with help flag."""
        test_args = ["quickmcp", "--help"]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # argparse exits with 0 for help
            assert exc_info.value.code == 0
    
    def test_main_invalid_command(self):
        """Test main with invalid command."""
        test_args = ["quickmcp", "invalid"]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # argparse exits with error for invalid commands
            assert exc_info.value.code != 0
    
    def test_main_discover_with_options(self):
        """Test main with discover command and options."""
        test_args = ["quickmcp", "discover", "--scan-filesystem", "--scan-network"]
        
        with patch('sys.argv', test_args):
            with patch('quickmcp.cli.discover_servers') as mock_discover:
                mock_discover.return_value = 0
                
                result = main()
                
                mock_discover.assert_called_once_with(
                    scan_filesystem=True,
                    scan_network=True
                )
                assert result == 0
    
    def test_main_export_with_format(self):
        """Test main with export command and format option."""
        test_args = ["quickmcp", "export", "--format", "yaml", "-o", "out.yaml"]
        
        with patch('sys.argv', test_args):
            with patch('quickmcp.cli.export_config') as mock_export:
                mock_export.return_value = 0
                
                result = main()
                
                mock_export.assert_called_once_with(
                    format="yaml",
                    output="out.yaml"
                )
                assert result == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])