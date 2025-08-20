"""
Tests for factory utility functions.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import sys
from io import StringIO

from quickmcp.factory.utils import (
    create_mcp_from_module,
    create_mcp_from_object,
    analyze_dependencies,
    check_dependencies,
    print_dependency_report,
    get_install_command,
    validate_factory_setup,
    mcp_tool,
    create_factory_for_development,
    create_safe_factory,
    create_factory_with_config
)
from quickmcp.factory.config import FactoryConfig
from quickmcp.factory.errors import MissingDependencyError


class TestCreateMCPFromModule:
    """Test create_mcp_from_module function."""
    
    def test_create_from_file_path(self, tmp_path):
        """Test creating MCP from a file path."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def hello():
    return "world"

def add(a: int, b: int) -> int:
    return a + b
""")
        
        with patch('quickmcp.factory.utils.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_file.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            result = create_mcp_from_module(str(test_file))
            
            mock_factory_class.assert_called_once()
            mock_factory.from_file.assert_called_once_with(str(test_file))
            assert result == mock_server
    
    def test_create_from_module_name(self):
        """Test creating MCP from a module name."""
        with patch('quickmcp.factory.utils.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_module.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            result = create_mcp_from_module("os.path")
            
            mock_factory.from_module.assert_called_once_with("os.path")
            assert result == mock_server
    
    def test_create_with_custom_config(self):
        """Test creating MCP with custom configuration."""
        config = FactoryConfig(strict_type_conversion=True)
        
        with patch('quickmcp.factory.utils.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_module.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            result = create_mcp_from_module("test_module", config=config)
            
            mock_factory_class.assert_called_once_with(
                name="test_module-mcp",
                config=config
            )
            assert result == mock_server
    
    def test_create_with_patterns(self):
        """Test creating MCP with include/exclude patterns."""
        with patch('quickmcp.factory.utils.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_module.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            result = create_mcp_from_module(
                "test_module",
                include_pattern="test_*",
                exclude_pattern="_private"
            )
            
            mock_factory.from_module.assert_called_once_with(
                "test_module",
                include_pattern="test_*",
                exclude_pattern="_private"
            )
            assert result == mock_server


class TestCreateMCPFromObject:
    """Test create_mcp_from_object function."""
    
    def test_create_from_dict(self):
        """Test creating MCP from a dictionary of functions."""
        def func1():
            return "one"
        
        def func2(x: int) -> int:
            return x * 2
        
        funcs = {"func1": func1, "func2": func2}
        
        with patch('quickmcp.factory.utils.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_functions.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            result = create_mcp_from_object(funcs)
            
            mock_factory.from_functions.assert_called_once_with(funcs)
            assert result == mock_server
    
    def test_create_from_class(self):
        """Test creating MCP from a class."""
        class TestClass:
            def method1(self):
                return "test"
            
            def method2(self, x: int) -> int:
                return x + 1
        
        with patch('quickmcp.factory.utils.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_class.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            result = create_mcp_from_object(TestClass)
            
            mock_factory.from_class.assert_called_once_with(TestClass)
            assert result == mock_server
    
    def test_create_from_instance(self):
        """Test creating MCP from a class instance."""
        class TestClass:
            def method(self):
                return "test"
        
        instance = TestClass()
        
        with patch('quickmcp.factory.utils.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_instance.return_value = mock_server
            mock_factory_class.return_value = mock_factory
            
            result = create_mcp_from_object(instance, name="test-server")
            
            mock_factory_class.assert_called_once_with(name="test-server")
            mock_factory.from_instance.assert_called_once_with(instance)
            assert result == mock_server
    
    def test_create_invalid_object(self):
        """Test creating MCP from invalid object type."""
        with pytest.raises(ValueError, match="Unsupported object type"):
            create_mcp_from_object(123)  # Invalid type


class TestDependencyFunctions:
    """Test dependency analysis functions."""
    
    def test_analyze_dependencies(self, tmp_path):
        """Test analyze_dependencies function."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import os
