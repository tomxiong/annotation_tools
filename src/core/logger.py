"""
Logging system for batch annotation tool.
Provides structured logging with file rotation and different levels.
"""
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


class Logger:
    """Centralized logging system."""
    
    def __init__(self, name: str = "batch_annotation", log_dir: str = "./logs", 
                 log_level: str = "INFO", max_bytes: int = 10485760, backup_count: int = 5):
        """
        Initialize logger with file rotation.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_bytes: Maximum size of log file before rotation (default: 10MB)
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper())
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        
        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
        
        # Setup file handler with rotation
        log_file = self.log_dir / f"{name}.log"
        self.file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        
        # Setup console handler
        self.console_handler = logging.StreamHandler()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Set formatters
        self.file_handler.setFormatter(formatter)
        self.console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)
    
    def close(self):
        """Close all handlers and clean up resources."""
        if hasattr(self, 'file_handler'):
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)
        if hasattr(self, 'console_handler'):
            self.console_handler.close()
            self.logger.removeHandler(self.console_handler)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)
    
    @classmethod
    def get_logger(cls, name: str = "batch_annotation", **kwargs) -> 'Logger':
        """Get or create logger instance."""
        return cls(name=name, **kwargs)