import json
import redis
import os
import time
from typing import Optional, Dict, Any
from llm_query_understand.logging_config import get_logger

# Get the configured logger
logger = get_logger()

class QueryCache:
    """
    Cache for storing and retrieving query parsing results using Redis.
    """
    
    def __init__(self, host: str = None, port: int = None, db: int = 0):
        """
        Initialize the cache with Redis connection parameters.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database ID
        """
        self.redis_enabled = os.environ.get("REDIS_ENABLED", "false").lower() == "true"
        
        # Get Redis connection parameters from environment variables
        redis_host = host or os.environ.get("REDIS_HOST", "localhost")
        redis_port = port or int(os.environ.get("REDIS_PORT", "6379"))
        
        # Log cache configuration
        logger.info(f"Initializing QueryCache with redis_enabled={self.redis_enabled}")
        if self.redis_enabled:
            logger.debug(f"Redis configuration: host={redis_host}, port={redis_port}, db={db}")
            
        if self.redis_enabled:
            try:
                logger.debug("Attempting to connect to Redis...")
                start_time = time.time()
                self.redis = redis.Redis(host=redis_host, port=redis_port, db=db)
                self.redis.ping()  # Test connection
                connection_time = time.time() - start_time
                logger.info(f"Redis connection successful (took {connection_time:.4f}s)")
            except redis.exceptions.ConnectionError as e:
                logger.warning(f"Redis connection failed: {str(e)}")
                logger.warning("Caching disabled due to connection failure")
                self.redis_enabled = False
            except Exception as e:
                logger.error(f"Unexpected error connecting to Redis: {str(e)}", exc_info=True)
                self.redis_enabled = False
        else:
            logger.info("Redis cache disabled by configuration")
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get parsed query results from cache.
        
        Args:
            query: The original search query
            
        Returns:
            Cached parsing result or None if not found
        """
        if not self.redis_enabled:
            logger.debug("Cache lookup skipped - Redis disabled")
            return None
            
        try:
            # Create a deterministic cache key
            cache_key = f"query:{query}"
            logger.debug(f"Looking up cache key: {cache_key}")
            
            start_time = time.time()
            cached_result = self.redis.get(cache_key)
            lookup_time = time.time() - start_time
            
            if cached_result:
                logger.info(f"Cache HIT for query: '{query}' (lookup took {lookup_time:.4f}s)")
                result = json.loads(cached_result)
                logger.debug(f"Retrieved cached result: {result}")
                return result
            else:
                logger.info(f"Cache MISS for query: '{query}' (lookup took {lookup_time:.4f}s)")
                return None
        except Exception as e:
            logger.error(f"Error during cache lookup: {str(e)}", exc_info=True)
            return None
    
    def set(self, query: str, result: Dict[str, Any], expiry: int = 3600) -> bool:
        """
        Store parsed query results in cache.
        
        Args:
            query: The original search query
            result: The parsed query result to cache
            expiry: Cache expiration time in seconds (default: 1 hour)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.redis_enabled:
            logger.debug("Cache storage skipped - Redis disabled")
            return False
            
        try:
            cache_key = f"query:{query}"
            logger.debug(f"Storing result in cache with key: {cache_key}, expiry: {expiry}s")
            
            # Create a copy of the result that's safe to serialize
            cache_data = json.dumps(result)
            
            start_time = time.time()
            self.redis.setex(
                cache_key,
                expiry,
                cache_data
            )
            storage_time = time.time() - start_time
            
            result_size = len(cache_data)
            logger.info(f"Cached result for query: '{query}' ({result_size} bytes, took {storage_time:.4f}s)")
            return True
        except Exception as e:
            logger.error(f"Error storing result in cache: {str(e)}", exc_info=True)
            return False