import numpy
from sklearn import metrics
""")
        
        with patch('quickmcp.factory.utils.ImportAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_dep1 = MagicMock()
            mock_dep1.module = "numpy"
            mock_dep2 = MagicMock()
            mock_dep2.module = "sklearn"
            mock_analyzer.analyze_file.return_value = [mock_dep1, mock_dep2]
            mock_analyzer_class.return_value = mock_analyzer
            
            deps = analyze_dependencies(str(test_file))
            
            mock_analyzer.analyze_file.assert_called_once_with(str(test_file))
            assert len(deps) == 2
            assert deps[0].module == "numpy"
            assert deps[1].module == "sklearn"
    
    def test_check_dependencies(self, tmp_path):
        """Test check_dependencies function."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import numpy")
        
        with patch('quickmcp.factory.utils.ImportAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_dep = MagicMock()
            mock_dep.module = "numpy"
            mock_dep.import_type = "import"
            mock_analyzer.analyze_file.return_value = [mock_dep]
            mock_analyzer_class.return_value = mock_analyzer
            
            # Should raise for missing required dependency
            with pytest.raises(MissingDependencyError) as exc_info:
                check_dependencies(str(test_file))
            
            assert "numpy" in str(exc_info.value)
    
    def test_check_dependencies_optional(self, tmp_path):
        """Test check_dependencies with optional imports."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
try:
    import numpy
except ImportError:
    numpy = None
""")
        
        with patch('quickmcp.factory.utils.ImportAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_dep = MagicMock()
            mock_dep.module = "numpy"
            mock_dep.import_type = "optional"
            mock_analyzer.analyze_file.return_value = [mock_dep]
            mock_analyzer_class.return_value = mock_analyzer
            
            # Should not raise for optional dependency
            check_dependencies(str(test_file))
    
    def test_print_dependency_report(self, tmp_path, capsys):
        """Test print_dependency_report function."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import os
import numpy
try:
    import optional_lib
except:
    pass
""")
        
        with patch('quickmcp.factory.utils.ImportAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            
            mock_dep1 = MagicMock()
            mock_dep1.module = "numpy"
            mock_dep1.import_type = "import"
            mock_dep1.suggested_install = "numpy"
            mock_dep1.is_dev_dependency = False
            
            mock_dep2 = MagicMock()
            mock_dep2.module = "optional_lib"
            mock_dep2.import_type = "optional"
            mock_dep2.suggested_install = "optional-lib"
            mock_dep2.is_dev_dependency = False
            
            mock_analyzer.analyze_file.return_value = [mock_dep1, mock_dep2]
            mock_analyzer_class.return_value = mock_analyzer
            
            print_dependency_report(str(test_file))
            
            captured = capsys.readouterr()
            assert "numpy" in captured.out
            assert "optional_lib" in captured.out
            assert "Required" in captured.out
            assert "Optional" in captured.out
    
    def test_get_install_command(self, tmp_path):
        """Test get_install_command function."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import numpy\nimport pandas")
        
        with patch('quickmcp.factory.utils.ImportAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            
            mock_dep1 = MagicMock()
            mock_dep1.module = "numpy"
            mock_dep1.suggested_install = "numpy"
            
            mock_dep2 = MagicMock()
            mock_dep2.module = "pandas"
            mock_dep2.suggested_install = "pandas"
            
            mock_analyzer.analyze_file.return_value = [mock_dep1, mock_dep2]
            mock_analyzer.get_install_commands.return_value = {
                "numpy": "pip install numpy",
                "pandas": "pip install pandas"
            }
            mock_analyzer_class.return_value = mock_analyzer
            
            # Test with pip
            with patch('shutil.which', return_value=None):
                cmd = get_install_command(str(test_file))
                assert "pip install" in cmd
                assert "numpy" in cmd
                assert "pandas" in cmd
            
            # Test with uv
            with patch('shutil.which', return_value="/usr/bin/uv"):
                cmd = get_install_command(str(test_file))
                assert "uv pip install" in cmd
    
    def test_get_install_command_no_missing(self, tmp_path):
        """Test get_install_command with no missing dependencies."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import os")
        
        with patch('quickmcp.factory.utils.ImportAnalyzer') as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze_file.return_value = []
            mock_analyzer_class.return_value = mock_analyzer
            
            cmd = get_install_command(str(test_file))
            assert cmd == ""


