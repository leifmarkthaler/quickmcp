"""
Tests for the factory configuration system.
"""

import pytest
from makemcp.factory.config import (
    FactoryConfig,
    DEFAULT_CONFIG,
    create_safe_config,
    create_development_config,
    create_permissive_config
)


class TestFactoryConfig:
    """Test the FactoryConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = FactoryConfig()
        
        # Check key defaults
        assert config.check_dependencies is True
        assert config.allow_code_execution is True
        assert config.strict_type_conversion is False
        assert config.cache_dependency_analysis is True
        assert config.max_file_size_mb == 10
        assert config.log_level == "INFO"
    
    def test_custom_config(self):
        """Test creating configuration with custom values."""
        config = FactoryConfig(
            check_dependencies=False,
            strict_type_conversion=True,
            max_file_size_mb=20,
            custom_pip_mappings={"cv2": "opencv-python"}
        )
        
        assert config.check_dependencies is False
        assert config.strict_type_conversion is True
        assert config.max_file_size_mb == 20
        assert "cv2" in config.custom_pip_mappings
    
    def test_merge_pip_mappings(self):
        """Test merging pip mappings."""
        config = FactoryConfig(
            custom_pip_mappings={
                "custom_module": "custom-package",
                "sklearn": "my-scikit-learn"  # Override default
            }
        )
        
        base_mappings = {"sklearn": "scikit-learn", "numpy": "numpy"}
        merged = config.merge_pip_mappings(base_mappings)
        
        # Should include both and override
        assert merged["custom_module"] == "custom-package"
        assert merged["sklearn"] == "my-scikit-learn"  # Overridden
        assert merged["numpy"] == "numpy"  # From base
    
    def test_merge_stdlib_modules(self):
        """Test merging stdlib modules."""
        config = FactoryConfig(
            additional_stdlib_modules={"mylib", "customlib"}
        )
        
        base_modules = {"os", "sys", "json"}
        effective = config.get_effective_stdlib_modules(base_modules)
        
        # Should include both
        assert "mylib" in effective
        assert "customlib" in effective
        assert "os" in effective
        assert "sys" in effective
        assert "json" in effective
    
    def test_validation_log_level(self):
        """Test log level validation."""
        # Valid log level
        config = FactoryConfig(log_level="DEBUG")
        assert config.log_level == "DEBUG"
        
        # Invalid log level should raise during creation
        with pytest.raises(ValueError, match="Invalid log_level"):
            config = FactoryConfig(log_level="invalid")
    
    def test_file_size_limit(self):
        """Test file size limit configuration."""
        config = FactoryConfig(
            max_file_size_mb=50
        )
        
        assert config.max_file_size_mb == 50
        
        # Test invalid size
        with pytest.raises(ValueError, match="max_file_size_mb must be positive"):
            config = FactoryConfig(max_file_size_mb=0)
    
    def test_performance_options(self):
        """Test performance-related options."""
        config = FactoryConfig(
            cache_dependency_analysis=False,
            cache_type_hints=False
        )
        
        assert config.cache_dependency_analysis is False
        assert config.cache_type_hints is False


class TestPreConfiguredConfigs:
    """Test pre-configured configuration functions."""
    
    def test_safe_config(self):
        """Test safe configuration for production."""
        config = create_safe_config()
        
        # Should be restrictive
        assert config.allow_code_execution is False
        assert config.strict_type_conversion is True
        assert config.allow_type_coercion is False
        assert config.warn_on_code_execution is True
        assert config.log_level == "WARNING"
    
    def test_development_config(self):
        """Test development configuration."""
        config = create_development_config()
        
        # Should be balanced
        assert config.allow_code_execution is True
        assert config.warn_on_code_execution is True
        assert config.strict_type_conversion is False
        assert config.cache_dependency_analysis is False  # For fresh analysis in dev
        assert config.check_dependencies is True
        assert config.log_level == "DEBUG"
    
    def test_permissive_config(self):
        """Test permissive configuration."""
        config = create_permissive_config()
        
        # Should be very flexible
        assert config.allow_code_execution is True
        assert config.warn_on_code_execution is False
        assert config.strict_type_conversion is False
        assert config.allow_type_coercion is True
        assert config.check_dependencies is False
        assert config.log_level == "ERROR"


class TestConfigComparison:
    """Test configuration comparisons and usage."""
    
    def test_configs_are_different(self):
        """Test that pre-configured configs are actually different."""
        safe = create_safe_config()
        dev = create_development_config()
        perm = create_permissive_config()
        
        # Key differences
        assert safe.allow_code_execution != perm.allow_code_execution
        assert safe.strict_type_conversion != perm.strict_type_conversion
        assert dev.warn_on_code_execution != perm.warn_on_code_execution
    
    def test_config_immutability(self):
        """Test that configs can be modified after creation."""
        config = create_safe_config()
        
        # Should be able to override
        config.allow_code_execution = True
        assert config.allow_code_execution is True
        
        # Original safe config function should still return False
        new_safe = create_safe_config()
        assert new_safe.allow_code_execution is False
    
    def test_default_config_singleton(self):
        """Test that DEFAULT_CONFIG is consistent."""
        assert DEFAULT_CONFIG.check_dependencies is True
        assert DEFAULT_CONFIG.allow_code_execution is True
        
        # Should be the same instance
        from makemcp.factory.config import DEFAULT_CONFIG as config2
        assert DEFAULT_CONFIG is config2


class TestConfigIntegration:
    """Test configuration integration with factory."""
    
    def test_factory_uses_config(self):
        """Test that factory respects configuration."""
        from makemcp.factory import MCPFactory
        
        # Create factory with custom config
        config = FactoryConfig(
            check_dependencies=False,
            strict_type_conversion=True
        )
        
        factory = MCPFactory(config=config)
        
        # Check config is used
        assert factory.config.check_dependencies is False
        assert factory.config.strict_type_conversion is True
    
    def test_factory_with_safe_config(self):
        """Test factory with safe configuration."""
        from makemcp.factory import MCPFactory
        
        config = create_safe_config()
        factory = MCPFactory(config=config)
        
        # Should not allow code execution
        assert factory.config.allow_code_execution is False
    
    def test_config_affects_type_converter(self):
        """Test that config affects type conversion."""
        from makemcp.factory.type_conversion import TypeConverter
        
        # Strict config
        strict_config = FactoryConfig(strict_type_conversion=True)
        strict_converter = TypeConverter(strict_config)
        
        # Flexible config
        flex_config = FactoryConfig(strict_type_conversion=False)
        flex_converter = TypeConverter(flex_config)
        
        # Both should have different behavior
        assert strict_converter.config.strict_type_conversion is True
        assert flex_converter.config.strict_type_conversion is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])