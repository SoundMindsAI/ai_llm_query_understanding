# Testing Guide

This guide explains how to run tests for the LLM Query Understanding Service and how to write new tests.

## Test Structure

The project uses a well-organized test hierarchy:

```
tests/
├── conftest.py                # Shared pytest fixtures
├── unit/                      # Unit tests
│   ├── test_cache.py          # Tests for cache functionality 
│   ├── test_llm.py            # Tests for LLM functionality
│   └── test_utils.py          # Tests for utility functions
├── integration/               # Integration tests
│   ├── test_api.py            # Tests for API endpoints
│   └── test_e2e.py            # End-to-end workflow tests
└── mocks/                     # Mock data and utilities
    ├── mock_llm.py            # Mock LLM for testing
```

## Running Tests

### Running All Tests

To run all tests:

```bash
pytest
```

### Running Specific Test Types

Run only unit tests:

```bash
pytest tests/unit
```

Run only integration tests:

```bash
pytest tests/integration
```

### Running Tests by Category

The tests are marked with categories for easy filtering:

```bash
# Run only API tests
pytest -m api

# Run only cache tests
pytest -m cache

# Run only LLM tests
pytest -m llm

# Exclude slow tests
pytest -m "not slow"
```

### Running Tests with Coverage

To run tests with coverage reporting:

```bash
pytest --cov=llm_query_understand
```

For a detailed HTML coverage report:

```bash
pytest --cov=llm_query_understand --cov-report=html
```

This will create a `htmlcov` directory with the coverage report.

## Writing New Tests

### Unit Tests

Unit tests should:
- Test a single component in isolation
- Mock all dependencies
- Be fast to run
- Have descriptive names that explain what they test

Example of a good unit test:

```python
def test_cache_set_stores_value_with_correct_expiry():
    """Test that cache.set() stores values with the configured expiry time."""
    # Test implementation...
```

### Integration Tests

Integration tests should:
- Test interactions between components
- Use controlled test fixtures
- Verify correct data flow between components

### End-to-End Tests

End-to-end tests should:
- Test complete workflows from API to response
- Verify business requirements are met
- Use mocks for external dependencies like the LLM

## Mocking the LLM

The `tests/mocks/mock_llm.py` module provides a `MockLargeLanguageModel` class that can be used to test LLM-dependent code without loading the actual model.

Example usage:

```python
from tests.mocks.mock_llm import MockLargeLanguageModel
from unittest.mock import patch

# Create a mock LLM with custom responses
mock_llm = MockLargeLanguageModel({
    "blue wooden table": '{"item_type": "table", "material": "wooden", "color": "blue"}'
})

# Patch the LLM in the module being tested
with patch('llm_query_understand.api.app.llm', mock_llm):
    # Your test code here
```

## Test Coverage Goals

The project aims for high test coverage, with these guidelines:

1. **Core functionality**: 90%+ coverage
2. **API endpoints**: 100% coverage for success and error paths
3. **Utility functions**: 80%+ coverage

## Continuous Integration

Tests are automatically run in CI on each pull request. PRs should not be merged if tests are failing.
