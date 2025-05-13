# Deployment Guide

This guide covers different deployment options for the LLM Query Understanding Service.

## Deployment Options

- [Docker Deployment](./docker.md): Containerized deployment with Docker and Docker Compose
- [Local Deployment](./local.md): Running the service directly on a server
- [Cloud Deployment](./cloud.md): Deployment on cloud platforms

## Production Considerations

### Performance Optimization

- **Model Quantization**: Use quantized models to reduce memory usage and increase inference speed
- **Redis Caching**: Enable Redis for caching frequent queries
- **Appropriate Hardware**: When possible, deploy on machines with sufficient RAM (16GB+ recommended)
- **Load Testing**: Conduct load testing before production deployment to determine appropriate resource allocation

### Security

- **HTTPS**: Always use HTTPS in production
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Input Validation**: The service uses Pydantic for input validation
- **Environment Variables**: Use environment variables for sensitive configuration

### Monitoring

- **Logging**: Configure structured JSON logging for easier parsing
- **Metrics Collection**: Track API latency, error rates, and resource usage
- **Health Checks**: Use the `/health` endpoint for monitoring
- **Performance Monitoring**: Track generation times in the response payload

### Scaling

- **Horizontal Scaling**: Deploy multiple instances behind a load balancer
- **Redis Cluster**: When scaling, consider using a Redis cluster for shared caching
- **Model Size vs Performance**: Consider using smaller models for faster response times when scaling

## Environment Variables

The service can be configured using the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_ENABLED` | Enable Redis caching | `false` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `LOG_LEVEL` | Logging level | `info` |
| `JSON_LOGS` | Enable JSON logging format | `false` |
| `LOG_FILE` | Log file path | `None` (stdout) |

## Minimum Requirements

- **CPU**: 4 cores (8+ recommended)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Disk**: 2GB for code and models
- **Python**: 3.8 or higher

## Common Issues

### High Memory Usage

If you observe high memory usage:
- Use a smaller LLM model (e.g., Qwen2-0.25B instead of Qwen2-0.5B)
- Enable model quantization
- Increase server RAM
- Monitor and adjust batch sizes if needed

### Slow Response Times

If response times are too slow:
- Enable Redis caching
- Use a smaller model
- Consider dedicated GPU hardware
- Optimize prompts for brevity
