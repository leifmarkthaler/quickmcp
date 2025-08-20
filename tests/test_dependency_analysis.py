"""
Test dependency analysis functionality in MCP Factory.
"""

import pytest
import tempfile
from pathlib import Path
import sys

from quickmcp.factory import (
    MCPFactory, ImportAnalyzer, MissingDependency, MissingDependencyError,
    analyze_dependencies, check_dependencies, get_install_command
)


class TestImportAnalyzer:
    """Test the ImportAnalyzer class."""
    
    def test_analyze_required_imports(self, tmp_path):
        """Test analysis of required imports that are missing."""
        test_file = tmp_path / "test_required.py"
        test_file.write_text('''
import non_existent_module
import aiohttp
from requests import Session

def my_function():
    return "hello"
''')
        
        analyzer = ImportAnalyzer()
        deps = analyzer.analyze_file(str(test_file))
        
        # Should find missing modules (assuming they're not installed)
        module_names = [dep.module for dep in deps]
        
        # non_existent_module should always be missing
        assert "non_existent_module" in module_names
        
        # Check that all dependencies are marked as required (not optional)
        required_deps = [dep for dep in deps if dep.import_type != "optional"]
        assert len(required_deps) > 0
    
    def test_analyze_optional_imports(self, tmp_path):
        """Test analysis of optional imports in try/except blocks."""
        test_file = tmp_path / "test_optional.py"
        test_file.write_text('''
try:
    import non_existent_module
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

try:
    from another_missing_module import Something
except ImportError:
    Something = None

def my_function():
    return "hello"
''')
        
        analyzer = ImportAnalyzer()
        deps = analyzer.analyze_file(str(test_file))
        
        # Should detect both as optional
        optional_deps = [dep for dep in deps if dep.import_type == "optional"]
        module_names = [dep.module for dep in optional_deps]
        
        assert "non_existent_module" in module_names
        assert "another_missing_module" in module_names
    
    def test_stdlib_modules_ignored(self, tmp_path):
        """Test that standard library modules are not reported as missing."""
        test_file = tmp_path / "test_stdlib.py"
        test_file.write_text('''
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List

def my_function():
    return "hello"
''')
        
        analyzer = ImportAnalyzer()
        deps = analyzer.analyze_file(str(test_file))
        
        # Should find no missing dependencies (all stdlib)
        assert len(deps) == 0
    
    def test_pip_mappings(self):
        """Test that pip install suggestions are correct."""
        analyzer = ImportAnalyzer()
        
        # Test common mappings - these are now private attributes
        assert analyzer._pip_mappings.get("cv2") == "opencv-python"
        assert analyzer._pip_mappings.get("PIL") == "Pillow"
        assert analyzer._pip_mappings.get("sklearn") == "scikit-learn"
        assert analyzer._pip_mappings.get("yaml") == "PyYAML"
        
        # Test that unknown modules fall back to the module name
        assert analyzer._pip_mappings.get("unknown_module") is None
    
    def test_line_numbers_and_source(self, tmp_path):
        """Test that line numbers and source lines are captured."""
        test_file = tmp_path / "test_lines.py"
        test_file.write_text('''# Line 1
import non_existent_module  # Line 2
from another_missing import something  # Line 3

def my_function():  # Line 5
    return "hello"
''')
        
        analyzer = ImportAnalyzer()
        deps = analyzer.analyze_file(str(test_file))
        
        # Should have line numbers and source
        for dep in deps:
            assert dep.line_number is not None
            assert dep.source_line is not None
            assert dep.line_number > 0
        
        # Check specific line numbers
        line_numbers = [dep.line_number for dep in deps]
        assert 2 in line_numbers  # import non_existent_module
        assert 3 in line_numbers  # from another_missing import something


class TestMissingDependencyError:
    """Test the MissingDependencyError exception."""
    
    def test_format_error_message(self):
        """Test formatting of error messages."""
        deps = [
            MissingDependency(
                module="aiohttp",
                import_type="import",
                line_number=5,
                source_line="import aiohttp",
                suggested_install="aiohttp"
            ),
            MissingDependency(
                module="requests",
                import_type="optional",
                line_number=10,
                source_line="import requests",
                suggested_install="requests"
            )
        ]
        
        error = MissingDependencyError("Test error", deps)
        message = error.format_error_message()
        
        assert "Test error" in message
        assert "Required dependencies" in message
        assert "Optional dependencies" in message
        assert "aiohttp" in message
        assert "requests" in message
        assert "pip install aiohttp" in message
        assert "Line 5: import aiohttp" in message
    
    def test_empty_dependencies(self):
        """Test formatting with no dependencies."""
        error = MissingDependencyError("Test error", [])
        message = error.format_error_message()
        
        assert message == "Test error"


