"""
Simple tests for CLI module to improve coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
import argparse

from makemcp.cli import cmd_register, cmd_list, cmd_info, cmd_discover, cmd_export, cmd_unregister


class TestCLICommands:
    """Test CLI command functions."""
    
    def test_cmd_register(self):
        """Test register command."""
        args = argparse.Namespace(
            name="test-server",
            command="python test.py",
            description="Test server",
            working_dir=None,
            tool_prefix=None
        )
        
        with patch('makemcp.cli.register_server') as mock_register:
            cmd_register(args)
            
            mock_register.assert_called_once_with(
                name="test-server",
                command=["python", "test.py"],
                description="Test server",
                working_dir=None,
                tool_prefix=None
            )
    
    def test_cmd_list(self):
        """Test list command."""
        args = argparse.Namespace()
        
        with patch('makemcp.cli.ServerRegistry') as mock_registry:
            from makemcp.registry import ServerRegistration
            mock_instance = MagicMock()
            mock_instance.list.return_value = [
                ServerRegistration(
                    name="server1",
                    description="Test server",
                    command=["python", "test.py"]
                )
            ]
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print'):
                cmd_list(args)
                mock_instance.list.assert_called_once()
    
    def test_cmd_info(self):
        """Test info command."""
        args = argparse.Namespace(name="test-server")
        
        with patch('makemcp.cli.ServerRegistry') as mock_registry:
            from makemcp.registry import ServerRegistration
            mock_instance = MagicMock()
            mock_instance.get.return_value = ServerRegistration(
                name="test-server",
                description="Test server",
                command=["python", "test.py"]
            )
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print'):
                cmd_info(args)
                mock_instance.get.assert_called_once_with("test-server")
    
    def test_cmd_discover(self):
        """Test discover command."""
        args = argparse.Namespace(
            scan_filesystem=True,
            scan_network=False,
            paths=None,
            auto_register=False,
            timeout=5.0
        )
        
        with patch('makemcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.auto_discover.return_value = []
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print'):
                cmd_discover(args)
                mock_instance.auto_discover.assert_called_once()
    
    def test_cmd_export(self):
        """Test export command."""
        args = argparse.Namespace(
            format="json",
            output=None
        )
        
        with patch('makemcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.to_gleitzeit_config.return_value = {"mcp": {"servers": []}}
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print'):
                cmd_export(args)
                mock_instance.to_gleitzeit_config.assert_called_once()
    
    def test_cmd_unregister(self):
        """Test unregister command."""
        args = argparse.Namespace(name="test-server")
        
        with patch('makemcp.cli.ServerRegistry') as mock_registry:
            mock_instance = MagicMock()
            mock_instance.unregister.return_value = True
            mock_registry.return_value = mock_instance
            
            with patch('builtins.print'):
                cmd_unregister(args)
                mock_instance.unregister.assert_called_once_with("test-server")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])