"""
Logging configuration module for the LLM Query Understanding Service.
Provides structured JSON logging with configurable log levels and advanced features.
"""
import os
import sys
import time
import logging
import logging.handlers
import uuid
import threading
import socket
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager
from pythonjsonlogger import json as jsonlogger

# Thread-local storage for request context
_thread_local = threading.local()

# Default log level can be overridden by environment variable
DEFAULT_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
ENV = os.environ.get("ENVIRONMENT", "development")
SERVICE_NAME = "llm_query_understand"
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
HOSTNAME = socket.gethostname()

# Valid log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# Determine maximum log file size (default: 10MB)
MAX_LOG_SIZE_BYTES = int(os.environ.get("MAX_LOG_SIZE_BYTES", 10 * 1024 * 1024))
MAX_LOG_BACKUPS = int(os.environ.get("MAX_LOG_BACKUPS", 5))

# Determine if logs should be in JSON format
JSON_LOGS = os.environ.get("JSON_LOGS", "true" if ENV != "development" else "false").lower() == "true"

# Use the specified level or default to INFO
log_level = LOG_LEVELS.get(DEFAULT_LOG_LEVEL, logging.INFO)

# Create the root logger
logger = logging.getLogger(SERVICE_NAME)
logger.setLevel(log_level)
logger.propagate = False  # Prevent duplicate logs

# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# --------- Handler Setup ---------

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)

# Create enhanced JSON formatter with additional fields
class EnhancedJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record["timestamp"] = self.formatTime(record)
        log_record["service"] = SERVICE_NAME
        log_record["hostname"] = HOSTNAME
        log_record["environment"] = ENV
        log_record["app_version"] = APP_VERSION
        
        # Add request context if available
        if hasattr(_thread_local, "request_id"):
            log_record["request_id"] = _thread_local.request_id
            
        if hasattr(_thread_local, "session_id"):
            log_record["session_id"] = _thread_local.session_id
            
        if hasattr(_thread_local, "user_id"):
            log_record["user_id"] = _thread_local.user_id
        
        # Add execution context
        log_record["thread_id"] = record.thread
        log_record["process_id"] = record.process
        
        # Add log level name (consistent with standard logs)
        log_record["level"] = record.levelname

# Format log messages
if JSON_LOGS:
    log_format = "%(asctime)s %(levelname)s %(message)s %(pathname)s %(funcName)s %(lineno)d %(thread)d %(process)d"
    formatter = EnhancedJsonFormatter(log_format)
else:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s [%(request_id)s] - %(message)s', 
                                  defaults={"request_id": "--"})

# Set formatter for console handler
console_handler.setFormatter(formatter)

# Add console handler to logger
logger.addHandler(console_handler)

# Configure file logging if specified
log_file = os.environ.get("LOG_FILE")
if log_file:
    # Use rotating file handler to prevent excessive file growth
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE_BYTES,
        backupCount=MAX_LOG_BACKUPS
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# --------- Context Management ---------

def set_request_context(request_id: Optional[str] = None, 
                       session_id: Optional[str] = None,
                       user_id: Optional[str] = None) -> str:
    """
    Set context values for the current thread/request.
    
    Args:
        request_id: Unique ID for the current request (generated if not provided)
        session_id: Session ID if available
        user_id: User ID if available
        
    Returns:
        The request ID (either provided or generated)
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
        
    _thread_local.request_id = request_id
    
    if session_id:
        _thread_local.session_id = session_id
        
    if user_id:
        _thread_local.user_id = user_id
    
    return request_id


def clear_request_context():
    """Clear all thread-local request context data."""
    if hasattr(_thread_local, "request_id"):
        delattr(_thread_local, "request_id")
        
    if hasattr(_thread_local, "session_id"):
        delattr(_thread_local, "session_id")
        
    if hasattr(_thread_local, "user_id"):
        delattr(_thread_local, "user_id")


@contextmanager
def request_context(request_id: Optional[str] = None, 
                   session_id: Optional[str] = None,
                   user_id: Optional[str] = None):
    """
    Context manager to handle request context for a block of code.
    
    Args:
        request_id: Unique ID for the request
        session_id: Session ID if available
        user_id: User ID if available
    """
    try:
        set_request_context(request_id, session_id, user_id)
        yield
    finally:
        clear_request_context()


# --------- Performance Monitoring ---------

@contextmanager
def log_execution_time(operation_name: str, log_level: int = logging.INFO, **additional_context):
    """
    Context manager that logs the execution time of a block of code.
    
    Args:
        operation_name: Name of the operation being timed
        log_level: Log level to use for the timing message
        additional_context: Additional data to include in the log
    """
    start_time = time.time()
    try:
        yield
    finally:
        execution_time = time.time() - start_time
        
        # Add all context to the log message
        context = {"operation": operation_name, "duration_seconds": round(execution_time, 4)}
        context.update(additional_context)
        
        # Format as a string for non-JSON logs
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        
        logger.log(log_level, f"Execution timing: {context_str}", extra=context)


# --------- Sensitive Data Handling ---------

def sanitize_data(data: Union[Dict, list, str], sensitive_keys: list = None) -> Union[Dict, list, str]:
    """
    Sanitize sensitive data from logs.
    
    Args:
        data: The data to sanitize
        sensitive_keys: List of keys to sanitize (case insensitive)
        
    Returns:
        Sanitized data with sensitive values masked
    """
    if sensitive_keys is None:
        sensitive_keys = ["password", "token", "secret", "key", "authorization", 
                         "credit_card", "ssn", "api_key"]
    
    # Convert all sensitive keys to lowercase for case-insensitive matching
    sensitive_keys_lower = [k.lower() for k in sensitive_keys]
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if any(sk in key.lower() for sk in sensitive_keys_lower):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, (dict, list)):
                sanitized[key] = sanitize_data(value, sensitive_keys)
            else:
                sanitized[key] = value
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_data(item, sensitive_keys) for item in data]
    
    return data


# --------- API Functions ---------

def get_logger():
    """
    Get the configured logger instance.
    
    Returns:
        logging.Logger: The configured logger
    """
    return logger


def log_request(method: str, path: str, query_params: Optional[Dict] = None, 
               headers: Optional[Dict] = None, body: Optional[Any] = None, 
               status_code: Optional[int] = None, response_time: Optional[float] = None):
    """
    Log an API request with relevant details.
    
    Args:
        method: HTTP method
        path: Request path
        query_params: Query parameters (sanitized)
        headers: Request headers (sanitized)
        body: Request body (sanitized)
        status_code: Response status code
        response_time: Response time in seconds
    """
    log_data = {
        "http_method": method,
        "path": path,
    }
    
    if query_params:
        log_data["query_params"] = sanitize_data(query_params)
        
    if headers:
        # Include only relevant headers, sanitized
        safe_headers = {k.lower(): v for k, v in headers.items() 
                      if k.lower() in ["user-agent", "content-type", "accept"]}
        log_data["headers"] = safe_headers
        
    if body:
        log_data["body"] = sanitize_data(body)
        
    if status_code:
        log_data["status_code"] = status_code
        
    if response_time:
        log_data["response_time"] = round(response_time, 4)
    
    log_level = logging.INFO if status_code is None or status_code < 400 else logging.ERROR
    logger.log(log_level, f"API {method} {path}", extra=log_data)
