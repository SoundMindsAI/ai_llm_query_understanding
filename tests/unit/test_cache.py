"""Unit tests for the QueryCache class.

This module contains tests for the Redis caching functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import time
import json
from typing import Dict, Any, Optional

from llm_query_understand.core.cache import QueryCache


class TestQueryCache:
    """Test suite for the QueryCache class."""

    def test_init_without_redis(self):
        """Test initialization with Redis disabled."""
        # Test with environment variable disabled
        with patch.dict('os.environ', {'REDIS_ENABLED': 'false'}):
            cache = QueryCache()
            assert cache.redis_enabled is False
            assert not hasattr(cache, 'redis')

    def test_init_with_redis(self):
        """Test initialization with Redis enabled."""
        # Mock the Redis client
        with patch('redis.Redis') as mock_redis:
            # Configure Redis to be enabled
            with patch.dict('os.environ', {'REDIS_ENABLED': 'true'}):
                cache = QueryCache()
                assert cache.redis_enabled is True
            assert hasattr(cache, 'redis') 
            mock_redis.assert_called_once()

    def test_get_with_redis_disabled(self):
        """Test get() when Redis is disabled."""
        cache = QueryCache()
        cache.redis_enabled = False
        
        # When Redis is disabled, get should return None
        result = cache.get("any_query")
        assert result is None

    def test_set_with_redis_disabled(self):
        """Test set() when Redis is disabled."""
        cache = QueryCache()
        cache.redis_enabled = False
        
        # When Redis is disabled, set should return False
        result = cache.set("any_query", {"test": "data"})
        assert result is False

    def test_get_hit(self):
        """Test get() with a cache hit."""
        # Create a mock Redis client
        mock_redis = MagicMock()
        mock_data = json.dumps({"result": "cached_value"})
        mock_redis.get.return_value = mock_data
        
        # Create cache with mocked Redis
        cache = QueryCache()
        cache.redis_enabled = True
        cache.redis = mock_redis
        
        # Test get with a hit
        result = cache.get("test_query")
        
        # Verify Redis get was called
        mock_redis.get.assert_called_once_with("query:test_query")
        assert result == {"result": "cached_value"}

    def test_get_miss(self):
        """Test get() with a cache miss."""
        # Create a mock Redis client
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        # Create cache with mocked Redis
        cache = QueryCache()
        cache.redis_enabled = True
        cache.redis = mock_redis
        
        # Test get with a miss
        result = cache.get("test_query")
        
        # Verify result is None on miss
        assert result is None

    def test_set_success(self):
        """Test set() with successful cache write."""
        # Create a mock Redis client
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        
        # Create cache with mocked Redis
        cache = QueryCache()
        cache.redis_enabled = True
        cache.redis = mock_redis
        
        # Test data to cache
        test_data = {"key": "value", "nested": {"data": True}}
        
        # Test set with success
        result = cache.set("test_query", test_data)
        
        # Verify Redis setex was called with correct parameters
        mock_redis.setex.assert_called_once()
        # The first arg should be the key
        assert mock_redis.setex.call_args[0][0] == "query:test_query"
        # Verify the expiry time (second arg)
        assert isinstance(mock_redis.setex.call_args[0][1], int)
        # Third arg should be JSON string of data
        assert json.loads(mock_redis.setex.call_args[0][2]) == test_data
        
        assert result is True

    def test_set_failure(self):
        """Test set() with Redis failure."""
        # Create a mock Redis client
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = Exception("Redis error")
        
        # Create cache with mocked Redis
        cache = QueryCache()
        cache.redis_enabled = True
        cache.redis = mock_redis
        
        # Test set with failure
        result = cache.set("test_query", {"data": "value"})
        
        # Verify result is False on error
        assert result is False

    def test_cache_expiry(self):
        """Test that cached items expire after the configured time."""
        # Create a mock Redis client
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        
        # Create cache with default expiry time (3600 seconds)
        cache = QueryCache()
        cache.redis_enabled = True
        cache.redis = mock_redis
        
        # Set a value in cache
        cache.set("test_query", {"data": "value"}, expiry=3600)
        
        # Verify expiry time was passed correctly to setex (first positional argument after key)
        assert mock_redis.setex.call_args[0][1] == 3600
