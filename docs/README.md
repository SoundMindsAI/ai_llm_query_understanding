# LLM Query Understanding Service Documentation

This directory contains the official documentation for the LLM Query Understanding Service.

## Documentation Structure

- **[Getting Started](./guides/getting-started.md)**: Quick installation and setup guide
- **[API Reference](./api/README.md)**: Detailed API endpoint documentation
- **[Development Guide](./development/README.md)**: Development workflow and practices
- **[Deployment Guide](./deployment/README.md)**: Deployment options and configuration

## Project Overview

The LLM Query Understanding Service is a lightweight API that transforms natural language furniture queries into structured JSON data using a small, efficient Large Language Model (Qwen2-0.5B-Instruct).

Example transformation:
```
"blue wooden dining table" → {"item_type": "dining table", "material": "wooden", "color": "blue"}
```

This service is designed for integration with e-commerce search systems, catalog management tools, and other applications requiring natural language understanding for furniture queries.
