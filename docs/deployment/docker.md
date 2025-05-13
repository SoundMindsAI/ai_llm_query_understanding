# Docker Deployment

This guide covers deploying the LLM Query Understanding Service using Docker and Docker Compose.

## Prerequisites

- Docker Engine (version 20.10.0+)
- Docker Compose (version 2.0.0+)
- 16GB RAM recommended for Docker host

## Quick Start with Docker Compose

The simplest way to deploy the service is using Docker Compose, which sets up both the API service and Redis cache.

1. Make sure you're in the project root directory with the `docker-compose.yml` file.

2. Start the service:
```bash
docker compose up -d
```

3. Check if the containers are running:
```bash
docker compose ps
```

The service will be available at: http://localhost:8000

## Docker Compose Configuration

The default `docker-compose.yml` file includes:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_ENABLED=true
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    volumes:
      - huggingface_cache:/root/.cache/huggingface
    depends_on:
      - redis

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  huggingface_cache:
    driver: local
  redis_data:
    driver: local
```

## Building and Running the Docker Image Manually

If you prefer to manage the containers separately:

1. Build the Docker image:
```bash
docker build -t llm-query-service .
```

2. Run Redis:
```bash
docker run -d --name redis -p 6379:6379 redis:alpine
```

3. Run the service:
```bash
docker run -d --name llm-service \
  -p 8000:8000 \
  -e REDIS_ENABLED=true \
  -e REDIS_HOST=redis \
  -e REDIS_PORT=6379 \
  --link redis \
  llm-query-service
```

## Environment Variables

You can configure the Docker deployment using environment variables in the `docker-compose.yml` file:

```yaml
environment:
  - REDIS_ENABLED=true
  - REDIS_HOST=redis
  - REDIS_PORT=6379
  - LOG_LEVEL=info
  - JSON_LOGS=true
```

## Persistent Storage

The Docker Compose configuration uses named volumes for:

1. **Redis data**: Ensures cached query results persist between restarts
2. **Hugging Face cache**: Prevents re-downloading model weights on restarts

## Docker Image Optimization

The Dockerfile is optimized for:

- Size: Uses multi-stage builds to minimize final image size
- Performance: Installs only required dependencies
- Caching: Leverages Docker layer caching for faster builds

## Managing Docker Compose Containers

Common operations:

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```

## Production Deployment Recommendations

For production environments:

1. **Set resource limits**:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: "4"
          memory: 16G
```

2. **Use a reverse proxy** (like Nginx or Traefik) for SSL termination

3. **Set up proper monitoring** with Prometheus and Grafana

4. **Configure auto-restart** policies:
```yaml
services:
  api:
    restart: unless-stopped
```

## Troubleshooting

### Container doesn't start

Check logs with:
```bash
docker compose logs api
```

### Cannot connect to API

Verify if containers are running:
```bash
docker compose ps
```

Check if the port mapping is correct:
```bash
docker compose port api 8000
```

### Redis connection errors

Ensure the Redis service name matches the `REDIS_HOST` environment variable in docker-compose.yml.
