"""
Configuration management for batch annotation tool.
Supports YAML files, environment variables, and validation.
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigError(Exception):
    """Configuration related errors."""
    pass


class Config:
    """Configuration management class."""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        'batch_size': 32,
        'output_format': 'json',
        'confidence_threshold': 0.5,
        'log_level': 'INFO',
        'max_workers': 4,
        'image_extensions': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp'],
        'output_dir': './output',
        'log_dir': './logs'
    }
    
    # Required fields that must be present
    REQUIRED_FIELDS = ['batch_size', 'output_format', 'confidence_threshold', 'log_level']
    
    # Environment variable prefix
    ENV_PREFIX = 'BAT_'
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration with default values and optional overrides."""
        self._config = self.DEFAULT_CONFIG.copy()
        
        if config_dict:
            self._config.update(config_dict)
            
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate()
    
    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
        except FileNotFoundError:
            raise ConfigError(f"Config file not found: {config_path}")
        except Exception as e:
            raise ConfigError(f"Error reading config file: {e}")
            
        if not isinstance(config_dict, dict):
            raise ConfigError("Config file must contain a YAML dictionary")
        
        # Check for required fields in the loaded config
        for field in cls.REQUIRED_FIELDS:
            if field not in config_dict:
                raise ConfigError(f"Missing required field: {field}")
            
        return cls(config_dict)
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        for key in self._config:
            env_key = f"{self.ENV_PREFIX}{key.upper()}"
            if env_key in os.environ:
                value = os.environ[env_key]
                # Convert to appropriate type
                if key in ['batch_size', 'max_workers']:
                    try:
                        self._config[key] = int(value)
                    except ValueError:
                        raise ConfigError(f"Invalid integer value for {key}: {value}")
                elif key == 'confidence_threshold':
                    try:
                        self._config[key] = float(value)
                    except ValueError:
                        raise ConfigError(f"Invalid float value for {key}: {value}")
                else:
                    self._config[key] = value
    
    def _validate(self):
        """Validate configuration values."""
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in self._config:
                raise ConfigError(f"Missing required field: {field}")
        
        # Validate batch_size
        if not (1 <= self._config['batch_size'] <= 1000):
            raise ConfigError("batch_size must be between 1 and 1000")
        
        # Validate confidence_threshold
        if not (0.0 <= self._config['confidence_threshold'] <= 1.0):
            raise ConfigError("confidence_threshold must be between 0.0 and 1.0")
        
        # Validate output_format
        valid_formats = ['json', 'csv', 'xml', 'coco', 'yolo']
        if self._config['output_format'] not in valid_formats:
            raise ConfigError(f"output_format must be one of: {valid_formats}")
        
        # Validate log_level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self._config['log_level'] not in valid_levels:
            raise ConfigError(f"log_level must be one of: {valid_levels}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self._config.copy()
    
    def save_to_file(self, config_path: str):
        """Save configuration to YAML file."""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise ConfigError(f"Error saving config file: {e}")
    
    # Property accessors for common config values
    @property
    def batch_size(self) -> int:
        return self._config['batch_size']
    
    @property
    def output_format(self) -> str:
        return self._config['output_format']
    
    @property
    def confidence_threshold(self) -> float:
        return self._config['confidence_threshold']
    
    @property
    def log_level(self) -> str:
        return self._config['log_level']
    
    @property
    def max_workers(self) -> int:
        return self._config['max_workers']
    
    @property
    def image_extensions(self) -> list:
        return self._config['image_extensions']
    
    @property
    def output_dir(self) -> str:
        return self._config['output_dir']
    
    @property
    def log_dir(self) -> str:
        return self._config['log_dir']
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self._config[key] = value
        self._validate()