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

## Edge Case Handling

The service employs a dual approach to handle edge cases in query parsing:

### 1. Prompt Engineering

The system prompt in `app.py` is designed to guide the LLM's behavior with:

- Explicit parsing rules for common patterns
- Direct examples of edge cases and expected outputs
- Pattern-matching instructions for material/color disambiguation

### 2. Post-Processing Function

The `handle_edge_cases` function in `app.py` serves as a safety net for known problematic queries:

```python
def handle_edge_cases(query: str, parsed_response: dict) -> dict:
    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()
    
    # Apply specific rules for known edge cases
    if "gold metal accent table" in query_lower:
        return {
            "item_type": "accent table",
            "material": "metal",
            "color": "gold"
        }
    # Additional cases...
    
    return parsed_response
```

This approach follows these principles:

1. **Simple over complex**: Direct string matching is used instead of complex regex or NLP
2. **Targeted intervention**: Only modifies output for known problematic cases
3. **Maintainable**: Easy to extend with new edge cases as they're discovered

When adding new edge cases, follow these steps:

1. First, attempt to improve the system prompt to handle the case naturally
2. If prompt engineering isn't sufficient, add a targeted rule to `handle_edge_cases`
3. Document the edge case and solution in the appropriate test files
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
