# Getting Started

This guide will help you set up and run the LLM Query Understanding Service locally.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

## Installation

### 1. Clone or download the repository

```bash
git clone https://github.com/soundmindsai/ai_llm_query_understanding.git
cd ai_llm_query_understanding
```

### 2. Install dependencies

```bash
pip install -e .
```

This will install the package in development mode along with all required dependencies.

## Running the Service

The service can be started using the included start script:

```bash
python scripts/start_server.py
```

This will:
1. Automatically handle any port conflicts
2. Start the FastAPI server on port 8000
3. Initialize the LLM (downloading model weights on first run)
4. Set up the Redis cache if configured

The server will be available at: http://localhost:8000

### Configuration Options

You can configure the server with command-line arguments:

```bash
python scripts/start_server.py --host 127.0.0.1 --port 8080 --no-reload --log-level debug
```

### Environment Variables

The service can be configured using environment variables:

- `REDIS_ENABLED` - Enable Redis caching (default: false)
- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `LOG_LEVEL` - Logging level (default: info)
- `JSON_LOGS` - Enable JSON logging format (default: false)
- `LOG_FILE` - Log file path (default: none, logs to stdout)

Example:
```bash
REDIS_ENABLED=true REDIS_HOST=localhost LOG_LEVEL=debug python scripts/start_server.py
```

## Verifying Installation

Once the server is running, you can verify it's working by checking the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok"}
```

## Next Steps

- Explore the [API Reference](../api/README.md) to learn about available endpoints
- Set up [Docker deployment](../deployment/docker.md) for production use
- Check the [Development Guide](../development/README.md) for contributing to the project