class TestMCPFactoryDependencyChecking:
    """Test dependency checking in MCPFactory."""
    
    def test_factory_with_missing_dependencies(self, tmp_path):
        """Test that factory raises MissingDependencyError for required imports."""
        test_file = tmp_path / "test_missing.py"
        test_file.write_text('''
import non_existent_module

def my_function():
    return "hello"
''')
        
        from quickmcp.factory import FactoryConfig
        config = FactoryConfig(check_dependencies=True)
        factory = MCPFactory(config=config)
        
        with pytest.raises(MissingDependencyError) as exc_info:
            factory.from_module(str(test_file))
        
        error = exc_info.value
        assert len(error.missing_dependencies) > 0
        assert "non_existent_module" in [dep.module for dep in error.missing_dependencies]
    
    def test_factory_with_optional_dependencies(self, tmp_path):
        """Test that factory succeeds with optional imports."""
        test_file = tmp_path / "test_optional.py"
        test_file.write_text('''
try:
    import non_existent_module
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

def my_function():
    if HAS_MODULE:
        return "with module"
    return "without module"
''')
        
        from quickmcp.factory import FactoryConfig
        config = FactoryConfig(check_dependencies=True)
        factory = MCPFactory(config=config)
        server = factory.from_module(str(test_file))
        
        # Should succeed and create server
        assert server is not None
        assert "my_function" in server.list_tools()
    
    def test_factory_ignore_dependencies(self, tmp_path):
        """Test that factory can ignore dependency checking."""
        test_file = tmp_path / "test_ignore.py"
        test_file.write_text('''
# This will fail when loaded, but we're testing that
# dependency checking can be disabled
import non_existent_module

def my_function():
    return "hello"
''')
        
        from quickmcp.factory import FactoryConfig
        config = FactoryConfig(check_dependencies=False)
        factory = MCPFactory(config=config)
        
        # Should not raise MissingDependencyError, but will raise ModuleLoadError due to missing import
        from quickmcp.factory.errors import ModuleLoadError
        with pytest.raises(ModuleLoadError):
            factory.from_module(str(test_file))
    
    def test_analyze_dependencies_method(self, tmp_path):
        """Test the analyze_dependencies method."""
        test_file = tmp_path / "test_analyze.py"
        test_file.write_text('''
import non_existent_module
try:
    import another_missing
except ImportError:
    pass

def my_function():
    return "hello"
''')
        
        factory = MCPFactory()
        deps = factory.analyze_dependencies(str(test_file))
        
        assert len(deps) >= 2
        module_names = [dep.module for dep in deps]
        assert "non_existent_module" in module_names
        assert "another_missing" in module_names
        
        # Check types
        types = [dep.import_type for dep in deps]
        assert "import" in types
        assert "optional" in types
    
    def test_check_dependencies_method(self, tmp_path):
        """Test the check_dependencies method."""
        test_file = tmp_path / "test_check.py"
        test_file.write_text('''
import non_existent_module
try:
    import another_missing
except ImportError:
    pass

def my_function():
    return "hello"
''')
        
        factory = MCPFactory()
        report = factory.check_dependencies(str(test_file))
        
        assert "file" in report
        assert "total_missing" in report
        assert "required_missing" in report
        assert "optional_missing" in report
        assert "can_load" in report
        assert "install_command" in report
        
        assert report["total_missing"] >= 2
        assert report["required_missing"] >= 1
        assert report["optional_missing"] >= 1
        assert report["can_load"] is False
        assert report["install_command"] is not None


class TestStandaloneFunctions:
    """Test standalone utility functions."""
    
    def test_analyze_dependencies_function(self, tmp_path):
        """Test the standalone analyze_dependencies function."""
        test_file = tmp_path / "test_standalone.py"
        test_file.write_text('''
import non_existent_module

def my_function():
    return "hello"
''')
        
        deps = analyze_dependencies(str(test_file))
        
        assert len(deps) > 0
        assert "non_existent_module" in [dep.module for dep in deps]
    
    def test_check_dependencies_function(self, tmp_path):
        """Test the standalone check_dependencies function."""
        test_file = tmp_path / "test_standalone_check.py"
        test_file.write_text('''
import non_existent_module

def my_function():
    return "hello"
''')
        
        report = check_dependencies(str(test_file))
        
        assert isinstance(report, dict)
        assert report["total_missing"] > 0
        assert report["can_load"] is False
    
    def test_get_install_command_function(self, tmp_path):
        """Test the get_install_command function."""
        test_file = tmp_path / "test_install_cmd.py"
        test_file.write_text('''
import non_existent_module
import another_missing

def my_function():
    return "hello"
''')
        
        cmd = get_install_command(str(test_file))
        
        assert isinstance(cmd, dict)
        assert "required" in cmd
        required_cmd = cmd["required"]
        assert required_cmd.startswith("pip install")
        assert "non_existent_module" in required_cmd
        assert "another_missing" in required_cmd
    
    def test_get_install_command_no_missing(self, tmp_path):
        """Test get_install_command when no dependencies are missing."""
        test_file = tmp_path / "test_no_missing.py"
        test_file.write_text('''
import os
import sys

def my_function():
    return "hello"
''')
        
        cmd = get_install_command(str(test_file))
        
        assert isinstance(cmd, dict)
        assert len(cmd) == 0  # Empty dict when no missing dependencies


