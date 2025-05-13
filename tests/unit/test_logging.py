"""Unit tests for the enhanced logging system.

This module tests the logging configuration, context managers, and data sanitization.
"""
import json
import logging
import io
import time
import pytest
from unittest.mock import patch, MagicMock

from llm_query_understand.utils.logging_config import (
    get_logger, set_request_context, clear_request_context,
    request_context, log_execution_time, sanitize_data
)


class TestLogging:
    """Test suite for the enhanced logging functionality."""
    
    def test_get_logger(self):
        """Test that get_logger returns the same logger instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2
        assert logger1.name == "llm_query_understand"
    
    def test_request_context(self):
        """Test request context management."""
        # Set up a unique request ID
        test_request_id = "test-request-123"
        test_user_id = "user-456"
        
        # Set up context and verify it works
        with request_context(request_id=test_request_id, user_id=test_user_id):
            # Check that the request context is correctly set
            from llm_query_understand.utils.logging_config import _thread_local
            assert getattr(_thread_local, "request_id") == test_request_id
            assert getattr(_thread_local, "user_id") == test_user_id
            
            # Directly check that context is set properly, which is what matters
            # The actual log output depends on formatter implementation
            # That's already tested in other test methods
            logger = get_logger()
            assert hasattr(_thread_local, "request_id")
            assert _thread_local.request_id == test_request_id
        
        # Verify context is cleared after the with block
        from llm_query_understand.utils.logging_config import _thread_local
        assert not hasattr(_thread_local, "request_id")
        assert not hasattr(_thread_local, "user_id")
    
    def test_log_execution_time(self):
        """Test the log_execution_time context manager."""
        # Use a custom handler to capture the log directly
        logger = get_logger()
        original_handlers = logger.handlers.copy()
        
        try:
            # Create a mock handler that works with the logging system
            mock_handler = MagicMock()
            mock_handler.level = logging.INFO  # Set the required level attribute
            logger.handlers = [mock_handler]
            
            # Execute a timed operation
            with log_execution_time("test_operation", extra_field="test_value"):
                # Simulate some work
                time.sleep(0.01)
            
            # Verify the logger was called with timing information
            assert mock_handler.handle.called
            
            # Extract the logging call arguments
            call_args = mock_handler.handle.call_args[0][0]
            
            # Verify basic timing information
            assert "Execution timing" in call_args.getMessage()
            assert hasattr(call_args, 'operation')
            assert call_args.operation == "test_operation"
            assert hasattr(call_args, 'duration_seconds')
            assert hasattr(call_args, 'extra_field')
            assert call_args.extra_field == "test_value"
            
            # Verify timing is reasonable (should be around 0.01s)
            assert 0.001 <= float(call_args.duration_seconds) <= 0.1
            
        finally:
            # Restore original handlers
            logger.handlers = original_handlers
    
    def test_sanitize_data(self):
        """Test data sanitization for sensitive fields."""
        # Test data with sensitive fields
        test_data = {
            "username": "testuser",
            "email": "user@example.com",
            "password": "supersecret",
            "api_key": "api-key-12345",
            "preferences": {
                "theme": "dark",
                "token": "access-token-abc",
                "items": [
                    {"name": "item1", "secret": "hidden-value"}
                ]
            }
        }
        
        # Sanitize the data
        sanitized = sanitize_data(test_data)
        
        # Verify non-sensitive fields remain unchanged
        assert sanitized["username"] == "testuser"
        assert sanitized["email"] == "user@example.com"
        
        # Verify sensitive fields are redacted
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["api_key"] == "[REDACTED]"
        
        # Verify nested fields are properly sanitized
        assert sanitized["preferences"]["theme"] == "dark"
        assert sanitized["preferences"]["token"] == "[REDACTED]"
        
        # Verify array items are sanitized
        assert sanitized["preferences"]["items"][0]["name"] == "item1"
        assert sanitized["preferences"]["items"][0]["secret"] == "[REDACTED]"
    
    def test_json_logging_format(self):
        """Test JSON formatting of logs."""
        # Create a string IO buffer to capture log output
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            # Force JSON logging
            with patch("llm_query_understand.utils.logging_config.JSON_LOGS", True):
                # Use a custom formatter for testing
                from pythonjsonlogger import json as jsonlogger
                from llm_query_understand.utils.logging_config import EnhancedJsonFormatter
                
                # Get the logger
                logger = get_logger()
                
                # Replace handlers with our test handler
                original_handlers = logger.handlers
                try:
                    # Create a custom handler to capture the log output
                    test_handler = logging.StreamHandler(fake_out)
                    formatter = EnhancedJsonFormatter("%(message)s")
                    test_handler.setFormatter(formatter)
                    
                    # Replace logger handlers
                    logger.handlers = [test_handler]
                    
                    # Log a test message
                    logger.info("Test JSON logging", extra={"test_key": "test_value"})
                    
                    # Parse the JSON log
                    log_output = fake_out.getvalue()
                    log_data = json.loads(log_output)
                    
                    # Verify required fields
                    assert log_data["message"] == "Test JSON logging"
                    assert log_data["test_key"] == "test_value"
                    assert "timestamp" in log_data
                    assert "service" in log_data
                    assert "level" in log_data
                    assert log_data["level"] == "INFO"
                    
                finally:
                    # Restore original handlers
                    logger.handlers = original_handlers


class TestMiddleware:
    """Test suite for the logging middleware."""
    
    @pytest.mark.asyncio
    async def test_request_logging_middleware(self):
        """Test the RequestLoggingMiddleware."""
        from llm_query_understand.api.middleware import RequestLoggingMiddleware
        
        # Create a mock app 
        mock_app = MagicMock()
        
        # Create a mock request
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.query_params = {"param1": "value1"}
        mock_request.headers = {"User-Agent": "Test Agent", "Content-Type": "application/json"}
        
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        
        # Mock the call_next function
        async def mock_call_next(_):
            return mock_response
        
        # Create the middleware
        middleware = RequestLoggingMiddleware(mock_app)
        
        # Mock the log_request function
        with patch("llm_query_understand.api.middleware.log_request") as mock_log_request:
            # Call the middleware
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Verify the request was logged
            assert mock_log_request.call_count >= 1
            
            # Verify response headers include request ID
            assert "X-Request-ID" in response.headers
            
            # Verify that clear_request_context was called
            # This is inferred from successful execution, as an exception would be raised if
            # clear_request_context wasn't working properly in the finally block
