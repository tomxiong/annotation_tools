"""
Tests for logging system.
Following TDD approach - write tests first.
"""
import pytest
import tempfile
import os
from pathlib import Path
import logging

from src.core.logger import Logger


class TestLogger:
    """Test cases for Logger class."""
    
    def test_logger_creates_log_files(self):
        """Test that logger creates log files in specified directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with Logger(name="test_logger", log_dir=temp_dir) as logger:
                logger.info("Test message")
                
            log_file = Path(temp_dir) / "test_logger.log"
            assert log_file.exists()
            
            # Check file content
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test message" in content
    
    def test_logger_formats_messages_correctly(self):
        """Test that logger formats messages with timestamp and level."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with Logger(name="test_format", log_dir=temp_dir) as logger:
                logger.info("Format test message")
                
            log_file = Path(temp_dir) / "test_format.log"
            with open(log_file, 'r') as f:
                content = f.read()
                # Check format: timestamp - name - level - message
                assert "test_format" in content
                assert "INFO" in content
                assert "Format test message" in content
                assert "-" in content  # Separators
    
    def test_logger_handles_different_levels(self):
        """Test that logger handles different log levels correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with INFO level
            with Logger(name="test_levels", log_dir=temp_dir, log_level="INFO") as logger:
                logger.debug("Debug message")  # Should not appear
                logger.info("Info message")    # Should appear
                logger.warning("Warning message")  # Should appear
                logger.error("Error message")  # Should appear
                
            log_file = Path(temp_dir) / "test_levels.log"
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Debug message" not in content
                assert "Info message" in content
                assert "Warning message" in content
                assert "Error message" in content
    
    def test_logger_rotates_files(self):
        """Test that logger rotates files when size limit is reached."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create logger with very small max_bytes for testing
            with Logger(
                name="test_rotation", 
                log_dir=temp_dir, 
                max_bytes=100,  # Very small for testing
                backup_count=2
            ) as logger:
                # Write enough messages to trigger rotation
                for i in range(50):
                    logger.info(f"This is a long message to trigger rotation {i}")
                
            # Check that rotation occurred
            log_files = list(Path(temp_dir).glob("test_rotation.log*"))
            assert len(log_files) > 1  # Should have main file + rotated files
    
    def test_logger_get_logger_method(self):
        """Test the get_logger class method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with Logger.get_logger(name="test_get", log_dir=temp_dir) as logger:
                assert isinstance(logger, Logger)
                assert logger.name == "test_get"
                
                logger.info("Test get_logger method")
                
            log_file = Path(temp_dir) / "test_get.log"
            assert log_file.exists()
    
    def test_logger_exception_logging(self):
        """Test that logger can log exceptions with traceback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with Logger(name="test_exception", log_dir=temp_dir) as logger:
                try:
                    raise ValueError("Test exception")
                except ValueError:
                    logger.exception("An error occurred")
                
            log_file = Path(temp_dir) / "test_exception.log"
            with open(log_file, 'r') as f:
                content = f.read()
                assert "An error occurred" in content
                assert "ValueError" in content
                assert "Test exception" in content
                assert "Traceback" in content
    
    def test_logger_directory_creation(self):
        """Test that logger creates log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = Path(temp_dir) / "nested" / "log" / "dir"
            
            with Logger(name="test_dir", log_dir=str(nested_dir)) as logger:
                logger.info("Test directory creation")
                
            assert nested_dir.exists()
            log_file = nested_dir / "test_dir.log"
            assert log_file.exists()
