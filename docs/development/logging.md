# Logging Guide

The LLM Query Understanding Service uses a robust logging system designed for production-grade observability while following security best practices.

## Logging Features

- **Structured JSON Logging**: All logs in non-development environments are emitted as structured JSON for easy parsing and analysis
- **Log Correlation**: Request IDs track operations across the system
- **Performance Monitoring**: Automatic timing for API requests and operations
- **Data Privacy**: Automatic redaction of sensitive information
- **Rotating Logs**: Prevents log files from growing too large
- **Context Managers**: Helpers for timing operations and tracking request context

## Configuration

Logging is configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Minimum log level to output (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) | `INFO` |
| `JSON_LOGS` | Whether to format logs as JSON (`true`, `false`) | `true` in production/staging, `false` in development |
| `LOG_FILE` | Path to log file (omit to log to stdout only) | None |
| `MAX_LOG_SIZE_BYTES` | Maximum size of each log file before rotation | 10 MB |
| `MAX_LOG_BACKUPS` | Number of rotated log files to keep | 5 |
| `ENVIRONMENT` | Current environment (`development`, `staging`, `production`) | `development` |
| `APP_VERSION` | Application version for log correlation | `1.0.0` |

## Using the Logger

### Basic Logging

```python
from llm_query_understand.utils.logging_config import get_logger

logger = get_logger()

# Log at different levels
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")

# Include additional context
logger.info("Process completed", extra={"items_processed": 100, "duration_ms": 1500})
```

### Performance Monitoring

Use the timing context manager to automatically log execution time:

```python
from llm_query_understand.utils.logging_config import log_execution_time, get_logger

logger = get_logger()

# Simple timing
with log_execution_time("database_query"):
    # Perform database query
    results = db.execute_query()

# Add context to the timing log
with log_execution_time("model_inference", model_name="Qwen2-0.5B", input_tokens=512):
    # Run model inference
    output = model.generate(prompt)
```

### Request Context

For operations that span multiple components, use request context:

```python
from llm_query_understand.utils.logging_config import (
    request_context, get_logger
)

logger = get_logger()

with request_context(request_id="unique-id-123", user_id="user-456"):
    # All logs in this context will include the request_id and user_id
    logger.info("Processing user request")
    
    # Perform operations
    result = process_user_data()
    
    logger.info("Request completed", extra={"status": "success"})
```

### Data Sanitization

Sanitize sensitive data before logging:

```python
from llm_query_understand.utils.logging_config import sanitize_data, get_logger

logger = get_logger()

user_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "api_key": "secret-key-123",
    "preferences": {
        "theme": "dark",
        "password": "secret-password"
    }
}

# Sanitize automatically removes sensitive fields
safe_data = sanitize_data(user_data)
logger.info("User data processed", extra={"user_data": safe_data})
```

## Log Analysis 

### JSON Log Format

In JSON mode, logs include standardized fields:

```json
{
  "timestamp": "2025-05-13T10:25:12.345Z",
  "level": "INFO",
  "message": "API request processed",
  "service": "llm_query_understand",
  "environment": "production",
  "request_id": "5d67-4e28-a0d9-12b5c31a7c82",
  "path": "/parse",
  "http_method": "POST",
  "status_code": 200,
  "response_time": 0.1235,
  "hostname": "server-123",
  "thread_id": 140123456789,
  "process_id": 12345
}
```

### Searching Logs

When using JSON logs with tools like Elasticsearch or CloudWatch Logs Insights:

```
# Find all errors for a specific request
filter level="ERROR" and request_id="5d67-4e28-a0d9-12b5c31a7c82"

# Find slow responses (>500ms)
filter response_time>0.5

# Find model inference timing logs
filter message like "Execution timing" and operation="model_inference"
```

## Best Practices

1. **Don't log sensitive information**:
   - Use `sanitize_data()` for any user-provided data
   - Never log API keys, passwords or tokens

2. **Use appropriate log levels**:
   - `DEBUG`: Detailed information for debugging problems
   - `INFO`: Confirmation that things are working as expected
   - `WARNING`: Indication that something unexpected happened, but the application is still working
   - `ERROR`: Due to a more serious problem, some functionality is unavailable
   - `CRITICAL`: A serious error indicating that the program itself may be unable to continue running

3. **Include context in logs**:
   - Use the `extra` parameter to add structured data
   - Always include relevant identifiers (user IDs, request IDs)
   - Add performance metrics to help identify bottlenecks

4. **Consistent formatting**:
   - Use lowercase for log keys
   - Use snake_case for multi-word keys
   - Be consistent with units (e.g., always use seconds or milliseconds)