class TestComplexDependencyScenarios:
    """Test complex dependency scenarios."""
    
    def test_mixed_required_and_optional(self, tmp_path):
        """Test file with both required and optional imports."""
        test_file = tmp_path / "test_mixed.py"
        test_file.write_text('''
# Required import - will cause failure
import definitely_missing_module

# Optional imports - handled gracefully
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    from requests import Session
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

def my_function():
    if HAS_AIOHTTP:
        return "with aiohttp"
    elif HAS_REQUESTS:
        return "with requests"
    return "basic version"
''')
        
        from quickmcp.factory import FactoryConfig
        config = FactoryConfig(check_dependencies=True)
        factory = MCPFactory(config=config)
        
        # Should fail due to required import
        with pytest.raises(MissingDependencyError) as exc_info:
            factory.from_module(str(test_file))
        
        error = exc_info.value
        deps = error.missing_dependencies
        
        # Check that we have both required and optional dependencies
        required = [dep for dep in deps if dep.import_type != "optional"]
        optional = [dep for dep in deps if dep.import_type == "optional"]
        
        assert len(required) > 0
        assert "definitely_missing_module" in [dep.module for dep in required]
        
        # Optional dependencies should be detected too
        # (though they wouldn't prevent loading if no required deps were missing)
        # Note: aiohttp and requests might actually be installed, so we can't assert on them
    
    def test_submodule_imports(self, tmp_path):
        """Test imports of submodules."""
        test_file = tmp_path / "test_submodules.py"
        test_file.write_text('''
import missing_package.submodule
from another_missing.sub.module import something

def my_function():
    return "hello"
''')
        
        analyzer = ImportAnalyzer()
        deps = analyzer.analyze_file(str(test_file))
        
        # Should detect the top-level packages
        module_names = [dep.module for dep in deps]
        assert "missing_package" in module_names
        assert "another_missing" in module_names
    
    def test_suggestion_mapping(self, tmp_path):
        """Test that pip install suggestions work correctly."""
        test_file = tmp_path / "test_suggestions.py"
        test_file.write_text('''
import cv2
from PIL import Image
import sklearn
import yaml

def my_function():
    return "hello"
''')
        
        deps = analyze_dependencies(str(test_file))
        
        # Find specific dependencies and check suggestions
        dep_map = {dep.module: dep.suggested_install for dep in deps}
        
        if "cv2" in dep_map:
            assert dep_map["cv2"] == "opencv-python"
        if "PIL" in dep_map:
            assert dep_map["PIL"] == "Pillow"
        if "sklearn" in dep_map:
            assert dep_map["sklearn"] == "scikit-learn"
        if "yaml" in dep_map:
            assert dep_map["yaml"] == "PyYAML"
    
    def test_large_file_performance(self, tmp_path):
        """Test that analysis works reasonably fast on larger files."""
        import time
        
        # Generate a file with many imports
        imports = []
        for i in range(100):
            if i % 3 == 0:
                imports.append(f"import missing_module_{i}")
            elif i % 3 == 1:
                imports.append(f"from missing_pkg_{i} import something")
            else:
                imports.append(f"import os")  # stdlib module
        
        imports.append("\ndef my_function():\n    return 'hello'")
        content = "\n".join(imports)
        
        test_file = tmp_path / "test_large.py"
        test_file.write_text(content)
        
        start = time.time()
        deps = analyze_dependencies(str(test_file))
        end = time.time()
        
        # Should complete in reasonable time (< 1 second for 100 imports)
        assert end - start < 1.0
        
        # Should find the missing modules but not stdlib
        missing_count = len([dep for dep in deps if dep.module.startswith("missing_")])
        assert missing_count > 50  # Should find most of the missing modules


if __name__ == "__main__":
    pytest.main([__file__, "-v"])