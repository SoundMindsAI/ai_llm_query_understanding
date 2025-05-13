"""End-to-end integration tests for the LLM Query Understanding Service.

This module tests the complete workflow from API endpoint to LLM processing
and response parsing, using mock objects to avoid loading the actual model.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from typing import Dict, Any, List

from llm_query_understand.api.app import app
from tests.mocks.mock_llm import MockLargeLanguageModel


@pytest.fixture(scope="module")
def mock_llm():
    """Create a mock LLM for testing."""
    return MockLargeLanguageModel()


@pytest.fixture(scope="module")
def client_with_mock_llm(mock_llm):
    """Create a test client with a mocked LLM."""
    # Create an application-level patch for tests
    with patch("llm_query_understand.api.app.LargeLanguageModel", return_value=mock_llm):
        # Return a TestClient that will use the mocked LLM
        client = TestClient(app)
        # Force initialization of the global LLM
        from llm_query_understand.api.app import llm
        # Set the global LLM to our mock
        with patch("llm_query_understand.api.app.llm", mock_llm):
            yield client


class TestEndToEnd:
    """End-to-end integration tests for the complete service."""

    def test_parse_blue_metal_dining_table(self, client_with_mock_llm, mock_llm):
        """Test parsing 'blue metal dining table' query end-to-end."""
        # Reset mock calls
        mock_llm.reset_calls()
        
        # Define custom response for this specific query
        mock_llm.responses["blue metal dining table"] = """
        {
            "item_type": "dining table",
            "material": "metal",
            "color": "blue"
        }
        """
        
        # Send the request
        response = client_with_mock_llm.post(
            "/parse",
            json={"query": "blue metal dining table"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify query was correctly echoed back
        assert data["query"] == "blue metal dining table"
        
        # Verify parsed data
        assert data["parsed_query"]["item_type"] == "dining table"
        assert data["parsed_query"]["material"] == "metal" 
        assert data["parsed_query"]["color"] == "blue"
        
        # Verify LLM was called
        assert len(mock_llm.get_calls()) == 1
        
        # Verify caching information
        assert data["cached"] is False
        assert "generation_time" in data
        assert "total_time" in data

    def test_parse_green_plastic_chair(self, client_with_mock_llm, mock_llm):
        """Test parsing 'green plastic chair' query end-to-end."""
        # Reset mock calls
        mock_llm.reset_calls()
        
        # Define custom response for this specific query
        mock_llm.responses["green plastic chair"] = """
        {
            "item_type": "chair",
            "material": "plastic",
            "color": "green"
        }
        """
        
        # Send the request
        response = client_with_mock_llm.post(
            "/parse",
            json={"query": "green plastic chair"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify query was correctly echoed back
        assert data["query"] == "green plastic chair"
        
        # Verify parsed data
        assert data["parsed_query"]["item_type"] == "chair"
        assert data["parsed_query"]["material"] == "plastic" 
        assert data["parsed_query"]["color"] == "green"
        
        # Verify LLM was called
        assert len(mock_llm.get_calls()) == 1

    def test_parse_malformed_llm_response(self, client_with_mock_llm, mock_llm):
        """Test handling of malformed LLM responses."""
        # Reset mock calls
        mock_llm.reset_calls()
        
        # Define a malformed response that's not valid JSON
        mock_llm.responses["malformed query"] = """
        This is not valid JSON and should be handled gracefully by the parser.
        """
        
        # Send the request
        response = client_with_mock_llm.post(
            "/parse",
            json={"query": "malformed query"}
        )
        
        # Verify response (should still be successful)
        assert response.status_code == 200
        data = response.json()
        
        # Verify fallback parsing returned null values
        assert data["parsed_query"]["item_type"] is None
        assert data["parsed_query"]["material"] is None
        assert data["parsed_query"]["color"] is None
        
        # Verify LLM was called
        assert len(mock_llm.get_calls()) == 1

    def test_parse_with_cache(self, client_with_mock_llm, mock_llm):
        """Test caching behavior with repeated queries."""
        # Reset mock calls
        mock_llm.reset_calls()
        
        # Mock the cache behavior
        with patch("llm_query_understand.api.app.cache") as mock_cache:
            # First request - cache miss
            mock_cache.get.return_value = None
            
            # First request
            response1 = client_with_mock_llm.post(
                "/parse",
                json={"query": "test query for caching"}
            )
            
            # Verify cache was checked
            mock_cache.get.assert_called_once()
            
            # Verify LLM was called (cache miss)
            assert len(mock_llm.get_calls()) == 1
            mock_llm.reset_calls()
            
            # Mock a cache hit for the second request
            cached_result = {
                "generation_time": 0.5,
                "parsed_query": {
                    "item_type": "cached item",
                    "material": "cached material",
                    "color": "cached color"
                }
            }
            mock_cache.get.return_value = cached_result
            
            # Second request with same query
            response2 = client_with_mock_llm.post(
                "/parse",
                json={"query": "test query for caching"}
            )
            
            # Verify second response
            assert response2.status_code == 200
            data2 = response2.json()
            
            # Verify data was retrieved from cache
            assert data2["cached"] is True
            assert data2["parsed_query"]["item_type"] == "cached item"
            
            # Verify LLM was NOT called (cache hit)
            assert len(mock_llm.get_calls()) == 0

    def test_parse_error_handling(self, client_with_mock_llm):
        """Test error handling in parse endpoint."""
        # Test with missing query parameter
        response = client_with_mock_llm.post(
            "/parse",
            json={}  # Missing query parameter
        )
        
        # Should return 422 Unprocessable Entity
        assert response.status_code == 422
        
        # Test with invalid JSON format but correct content type
        # Using bytes content to avoid deprecation warning
        response = client_with_mock_llm.post(
            "/parse",
            content=b"not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 Unprocessable Entity (FastAPI's standard for JSON parse errors)
        assert response.status_code == 422
