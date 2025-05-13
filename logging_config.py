"""
Logging configuration module for the LLM Query Understanding Service.
Provides structured JSON logging with configurable log levels.
"""
import os
import sys
import logging
from pythonjsonlogger import jsonlogger

# Default log level can be overridden by environment variable
DEFAULT_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Valid log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# Use the specified level or default to INFO
log_level = LOG_LEVELS.get(DEFAULT_LOG_LEVEL, logging.INFO)

# Create the logger
logger = logging.getLogger("llm_query_understand")
logger.setLevel(log_level)

# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)

# Create formatter
# Format includes timestamp, level, message and any extra fields as JSON
log_format = "%(asctime)s %(levelname)s %(message)s %(filename)s %(funcName)s %(lineno)d"
if os.environ.get("JSON_LOGS", "false").lower() == "true":
    formatter = jsonlogger.JsonFormatter(log_format)
else:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to console handler
console_handler.setFormatter(formatter)

# Add console handler to logger
logger.addHandler(console_handler)

# Optionally add file handler if LOG_FILE is specified
log_file = os.environ.get("LOG_FILE")
if log_file:
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def get_logger():
    """
    Get the configured logger instance.
    Returns:
        logging.Logger: The configured logger
    """
    return logger