class TestValidateFactorySetup:
    """Test validate_factory_setup function."""
    
    def test_validate_success(self):
        """Test successful validation."""
        factory = MagicMock()
        factory.list_tools.return_value = ["tool1", "tool2"]
        factory.config = FactoryConfig()
        
        # Should not raise
        validate_factory_setup(factory)
    
    def test_validate_no_tools(self):
        """Test validation with no tools."""
        factory = MagicMock()
        factory.list_tools.return_value = []
        factory.config = FactoryConfig()
        
        with patch('quickmcp.factory.utils.logger') as mock_logger:
            validate_factory_setup(factory)
            mock_logger.warning.assert_called_with("No tools registered in factory")
    
    def test_validate_strict_config(self):
        """Test validation with strict configuration."""
        factory = MagicMock()
        factory.list_tools.return_value = ["tool1"]
        factory.config = FactoryConfig(strict_type_conversion=True)
        
        with patch('quickmcp.factory.utils.logger') as mock_logger:
            validate_factory_setup(factory)
            mock_logger.info.assert_any_call("Factory validation passed")
            mock_logger.info.assert_any_call("Using strict type conversion")


class TestMCPToolDecorator:
    """Test mcp_tool decorator."""
    
    def test_decorator_basic(self):
        """Test basic decorator usage."""
        @mcp_tool
        def my_function(x: int) -> int:
            return x * 2
        
        # Function should be marked
        assert hasattr(my_function, '__mcp_tool__')
        assert my_function.__mcp_tool__ is True
        
        # Function should still work
        assert my_function(5) == 10
    
    def test_decorator_with_options(self):
        """Test decorator with options."""
        @mcp_tool(name="custom_name", description="Custom tool")
        def my_function(x: int) -> int:
            return x * 2
        
        assert hasattr(my_function, '__mcp_tool__')
        assert my_function.__mcp_tool__ is True
        assert my_function.__mcp_name__ == "custom_name"
        assert my_function.__mcp_description__ == "Custom tool"
    
    def test_decorator_on_method(self):
        """Test decorator on class method."""
        class MyClass:
            @mcp_tool
            def my_method(self, x: int) -> int:
                return x * 3
        
        instance = MyClass()
        assert hasattr(instance.my_method, '__mcp_tool__')
        assert instance.my_method(4) == 12
    
    def test_decorator_async_function(self):
        """Test decorator on async function."""
        @mcp_tool
        async def async_func(x: int) -> int:
            return x * 2
        
        assert hasattr(async_func, '__mcp_tool__')
        
        # Test that it's still async
        import asyncio
        result = asyncio.run(async_func(5))
        assert result == 10


class TestFactoryCreationHelpers:
    """Test factory creation helper functions."""
    
    def test_create_factory_for_development(self):
        """Test create_factory_for_development."""
        factory = create_factory_for_development("dev-server")
        
        assert factory is not None
        assert factory.config.strict_type_conversion is False
        assert factory.config.allow_type_coercion is True
        assert factory.config.verbose_errors is True
    
    def test_create_safe_factory(self):
        """Test create_safe_factory."""
        factory = create_safe_factory("safe-server")
        
        assert factory is not None
        assert factory.config.strict_type_conversion is True
        assert factory.config.allow_type_coercion is False
        assert factory.config.check_dependencies is True
    
    def test_create_factory_with_config(self):
        """Test create_factory_with_config."""
        custom_config = FactoryConfig(
            max_file_size_mb=50,
            log_level="DEBUG"
        )
        
        factory = create_factory_with_config("custom-server", custom_config)
        
        assert factory is not None
        assert factory.config.max_file_size_mb == 50
        assert factory.config.log_level == "DEBUG"


class TestIntegration:
    """Integration tests for factory utils."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow from file to server."""
        test_file = tmp_path / "calculator.py"
        test_file.write_text("""
def add(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b

def multiply(a: int, b: int) -> int:
    '''Multiply two numbers.'''
    return a * b

@mcp_tool
def divide(a: float, b: float) -> float:
    '''Divide two numbers.'''
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""")
        
        # Analyze dependencies
        deps = analyze_dependencies(str(test_file))
        assert len(deps) == 0  # No external dependencies
        
        # Create server from module
        with patch('quickmcp.factory.utils.MCPFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_server = MagicMock()
            mock_factory.from_file.return_value = mock_server
            mock_factory.list_tools.return_value = ["add", "multiply", "divide"]
            mock_factory_class.return_value = mock_factory
            
            server = create_mcp_from_module(str(test_file))
            
            # Validate setup
            validate_factory_setup(mock_factory)
            
            assert server is not None
            mock_factory.from_file.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])