"""
Tests for the CLI factory module.
"""

import pytest
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import argparse

from quickmcp.cli_factory import main, create_parser, run_factory


class TestCLIFactoryParser:
    """Test the argument parser creation."""
    
    def test_create_parser(self):
        """Test parser creation with all arguments."""
        parser = create_parser()
        
        # Test basic arguments
        args = parser.parse_args(["test.py"])
        assert args.file == "test.py"
        assert args.name is None
        assert args.transport == "stdio"
        
        # Test with all options
        args = parser.parse_args([
            "test.py",
            "--name", "my-server",
            "--transport", "sse",
            "--host", "localhost",
            "--port", "8080",
            "--include", "func_*",
            "--exclude", "_private",
            "--include-private",
            "--check-dependencies",
            "--verbose"
        ])
        assert args.file == "test.py"
        assert args.name == "my-server"
        assert args.transport == "sse"
        assert args.host == "localhost"
        assert args.port == 8080
        assert args.include == "func_*"
        assert args.exclude == "_private"
        assert args.include_private is True
        assert args.check_dependencies is True
        assert args.verbose is True
    
    def test_parser_transport_choices(self):
        """Test transport argument choices."""
        parser = create_parser()
        
        # Valid transports
        for transport in ["stdio", "sse"]:
            args = parser.parse_args(["test.py", "--transport", transport])
            assert args.transport == transport
        
        # Invalid transport should raise
        with pytest.raises(SystemExit):
            parser.parse_args(["test.py", "--transport", "invalid"])


