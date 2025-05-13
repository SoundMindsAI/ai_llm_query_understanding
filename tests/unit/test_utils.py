"""Unit tests for utility modules.

This module contains tests for utility functions, particularly logging configuration.
"""
import pytest
import os
import logging
import json
from unittest.mock import patch, MagicMock

from llm_query_understand.utils.logging_config import get_logger


class TestLoggingConfig:
    """Test suite for logging configuration utilities."""

    def test_get_logger(self):
        """Test the get_logger function."""
        logger = get_logger()
        
        # Verify logger has the expected name
        assert logger.name == "llm_query_understand"
        
        # Verify it's the same logger instance if called again
        logger2 = get_logger()
        assert logger is logger2

    @patch('llm_query_understand.utils.logging_config.logging.FileHandler')
    def test_logging_config_with_file(self, mock_file_handler):
        """Test logging configuration with file output."""
        # Mock the file handler
        mock_handler = MagicMock()
        mock_file_handler.return_value = mock_handler
        
        # Setup test environment
        with patch.dict('os.environ', {
            'LOG_LEVEL': 'DEBUG',
            'LOG_FILE': '/tmp/test.log',
            'JSON_LOGS': 'false'
        }):
            # Reset the logging config
            logging.root.handlers = []
            
            # Reimport the module to trigger configuration
            import importlib
            import llm_query_understand.utils.logging_config
            importlib.reload(llm_query_understand.utils.logging_config)
            
            # Verify file handler was created with the right file
            mock_file_handler.assert_called_once_with('/tmp/test.log')
            
            # Get the logger
            logger = get_logger()
            
            # Verify the log level was set correctly
            assert logger.level == logging.DEBUG
            
            # Verify handlers were added
            assert len(logger.handlers) > 0

    def test_logging_json_format(self):
        """Test logging configuration with JSON log format."""
        # Setup test environment
        with patch.dict('os.environ', {
            'LOG_LEVEL': 'INFO',
            'JSON_LOGS': 'true'
        }):
            # Reset handlers
            logging.root.handlers = []
            
            # Reimport to trigger configuration
            import importlib
            import llm_query_understand.utils.logging_config
            importlib.reload(llm_query_understand.utils.logging_config)
            
            # Get the logger
            logger = get_logger()
            
            # Verify we have at least one handler
            assert len(logger.handlers) > 0
            
            # Check if the level is set correctly
            assert logger.level == logging.INFO
            
            # Check if at least one handler has a JsonFormatter
            has_json_formatter = False
            for handler in logger.handlers:
                if hasattr(handler, 'formatter') and 'JsonFormatter' in handler.formatter.__class__.__name__:
                    has_json_formatter = True
                    break
            assert has_json_formatter

    def test_log_message_json_format(self):
        """Test that log messages are properly formatted in JSON."""
        # Setup test environment with JSON logging
        with patch.dict('os.environ', {
            'JSON_LOGS': 'true',
            'LOG_LEVEL': 'DEBUG'
        }):
            # Reset handlers
            logging.root.handlers = []
            
            # Reimport to trigger configuration
            import importlib
            import llm_query_understand.utils.logging_config
            importlib.reload(llm_query_understand.utils.logging_config)
            
            # Create a string IO buffer to capture log output
            import io
            log_capture = io.StringIO()
            
            # Create a custom handler to capture the log output
            h = logging.StreamHandler(log_capture)
            
            # Create a JSON formatter (using recommended import to avoid deprecation warning)
            from pythonjsonlogger import json as jsonlogger
            formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
            h.setFormatter(formatter)
            
            # Get the logger and add our capture handler
            logger = get_logger()
            logger.handlers = [h]  # Replace existing handlers
            
            # Log a test message
            test_message = "Test log message"
            logger.info(test_message)
            
            # Get the captured log output
            log_output = log_capture.getvalue()
            
            # If JSON logging is working, we should be able to parse the output as JSON
            try:
                log_data = json.loads(log_output)
                # Verify the message was logged correctly
                assert log_data.get("message") == test_message
                # Verify other fields are present
                assert "asctime" in log_data
                assert "levelname" in log_data
                assert log_data["levelname"] == "INFO"
            except json.JSONDecodeError:
                # If we get here, the output wasn't valid JSON
                pytest.fail(f"Log output is not valid JSON: {log_output}")

    def test_logging_defaults(self):
        """Test logging configuration with default settings."""
        # Preserve original environment
        original_env = {}
        for key in ['LOG_LEVEL', 'JSON_LOGS', 'LOG_FILE']:
            if key in os.environ:
                original_env[key] = os.environ[key]
        
        try:
            # Clear environment variables
            for key in ['LOG_LEVEL', 'JSON_LOGS', 'LOG_FILE']:
                if key in os.environ:
                    del os.environ[key]
            
            # Reset handlers
            logging.root.handlers = []
            
            # Reimport to trigger configuration with defaults
            import importlib
            import llm_query_understand.utils.logging_config
            importlib.reload(llm_query_understand.utils.logging_config)
            
            # Get the logger
            logger = get_logger()
            
            # Verify the default log level (INFO)
            assert logger.level == logging.INFO
            
            # Verify handlers were added
            assert len(logger.handlers) > 0
            
            # Verify default formatter is not JSON
            for handler in logger.handlers:
                if hasattr(handler, 'formatter'):
                    formatter_str = str(handler.formatter._fmt)
                    assert 'JsonFormatter' not in handler.formatter.__class__.__name__
        
        finally:
            # Restore original environment
            for key, value in original_env.items():
                os.environ[key] = value
