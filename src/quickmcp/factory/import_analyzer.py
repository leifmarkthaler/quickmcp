"""
Import analysis for detecting missing dependencies.
"""

import ast
import importlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Dict, Any

from .config import FactoryConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class MissingDependency:
    """Information about a missing dependency."""
    module: str
    import_type: str  # "import", "from_import", "optional"
    line_number: Optional[int] = None
    source_line: Optional[str] = None
    suggested_install: Optional[str] = None
    is_dev_dependency: bool = False


class ImportAnalysisError(Exception):
    """Raised when import analysis fails."""
    pass


class ImportAnalyzer:
    """Analyze Python files for imports and missing dependencies."""
    
    # Common package name to pip install name mappings
    BASE_PIP_MAPPINGS = {
        'aiohttp': 'aiohttp',
        'requests': 'requests',
        'fastapi': 'fastapi',
        'starlette': 'starlette',
        'uvicorn': 'uvicorn',
        'pydantic': 'pydantic',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'sqlalchemy': 'sqlalchemy',
        'psycopg2': 'psycopg2-binary',
        'mysql': 'mysql-connector-python',
        'redis': 'redis',
        'celery': 'celery',
        'click': 'click',
        'typer': 'typer',
        'rich': 'rich',
        'httpx': 'httpx',
        'websockets': 'websockets',
        'jinja2': 'jinja2',
        'flask': 'flask',
        'django': 'django',
        'boto3': 'boto3',
        'openai': 'openai',
        'anthropic': 'anthropic',
        'langchain': 'langchain',
        'transformers': 'transformers',
        'torch': 'torch',
        'tensorflow': 'tensorflow',
        'sklearn': 'scikit-learn',
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'toml': 'toml',
        'dotenv': 'python-dotenv',
        'jwt': 'PyJWT',
        'bcrypt': 'bcrypt',
        'cryptography': 'cryptography',
    }
    
    # Development/testing packages
    DEV_PACKAGES = {
        'pytest', 'mypy', 'black', 'flake8', 'pylint', 'coverage',
        'tox', 'pre-commit', 'sphinx', 'mkdocs', 'bandit',
        'isort', 'autopep8', 'yapf', 'ruff'
    }
    
    # Standard library modules (Python 3.11+)
    BASE_STDLIB_MODULES = {
        'os', 'sys', 'json', 'ast', 'inspect', 'importlib', 'pathlib', 
        'typing', 'logging', 'asyncio', 'traceback', 'dataclasses',
        'functools', 'itertools', 'collections', 'datetime', 'time',
        'math', 'random', 'string', 're', 'urllib', 'http', 'email',
        'xml', 'html', 'sqlite3', 'pickle', 'csv', 'configparser',
        'argparse', 'subprocess', 'threading', 'multiprocessing',
        'queue', 'socket', 'ssl', 'hashlib', 'uuid', 'tempfile',
        'shutil', 'glob', 'fnmatch', 'zipfile', 'tarfile', 'gzip',
        'io', 'contextlib', 'warnings', 'unittest', 'doctest',
        'operator', 'copy', 'weakref', 'gc', 'atexit', 'signal',
        'errno', 'stat', 'filecmp', 'linecache', 'tokenize',
        'keyword', 'heapq', 'bisect', 'array', 'struct', 'codecs'
    }
    
    def __init__(self, config: Optional[FactoryConfig] = None):
        """Initialize the import analyzer."""
        self.config = config or DEFAULT_CONFIG
        self._pip_mappings = self.config.merge_pip_mappings(self.BASE_PIP_MAPPINGS)
        self._stdlib_modules = self.config.get_effective_stdlib_modules(self.BASE_STDLIB_MODULES)
        self._analysis_cache: Dict[str, List[MissingDependency]] = {}
    
    def analyze_file(self, file_path: str) -> List[MissingDependency]:
        """Analyze a Python file for missing dependencies."""
        file_path = str(Path(file_path).resolve())
        
        # Check cache if enabled
        if self.config.cache_dependency_analysis and file_path in self._analysis_cache:
            logger.debug(f"Using cached analysis for {file_path}")
            return self._analysis_cache[file_path]
        
        try:
            missing_deps = self._analyze_file_impl(file_path)
            
            # Cache results if enabled
            if self.config.cache_dependency_analysis:
                self._analysis_cache[file_path] = missing_deps
            
            return missing_deps
            
        except Exception as e:
            error_msg = f"Failed to analyze imports in {file_path}: {e}"
            if self.config.verbose_errors:
                logger.error(error_msg, exc_info=True)
            else:
                logger.error(error_msg)
            raise ImportAnalysisError(error_msg) from e
    
    def _analyze_file_impl(self, file_path: str) -> List[MissingDependency]:
        """Internal implementation of file analysis."""
        path = Path(file_path)
        
        # Check file size
        if path.stat().st_size > self.config.max_file_size_mb * 1024 * 1024:
            raise ImportAnalysisError(f"File {file_path} is too large (>{self.config.max_file_size_mb}MB)")
        
        # Read and parse file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
        except UnicodeDecodeError:
            raise ImportAnalysisError(f"Cannot decode file {file_path} as UTF-8")
        except IOError as e:
            raise ImportAnalysisError(f"Cannot read file {file_path}: {e}")
        
        # Parse AST
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            raise ImportAnalysisError(f"Syntax error in {file_path}: {e}")
        
        # Find all import statements
        missing_deps = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    missing = self._check_module(alias.name, "import", node.lineno, lines)
                    if missing:
                        missing_deps.append(missing)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    missing = self._check_module(node.module, "from_import", node.lineno, lines)
                    if missing:
                        missing_deps.append(missing)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_deps = []
        for dep in missing_deps:
            key = (dep.module, dep.import_type, dep.line_number)
            if key not in seen:
                seen.add(key)
                unique_deps.append(dep)
        
        return unique_deps
    
    def _check_module(self, module_name: str, import_type: str, line_num: int, lines: List[str]) -> Optional[MissingDependency]:
        """Check if a module is available."""
        # Get the top-level module name
        top_module = module_name.split('.')[0]
        
        # Skip standard library modules
        if top_module in self._stdlib_modules:
            logger.debug(f"Skipping stdlib module: {top_module}")
            return None
        
        try:
            importlib.import_module(top_module)
            logger.debug(f"Module {top_module} is available")
            return None  # Module is available
        except ImportError:
            logger.debug(f"Module {top_module} is missing")
            pass
        except Exception as e:
            # Other import errors (circular imports, etc.)
            logger.warning(f"Unexpected error importing {top_module}: {e}")
            return None
        
        # Get source line
        source_line = lines[line_num - 1] if 0 < line_num <= len(lines) else None
        
        # Check if this is an optional import (in try/except block)
        is_optional = self._is_optional_import(lines, line_num - 1)
        
        # Check if it's a development dependency
        is_dev = top_module in self.DEV_PACKAGES
        
        return MissingDependency(
            module=top_module,
            import_type="optional" if is_optional else import_type,
            line_number=line_num,
            source_line=source_line.strip() if source_line else None,
            suggested_install=self._pip_mappings.get(top_module, top_module),
            is_dev_dependency=is_dev
        )
    
    def _is_optional_import(self, lines: List[str], line_index: int) -> bool:
        """Check if an import is inside a try/except block."""
        if line_index < 0 or line_index >= len(lines):
            return False
        
        # Get the indentation level of the import line
        import_line = lines[line_index]
        import_indent = len(import_line) - len(import_line.lstrip())
        
        # Look backwards for 'try:' at the same or lesser indentation
        try_found = False
        for i in range(line_index - 1, max(-1, line_index - 20), -1):
            line = lines[i]
            if not line.strip():  # Skip empty lines
                continue
            
            line_indent = len(line) - len(line.lstrip())
            
            # If we find a line at the same or lesser indentation
            if line_indent <= import_indent:
                if line.strip().startswith('try:'):
                    try_found = True
                    break
                else:
                    # Found other code at same level, not in a try block
                    break
        
        if not try_found:
            return False
        
        # Look forwards for 'except' block at the same indentation as try (less than import)
        for i in range(line_index + 1, min(len(lines), line_index + 20)):
            line = lines[i]
            if not line.strip():  # Skip empty lines
                continue
            
            line_indent = len(line) - len(line.lstrip())
            
            # Look for except at the same level as the try (less indented than the import)
            if line_indent < import_indent:
                if line.strip().startswith('except'):
                    return True
                else:
                    # Found other code at try level, not an except block
                    break
            # Continue looking through same-level code inside the try block
        
        return False
    
    def clear_cache(self):
        """Clear the analysis cache."""
        self._analysis_cache.clear()
        logger.debug("Cleared import analysis cache")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the cache."""
        return {
            "enabled": self.config.cache_dependency_analysis,
            "entries": len(self._analysis_cache),
            "files": list(self._analysis_cache.keys())
        }