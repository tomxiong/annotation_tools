"""
Tests for configuration management system.
Following TDD approach - write tests first.
"""
import pytest
import tempfile
import os
from pathlib import Path
import yaml

from src.core.config import Config, ConfigError


class TestConfig:
    """Test cases for Config class."""
    
    def test_config_loads_default_values(self):
        """Test that config loads with default values when no file provided."""
        config = Config()
        
        assert config.batch_size == 32
        assert config.output_format == "json"
        assert config.confidence_threshold == 0.5
        assert config.log_level == "INFO"
        
    def test_config_validates_required_fields(self):
        """Test that config validates required fields."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'batch_size': 64,
                # Missing required fields
            }, f)
            f.flush()
            
            with pytest.raises(ConfigError, match="Missing required field"):
                Config.from_file(f.name)
                
        os.unlink(f.name)
        
    def test_config_handles_invalid_yaml(self):
        """Test that config handles invalid YAML gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            
            with pytest.raises(ConfigError, match="Invalid YAML"):
                Config.from_file(f.name)
                
        os.unlink(f.name)
        
    def test_config_environment_override(self):
        """Test that environment variables override config values."""
        os.environ['BAT_BATCH_SIZE'] = '128'
        os.environ['BAT_LOG_LEVEL'] = 'DEBUG'
        
        try:
            config = Config()
            assert config.batch_size == 128
            assert config.log_level == "DEBUG"
        finally:
            del os.environ['BAT_BATCH_SIZE']
            del os.environ['BAT_LOG_LEVEL']
            
    def test_config_validates_batch_size_range(self):
        """Test that batch size is within valid range."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'batch_size': 0,  # Invalid
                'output_format': 'json',
                'confidence_threshold': 0.5,
                'log_level': 'INFO'
            }, f)
            f.flush()
            
            with pytest.raises(ConfigError, match="batch_size must be between"):
                Config.from_file(f.name)
                
        os.unlink(f.name)
        
    def test_config_validates_confidence_threshold(self):
        """Test that confidence threshold is within valid range."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'batch_size': 32,
                'output_format': 'json',
                'confidence_threshold': 1.5,  # Invalid
                'log_level': 'INFO'
            }, f)
            f.flush()
            
            with pytest.raises(ConfigError, match="confidence_threshold must be between"):
                Config.from_file(f.name)
                
        os.unlink(f.name)
        
    def test_config_to_dict(self):
        """Test config serialization to dictionary."""
        config = Config()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'batch_size' in config_dict
        assert 'output_format' in config_dict
        assert 'confidence_threshold' in config_dict
        assert 'log_level' in config_dict