class TestRunFactory:
    """Test the run_factory function."""
    
    def test_run_factory_basic(self):
        """Test basic factory run with stdio transport."""
        args = argparse.Namespace(
            file="test.py",
            name=None,
            transport="stdio",
            host="localhost",
            port=8000,
            include=None,
            exclude=None,
            include_private=False,
            check_dependencies=False,
            verbose=False
        )
        
        with patch('quickmcp.cli_factory.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_file.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            with patch('quickmcp.cli_factory.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.stem = "test"
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance
                
                run_factory(args)
                
                mock_factory_class.assert_called_once_with(name="test-mcp")
                mock_factory.from_file.assert_called_once_with(
                    "test.py",
                    include_pattern=None,
                    exclude_pattern=None,
                    include_private=False
                )
                mock_server.run_stdio.assert_called_once()
    
    def test_run_factory_with_name(self):
        """Test factory run with custom name."""
        args = argparse.Namespace(
            file="test.py",
            name="custom-server",
            transport="stdio",
            host="localhost",
            port=8000,
            include=None,
            exclude=None,
            include_private=False,
            check_dependencies=False,
            verbose=False
        )
        
        with patch('quickmcp.cli_factory.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_file.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            with patch('quickmcp.cli_factory.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance
                
                run_factory(args)
                
                mock_factory_class.assert_called_once_with(name="custom-server")
    
    def test_run_factory_with_patterns(self):
        """Test factory run with include/exclude patterns."""
        args = argparse.Namespace(
            file="test.py",
            name=None,
            transport="stdio",
            host="localhost",
            port=8000,
            include="test_*",
            exclude="_internal",
            include_private=True,
            check_dependencies=False,
            verbose=False
        )
        
        with patch('quickmcp.cli_factory.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_file.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            with patch('quickmcp.cli_factory.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.stem = "test"
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance
                
                run_factory(args)
                
                mock_factory.from_file.assert_called_once_with(
                    "test.py",
                    include_pattern="test_*",
                    exclude_pattern="_internal",
                    include_private=True
                )
    
    def test_run_factory_sse_transport(self):
        """Test factory run with SSE transport."""
        args = argparse.Namespace(
            file="test.py",
            name=None,
            transport="sse",
            host="0.0.0.0",
            port=9000,
            include=None,
            exclude=None,
            include_private=False,
            check_dependencies=False,
            verbose=False
        )
        
        with patch('quickmcp.cli_factory.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_file.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            with patch('quickmcp.cli_factory.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.stem = "test"
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance
                
                run_factory(args)
                
                mock_server.run_sse.assert_called_once_with(
                    host="0.0.0.0",
                    port=9000
                )
    
    def test_run_factory_check_dependencies(self):
        """Test factory run with dependency checking."""
        args = argparse.Namespace(
            file="test.py",
            name=None,
            transport="stdio",
            host="localhost",
            port=8000,
            include=None,
            exclude=None,
            include_private=False,
            check_dependencies=True,
            verbose=False
        )
        
        with patch('quickmcp.cli_factory.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_file.return_value = mock_server
            mock_factory.check_dependencies.return_value = []
            mock_factory_class.return_value = mock_factory
            
            with patch('quickmcp.cli_factory.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.stem = "test"
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance
                
                with patch('quickmcp.cli_factory.logger') as mock_logger:
                    run_factory(args)
                    
                    mock_factory.check_dependencies.assert_called_once()
                    mock_logger.info.assert_called_with("All dependencies are satisfied")
    
    def test_run_factory_missing_dependencies(self):
        """Test factory run with missing dependencies."""
        args = argparse.Namespace(
            file="test.py",
            name=None,
            transport="stdio",
            host="localhost",
            port=8000,
            include=None,
            exclude=None,
            include_private=False,
            check_dependencies=True,
            verbose=False
        )
        
        missing_dep = MagicMock()
        missing_dep.module = "numpy"
        missing_dep.suggested_install = "numpy"
        
        with patch('quickmcp.cli_factory.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_file.return_value = mock_server
            mock_factory.check_dependencies.return_value = [missing_dep]
            mock_factory_class.return_value = mock_factory
            
            with patch('quickmcp.cli_factory.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.stem = "test"
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance
                
                with patch('quickmcp.cli_factory.logger') as mock_logger:
                    with pytest.raises(SystemExit):
                        run_factory(args)
                    
                    mock_logger.error.assert_called()
    
    def test_run_factory_file_not_found(self):
        """Test factory run with non-existent file."""
        args = argparse.Namespace(
            file="nonexistent.py",
            name=None,
            transport="stdio",
            host="localhost",
            port=8000,
            include=None,
            exclude=None,
            include_private=False,
            check_dependencies=False,
            verbose=False
        )
        
        with patch('quickmcp.cli_factory.Path') as mock_path:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = False
            mock_path.return_value = mock_path_instance
            
            with patch('quickmcp.cli_factory.logger') as mock_logger:
                with pytest.raises(SystemExit):
                    run_factory(args)
                
                mock_logger.error.assert_called_with("File not found: nonexistent.py")
    
    def test_run_factory_verbose_logging(self):
        """Test factory run with verbose logging."""
        args = argparse.Namespace(
            file="test.py",
            name=None,
            transport="stdio",
            host="localhost",
            port=8000,
            include=None,
            exclude=None,
            include_private=False,
            check_dependencies=False,
            verbose=True
        )
        
        with patch('quickmcp.cli_factory.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_file.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            with patch('quickmcp.cli_factory.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.stem = "test"
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance
                
                with patch('quickmcp.cli_factory.logging') as mock_logging:
                    run_factory(args)
                    
                    # Verify DEBUG level was set
                    mock_logging.basicConfig.assert_called_with(level=mock_logging.DEBUG)


class TestCLIFactoryMain:
    """Test the main entry point."""
    
    def test_main_stdio(self):
        """Test main with stdio transport."""
        test_args = ["mcp-factory", "test.py"]
        
        with patch('sys.argv', test_args):
            with patch('quickmcp.cli_factory.run_factory') as mock_run:
                main()
                
                assert mock_run.called
                args = mock_run.call_args[0][0]
                assert args.file == "test.py"
                assert args.transport == "stdio"
    
    def test_main_sse(self):
        """Test main with SSE transport."""
        test_args = ["mcp-factory", "test.py", "--transport", "sse", "--port", "9000"]
        
        with patch('sys.argv', test_args):
            with patch('quickmcp.cli_factory.run_factory') as mock_run:
                main()
                
                assert mock_run.called
                args = mock_run.call_args[0][0]
                assert args.file == "test.py"
                assert args.transport == "sse"
                assert args.port == 9000
    
    def test_main_with_patterns(self):
        """Test main with include/exclude patterns."""
        test_args = [
            "mcp-factory", "test.py",
            "--include", "api_*",
            "--exclude", "_internal",
            "--include-private"
        ]
        
        with patch('sys.argv', test_args):
            with patch('quickmcp.cli_factory.run_factory') as mock_run:
                main()
                
                assert mock_run.called
                args = mock_run.call_args[0][0]
                assert args.include == "api_*"
                assert args.exclude == "_internal"
                assert args.include_private is True
    
    def test_main_help(self):
        """Test main with help flag."""
        test_args = ["mcp-factory", "--help"]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 0
    
    def test_main_error_handling(self):
        """Test main with error in run_factory."""
        test_args = ["mcp-factory", "test.py"]
        
        with patch('sys.argv', test_args):
            with patch('quickmcp.cli_factory.run_factory') as mock_run:
                mock_run.side_effect = Exception("Test error")
                
                with patch('quickmcp.cli_factory.logger') as mock_logger:
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    mock_logger.error.assert_called()
                    assert exc_info.value.code == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])