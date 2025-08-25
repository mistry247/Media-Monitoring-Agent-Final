"""
Tests for logging configuration
"""
import pytest
import logging
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.logging_config import (
    JSONFormatter,
    ColoredFormatter,
    setup_logging,
    get_logger,
    log_operation,
    log_error,
    init_logging
)

class TestJSONFormatter:
    """Test JSON formatter"""
    
    def test_json_formatter_basic(self):
        """Test basic JSON formatting"""
        formatter = JSONFormatter()
        
        # Create a log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test"
        record.funcName = "test_function"
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert parsed["message"] == "Test message"
        assert parsed["module"] == "test"
        assert parsed["function"] == "test_function"
        assert parsed["line"] == 10
        assert "timestamp" in parsed
    
    def test_json_formatter_with_extra_fields(self):
        """Test JSON formatting with extra fields"""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test"
        record.funcName = "test_function"
        record.user_id = "user123"
        record.request_id = "req456"
        record.operation = "test_op"
        record.duration = 123.45
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["user_id"] == "user123"
        assert parsed["request_id"] == "req456"
        assert parsed["operation"] == "test_op"
        assert parsed["duration_ms"] == 123.45
    
    def test_json_formatter_with_exception(self):
        """Test JSON formatting with exception info"""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="Test error",
                args=(),
                exc_info=sys.exc_info()
            )
            record.module = "test"
            record.funcName = "test_function"
            
            formatted = formatter.format(record)
            parsed = json.loads(formatted)
            
            assert "exception" in parsed
            assert "ValueError" in parsed["exception"]
            assert "Test exception" in parsed["exception"]

class TestColoredFormatter:
    """Test colored formatter"""
    
    def test_colored_formatter_basic(self):
        """Test basic colored formatting"""
        formatter = ColoredFormatter()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test"
        record.funcName = "test_function"
        
        formatted = formatter.format(record)
        
        # Should contain ANSI color codes
        assert "\033[32m" in formatted  # Green for INFO
        assert "\033[0m" in formatted   # Reset
        assert "INFO" in formatted
        assert "test.logger" in formatted
        assert "Test message" in formatted
    
    def test_colored_formatter_different_levels(self):
        """Test colored formatting for different log levels"""
        formatter = ColoredFormatter()
        
        levels_colors = [
            (logging.DEBUG, "\033[36m"),    # Cyan
            (logging.INFO, "\033[32m"),     # Green
            (logging.WARNING, "\033[33m"),  # Yellow
            (logging.ERROR, "\033[31m"),    # Red
            (logging.CRITICAL, "\033[35m")  # Magenta
        ]
        
        for level, color in levels_colors:
            record = logging.LogRecord(
                name="test.logger",
                level=level,
                pathname="test.py",
                lineno=10,
                msg="Test message",
                args=(),
                exc_info=None
            )
            record.module = "test"
            record.funcName = "test_function"
            
            formatted = formatter.format(record)
            assert color in formatted

class TestLoggingSetup:
    """Test logging setup"""
    
    def test_setup_logging_basic(self):
        """Test basic logging setup"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            setup_logging("INFO")
            
            # Should configure root logger
            mock_logger.setLevel.assert_called()
            mock_logger.addHandler.assert_called()
    
    def test_setup_logging_with_file(self):
        """Test logging setup with file output"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            
            setup_logging("INFO", log_file=log_file)
            
            # Log file should be created
            assert os.path.exists(log_file)
            
            # Clean up handlers to release file
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
    
    def test_setup_logging_with_json(self):
        """Test logging setup with JSON formatting"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            
            setup_logging("INFO", log_file=log_file, enable_json_logging=True)
            
            # Should create log file
            assert os.path.exists(log_file)
            
            # Clean up handlers to release file
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)

class TestLoggerUtilities:
    """Test logger utility functions"""
    
    def test_get_logger(self):
        """Test get_logger function"""
        logger = get_logger("test.module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
    
    def test_log_operation(self):
        """Test log_operation function"""
        with patch('utils.logging_config.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = get_logger("test")
            log_operation(logger, "test_operation", 123.45, user_id="user123")
            
            # Should call logger.info with extra fields
            mock_logger.info.assert_called_once()
            args, kwargs = mock_logger.info.call_args
            
            assert "test_operation" in args[0]
            assert "123.45ms" in args[0]
            assert "extra" in kwargs
            assert kwargs["extra"]["operation"] == "test_operation"
            assert kwargs["extra"]["duration"] == 123.45
            assert kwargs["extra"]["user_id"] == "user123"
    
    def test_log_error(self):
        """Test log_error function"""
        with patch('utils.logging_config.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = get_logger("test")
            error = ValueError("Test error")
            log_error(logger, error, operation="test_operation", user_id="user123")
            
            # Should call logger.error with exc_info and extra fields
            mock_logger.error.assert_called_once()
            args, kwargs = mock_logger.error.call_args
            
            assert "test_operation" in args[0]
            assert "Test error" in args[0]
            assert kwargs["exc_info"] is True
            assert "extra" in kwargs
            assert kwargs["extra"]["error_type"] == "ValueError"
            assert kwargs["extra"]["operation"] == "test_operation"
            assert kwargs["extra"]["user_id"] == "user123"

class TestLoggingInitialization:
    """Test logging initialization"""
    
    @patch('utils.logging_config.settings')
    def test_init_logging_success(self, mock_settings):
        """Test successful logging initialization"""
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.LOG_FILE = None
        mock_settings.ENABLE_JSON_LOGGING = False
        
        with patch('utils.logging_config.setup_logging') as mock_setup:
            init_logging()
            
            mock_setup.assert_called_once_with(
                log_level="INFO",
                log_file=None,
                enable_json_logging=False
            )
    
    @patch('utils.logging_config.settings')
    def test_init_logging_failure(self, mock_settings):
        """Test logging initialization failure"""
        mock_settings.LOG_LEVEL = "INFO"
        
        with patch('utils.logging_config.setup_logging') as mock_setup:
            mock_setup.side_effect = Exception("Setup failed")
            
            with patch('logging.basicConfig') as mock_basic_config:
                init_logging()
                
                # Should fall back to basic config
                mock_basic_config.assert_called_once()
    
    @patch('utils.logging_config.settings')
    def test_init_logging_with_file(self, mock_settings):
        """Test logging initialization with file"""
        mock_settings.LOG_LEVEL = "DEBUG"
        mock_settings.LOG_FILE = "test.log"
        mock_settings.ENABLE_JSON_LOGGING = True
        
        with patch('utils.logging_config.setup_logging') as mock_setup:
            init_logging()
            
            mock_setup.assert_called_once_with(
                log_level="DEBUG",
                log_file="test.log",
                enable_json_logging=True
            )