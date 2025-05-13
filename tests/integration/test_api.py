#!/usr/bin/env python3
"""
Tests for the LLM Query Understanding Service API.

This module contains tests for the FastAPI application's endpoints.
"""
import json
import pytest
from fastapi.testclient import TestClient
from llm_query_understand.api.app import app

# Create a test client using FastAPI's TestClient
client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns correct service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "LLM Query Understanding Service"
    assert "version" in data
    assert "endpoints" in data

def test_health_check():
    """Test the health check endpoint returns ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_test_endpoint():
    """Test the test endpoint correctly parses simple furniture queries."""
    # Test with a blue wooden table query
    response = client.post(
        "/test",
        json={"query": "blue wooden dining table"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "blue wooden dining table"
    assert data["parsed_query"]["item_type"] == "dining table"
    assert data["parsed_query"]["material"] == "wooden"
    assert data["parsed_query"]["color"] == "blue"
    
    # Test with a red metal chair query
    response = client.post(
        "/test",
        json={"query": "red metal chair"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "red metal chair"
    assert data["parsed_query"]["item_type"] == "chair"
    assert data["parsed_query"]["material"] == "metal"
    assert data["parsed_query"]["color"] == "red"

def test_empty_query():
    """Test that an empty query returns a 400 error."""
    response = client.post(
        "/test",
        json={"query": ""}
    )
    # Since the test endpoint doesn't check for empty queries, this should still succeed
    assert response.status_code == 200
    
    # But the parse endpoint should reject empty queries
    response = client.post(
        "/parse",
        json={"query": ""}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

# Note: We don't test the actual LLM parsing here since it requires loading the model
# Those should be integration tests run separately
