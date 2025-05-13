# Development Guide

This guide covers best practices for developing and contributing to the LLM Query Understanding Service.

## Project Structure

The project follows a clean, modular Python package structure:

```
ai_llm_query_understanding/
├── llm_query_understand/     # Main package
│   ├── __init__.py           # Package metadata
│   ├── api/                  # API components
│   │   ├── __init__.py
│   │   └── app.py            # FastAPI application
│   ├── core/                 # Core functionality
│   │   ├── __init__.py
│   │   ├── llm.py            # LLM integration
│   │   └── cache.py          # Redis caching
│   └── utils/                # Utilities
│       ├── __init__.py
│       └── logging_config.py # Logging configuration
├── scripts/                  # Entry point scripts
│   └── start_server.py       # Server startup script
├── tests/                    # Tests
│   ├── __init__.py
│   └── test_api.py           # API tests
├── docs/                     # Documentation
├── setup.py                  # Package installation
├── pyproject.toml            # Project metadata
├── requirements.txt          # Dependencies
└── README.md                 # Project documentation
```

## Development Environment Setup

### Installing in Development Mode

For development, install the package in editable mode:

```bash
pip install -e .
```

### Setting Up Pre-commit Hooks

We recommend using pre-commit hooks to ensure code quality:

```bash
pip install pre-commit
pre-commit install
```

## Code Style and Standards

The project follows these standards:

- **PEP 8** for Python code style
- **Type hints** for all function parameters and return values
- **Comprehensive docstrings** in Google style format
- **Single responsibility** principle for functions and classes
- **Consistent naming** conventions
- **Maximum line length**: 88 characters (compatible with Black formatter)
- **Function size limit**: Keep functions small and focused (< 50 lines preferred)

## Testing

### Running Tests

Tests are written using pytest and can be run with:

```bash
pytest
```

For more verbose output:

```bash
pytest -v
```

For code coverage:

```bash
pytest --cov=llm_query_understand
```

### Writing Tests

All new functionality should include tests. For API endpoints, test both success and failure cases. For example:

```python
def test_parse_endpoint_success():
    """Test successful query parsing."""
    response = client.post("/parse", json={"query": "blue wooden table"})
    assert response.status_code == 200
    data = response.json()
    assert data["parsed_query"]["item_type"] == "table"
    assert data["parsed_query"]["material"] == "wooden"
    assert data["parsed_query"]["color"] == "blue"

def test_parse_endpoint_empty_query():
    """Test error handling for empty query."""
    response = client.post("/parse", json={"query": ""})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
```

## Performance Considerations

- **Lazy initialization**: The LLM is initialized only when first needed
- **Caching**: Use Redis caching for repeated queries
- **Quantization**: Consider quantizing models for better performance
- **Prompt optimization**: Keep prompts concise and clear

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Ensure all tests pass locally
4. Update documentation if needed
5. Submit a pull request with a clear description of changes

## Model Management

### Model Selection Criteria

We prioritize models based on:

1. **Performance**: Accuracy in parsing furniture queries
2. **Size**: Smaller models (like Qwen2-0.5B-Instruct) for faster startup
3. **License**: Models with permissive licenses
4. **Quantization**: Support for int8/int4 quantization

### Prompt Engineering

The system prompt for the LLM is critical for accurate parsing. The current prompt emphasizes:

- Literal matching of query terms
- Extraction of specifically mentioned attributes
- JSON-only output

When modifying the prompt, test thoroughly with a variety of queries to ensure consistent results.
