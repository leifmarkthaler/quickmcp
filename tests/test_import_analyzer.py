"""
Tests for the import analyzer module.
"""

import pytest
import tempfile
from pathlib import Path
from typing import List, Set

from quickmcp.factory.import_analyzer import ImportAnalyzer
from quickmcp.factory.config import FactoryConfig
from quickmcp.factory.errors import MissingDependency


class TestImportAnalyzer:
    """Test the ImportAnalyzer class."""
    
    def test_analyze_simple_imports(self, tmp_path):
        """Test analyzing simple import statements."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # All these are stdlib, so should be no missing deps
        assert len(missing_deps) == 0
    
    def test_analyze_third_party_imports(self, tmp_path):
        """Test analyzing third-party imports."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import requests
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # Check that third-party imports are detected as missing (if not installed)
        module_names = [dep.module for dep in missing_deps]
        
        # At least some of these should be detected as missing
        # (depending on what's installed in test environment)
        assert len(missing_deps) > 0
    
    def test_analyze_try_except_imports(self, tmp_path):
        """Test analyzing imports in try-except blocks."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import os  # Required

try:
    import numpy as np  # Optional
except ImportError:
    np = None

try:
    from PIL import Image
except:
    Image = None
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # Check that optional imports are marked as such
        for dep in missing_deps:
            if dep.module in ["numpy", "PIL"]:
                assert dep.import_type == "optional"
    
    def test_analyze_conditional_imports(self, tmp_path):
        """Test analyzing conditional imports."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import sys

if sys.platform == "win32":
    import winreg
else:
    import termios

def func():
    import json  # Local import
    return json.dumps({})

class MyClass:
    def method(self):
        import csv  # Method-level import
        return csv
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # Platform-specific imports might be missing
        module_names = [dep.module for dep in missing_deps]
        
        # json and csv are stdlib, should not be in missing
        assert "json" not in module_names
        assert "csv" not in module_names
    
    def test_analyze_from_imports(self, tmp_path):
        """Test analyzing 'from ... import ...' statements."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
from os import path, environ
from sys import argv, exit
from typing import List, Dict, Optional
from pathlib import Path, PurePath
from collections.abc import Mapping, Sequence
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # All stdlib, should be no missing deps
        assert len(missing_deps) == 0
    
    def test_analyze_relative_imports(self, tmp_path):
        """Test analyzing relative imports."""
        test_file = tmp_path / "submodule" / "test.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("""
from . import sibling
from .. import parent
from ..other import something
from .nested.module import function
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # Relative imports within same package are not external dependencies
        # They should not be reported as missing
        assert len(missing_deps) == 0
    
    def test_custom_pip_mappings(self, tmp_path):
        """Test custom pip mappings in config."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import cv2
import sklearn
from bs4 import BeautifulSoup
""")
        
        config = FactoryConfig(
            custom_pip_mappings={
                "cv2": "opencv-python",
                "bs4": "beautifulsoup4"
            }
        )
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # Check that pip names are correctly mapped
        for dep in missing_deps:
            if dep.module == "cv2":
                assert dep.suggested_install == "opencv-python"
            elif dep.module == "bs4":
                assert dep.suggested_install == "beautifulsoup4"
            elif dep.module == "sklearn":
                assert dep.suggested_install == "scikit-learn"  # Default mapping
    
    def test_additional_stdlib_modules(self, tmp_path):
        """Test additional stdlib modules in config."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import os
import custom_stdlib_module
import third_party_module
""")
        
        config = FactoryConfig(
            additional_stdlib_modules={"custom_stdlib_module"}
        )
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # custom_stdlib_module should not be in missing deps
        module_names = [dep.module for dep in missing_deps]
        assert "custom_stdlib_module" not in module_names
        assert "third_party_module" in module_names
    
    def test_analyze_with_aliases(self, tmp_path):
        """Test analyzing imports with aliases."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from typing import List as ListType
import os.path as ospath
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # Check that base modules are identified correctly
        module_names = [dep.module for dep in missing_deps]
        
        # Should identify numpy, pandas, matplotlib (if not installed)
        # Should not include os.path (stdlib)
        assert "os.path" not in module_names
        assert "os" not in module_names
    
    def test_analyze_star_imports(self, tmp_path):
        """Test analyzing star imports."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
from os import *
from typing import *
from some_module import *
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # os and typing are stdlib
        module_names = [dep.module for dep in missing_deps]
        assert "os" not in module_names
        assert "typing" not in module_names
        assert "some_module" in module_names
    
    def test_analyze_future_imports(self, tmp_path):
        """Test analyzing __future__ imports."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
from __future__ import annotations
from __future__ import print_function, division
import os
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # __future__ imports should not be considered dependencies
        module_names = [dep.module for dep in missing_deps]
        assert "__future__" not in module_names
        assert len(missing_deps) == 0
    
    def test_analyze_type_checking_imports(self, tmp_path):
        """Test analyzing TYPE_CHECKING conditional imports."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import expensive_module
    from another_module import SomeType
    
