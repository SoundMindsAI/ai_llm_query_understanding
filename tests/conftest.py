"""Shared pytest fixtures for the LLM Query Understanding Service tests.

This module contains fixtures that can be used across both unit and integration tests.
"""
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import app to create test client
from llm_query_understand.api.app import app


@pytest.fixture
def test_client():
    """Create a FastAPI TestClient for API testing."""
    return TestClient(app)


@pytest.fixture
def mock_cache():
    """Create a mock cache for testing."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    return mock


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response with successful parse."""
    return """
    {
        "item_type": "dining table",
        "material": "wooden",
        "color": "blue"
    }
    """


@pytest.fixture
def test_queries():
    """Sample furniture queries for testing."""
    return {
        "simple": "blue wooden table",
        "complex": "vintage mid-century modern walnut dining table with brass accents",
        "minimal": "chair",
        "empty": "",
        "non_furniture": "python programming language",
    }


@pytest.fixture
def sample_parsed_queries():
    """Sample parsed query results for different inputs."""
    return {
        "blue_wooden_table": {
            "item_type": "table",
            "material": "wooden",
            "color": "blue"
        },
        "green_plastic_chair": {
            "item_type": "chair",
            "material": "plastic",
            "color": "green"
        },
        "red_leather_sofa": {
            "item_type": "sofa",
            "material": "leather",
            "color": "red"
        }
    }


@pytest.fixture(scope="session", autouse=True)
def disable_redis_in_tests():
    """Disable Redis in all tests by default."""
    os.environ["REDIS_ENABLED"] = "false"
    yield
    # Clean up if needed
    if "REDIS_ENABLED" in os.environ:
        del os.environ["REDIS_ENABLED"]
