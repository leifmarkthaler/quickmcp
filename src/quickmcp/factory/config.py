"""
Configuration system for MCP Factory.
"""

from dataclasses import dataclass, field
from typing import Dict, Set, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class FactoryConfig:
    """Configuration for MCP Factory behavior."""
    
    # Dependency checking
    check_dependencies: bool = True
    warn_on_optional_missing: bool = True
    
    # Safety settings
    allow_code_execution: bool = True
    warn_on_code_execution: bool = True
    max_file_size_mb: int = 10
    
    # Type conversion
    strict_type_conversion: bool = False
    allow_type_coercion: bool = True
    
    # Performance
    cache_dependency_analysis: bool = True
    cache_type_hints: bool = True
    
    # Import analysis
    additional_stdlib_modules: Set[str] = field(default_factory=set)
    custom_pip_mappings: Dict[str, str] = field(default_factory=dict)
    
    # Logging
    log_level: str = "INFO"
    verbose_errors: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        
        if self.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"Invalid log_level: {self.log_level}")
        
        # Set up logging level for factory components
        factory_logger = logging.getLogger("quickmcp.factory")
        factory_logger.setLevel(getattr(logging, self.log_level))
    
    def merge_pip_mappings(self, base_mappings: Dict[str, str]) -> Dict[str, str]:
        """Merge custom pip mappings with base mappings."""
        merged = base_mappings.copy()
        merged.update(self.custom_pip_mappings)
        return merged
    
    def get_effective_stdlib_modules(self, base_modules: Set[str]) -> Set[str]:
        """Get effective set of stdlib modules."""
        return base_modules | self.additional_stdlib_modules


# Default configuration instance
DEFAULT_CONFIG = FactoryConfig()


def create_safe_config() -> FactoryConfig:
    """Create a configuration optimized for safety."""
    return FactoryConfig(
        allow_code_execution=False,
        warn_on_code_execution=True,
        strict_type_conversion=True,
        allow_type_coercion=False,
        verbose_errors=True,
        log_level="WARNING"
    )


def create_permissive_config() -> FactoryConfig:
    """Create a configuration optimized for flexibility."""
    return FactoryConfig(
        check_dependencies=False,
        allow_code_execution=True,
        warn_on_code_execution=False,
        strict_type_conversion=False,
        allow_type_coercion=True,
        verbose_errors=False,
        log_level="ERROR"
    )


def create_development_config() -> FactoryConfig:
    """Create a configuration optimized for development."""
    return FactoryConfig(
        check_dependencies=True,
        warn_on_optional_missing=True,
        allow_code_execution=True,
        warn_on_code_execution=True,
        strict_type_conversion=False,
        cache_dependency_analysis=False,  # Always fresh analysis
        log_level="DEBUG",
        verbose_errors=True
    )