import regular_module
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # TYPE_CHECKING imports should be marked as optional
        for dep in missing_deps:
            if dep.module in ["expensive_module", "another_module"]:
                assert dep.import_type == "optional"
            elif dep.module == "regular_module":
                assert dep.import_type in ["import", "from_import"]  # Regular imports are marked as their type
    
    def test_analyze_nested_try_except(self, tmp_path):
        """Test analyzing nested try-except blocks."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
try:
    try:
        import primary_module
    except ImportError:
        import fallback_module
except:
    import last_resort_module
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # All should be optional due to try-except
        for dep in missing_deps:
            assert dep.import_type == "optional"
    
    def test_analyze_multiline_imports(self, tmp_path):
        """Test analyzing multiline import statements."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
from typing import (
    List, Dict, Set,
    Tuple, Optional,
    Union, Any
)

from collections import (
    defaultdict,
    Counter,
    OrderedDict
)
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # All are stdlib, should be no missing deps
        assert len(missing_deps) == 0
    
    def test_cache_behavior(self, tmp_path):
        """Test caching of dependency analysis."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import numpy
import pandas
""")
        
        # With caching enabled
        config_cached = FactoryConfig(cache_dependency_analysis=True)
        analyzer_cached = ImportAnalyzer(config_cached)
        
        # First analysis
        deps1 = analyzer_cached.analyze_file(str(test_file))
        
        # Second analysis (should use cache)
        deps2 = analyzer_cached.analyze_file(str(test_file))
        
        # Results should be the same
        assert len(deps1) == len(deps2)
        assert [d.module for d in deps1] == [d.module for d in deps2]
        
        # Without caching
        config_no_cache = FactoryConfig(cache_dependency_analysis=False)
        analyzer_no_cache = ImportAnalyzer(config_no_cache)
        
        deps3 = analyzer_no_cache.analyze_file(str(test_file))
        deps4 = analyzer_no_cache.analyze_file(str(test_file))
        
        # Results should still be the same
        assert len(deps3) == len(deps4)
    
    def test_analyze_empty_file(self, tmp_path):
        """Test analyzing an empty file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        assert len(missing_deps) == 0
    
    def test_analyze_syntax_error(self, tmp_path):
        """Test analyzing a file with syntax errors."""
        test_file = tmp_path / "invalid.py"
        test_file.write_text("""
import os
this is not valid python code
import sys
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        # Should handle syntax errors gracefully
        # Might return empty or partial results
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # Should at least not crash
        assert isinstance(missing_deps, list)
    
    def test_get_install_commands(self, tmp_path):
        """Test getting install commands for missing dependencies."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import numpy
import pandas
import sklearn
try:
    import optional_module
except:
    pass
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        if missing_deps:
            # Test with uv
            commands_uv = analyzer.get_install_commands(missing_deps, use_uv=True)
            for cmd in commands_uv.values():
                assert cmd.startswith("uv pip install")
            
            # Test with pip
            commands_pip = analyzer.get_install_commands(missing_deps, use_uv=False)
            for cmd in commands_pip.values():
                assert cmd.startswith("pip install")
                assert not cmd.startswith("uv")
    
    def test_common_pip_mappings(self, tmp_path):
        """Test common pip package name mappings."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import cv2
import sklearn
import PIL
import yaml
import bs4
""")
        
        config = FactoryConfig()
        analyzer = ImportAnalyzer(config)
        
        missing_deps = analyzer.analyze_file(str(test_file))
        
        # Check known mappings
        mappings = {
            "cv2": "opencv-python",
            "sklearn": "scikit-learn",
            "PIL": "Pillow",  # Note the capital P
            "yaml": "PyYAML",  # Note the capital letters
            "bs4": "beautifulsoup4"
        }
        
        for dep in missing_deps:
            if dep.module in mappings:
                assert dep.suggested_install == mappings[dep.module]


class TestImportAnalyzerIntegration:
    """Integration tests for ImportAnalyzer."""
    
    def test_with_factory_config(self, tmp_path):
        """Test ImportAnalyzer with different factory configurations."""
        from quickmcp.factory.config import create_safe_config, create_permissive_config
        
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import numpy
try:
    import optional_module
except:
    pass
""")
        
        # Safe config
        safe_analyzer = ImportAnalyzer(create_safe_config())
        safe_deps = safe_analyzer.analyze_file(str(test_file))
        
        # Permissive config
        perm_analyzer = ImportAnalyzer(create_permissive_config())
        perm_deps = perm_analyzer.analyze_file(str(test_file))
        
        # Both should identify the same dependencies
        assert len(safe_deps) == len(perm_deps)
    
    def test_with_real_modules(self):
        """Test with real Python modules that should be detected correctly."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
# Standard library - should not be missing
import os
import sys
import json
import datetime
from pathlib import Path
from typing import List, Dict

# These are in our test environment - should not be missing
import pytest

# These might be missing (uncommon packages)
try:
    import uncommon_package_xyz
except:
    pass
""")
            test_file = f.name
        
        try:
            config = FactoryConfig()
            analyzer = ImportAnalyzer(config)
            
            missing_deps = analyzer.analyze_file(test_file)
            
            # Check that stdlib is not in missing
            module_names = [dep.module for dep in missing_deps]
            assert "os" not in module_names
            assert "sys" not in module_names
            assert "json" not in module_names
            assert "datetime" not in module_names
            assert "pathlib" not in module_names
            assert "typing" not in module_names
            
            # pytest should not be missing in test environment
            assert "pytest" not in module_names
            
            # Uncommon package should be missing
            assert "uncommon_package_xyz" in module_names
            
        finally:
            Path(test_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])