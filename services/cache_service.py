"""
Redis cache service with async support.
Implements caching interface with fault tolerance.

Features:
- Async Redis operations
- Connection pooling
- Automatic serialization/deserialization
- Graceful degradation on cache failures
- TTL management

Example Usage:
    cache = RedisCacheService(settings)
    await cache.connect()
    await cache.set("key", {"data": "value"}, ttl=3600)
    result = await cache.get("key")
"""

import json
from typing import Any

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from core.config import Settings
from core.logging_config import get_logger
from core.exceptions import CacheConnectionException

logger = get_logger(__name__)


class RedisCacheService:
    """
    Redis implementation of cache service.
    
    Attributes:
        settings: Application settings
        pool: Redis connection pool
        client: Redis client instance
    
    Example:
        >>> cache = RedisCacheService(settings)
        >>> await cache.connect()
        >>> await cache.set("user:123", {"name": "John"}, ttl=3600)
        >>> user = await cache.get("user:123")
        >>> print(user)  # {"name": "John"}
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize Redis cache service.
        
        Args:
            settings: Application settings containing Redis configuration
        """
        self.settings = settings
        self.pool: ConnectionPool | None = None
        self.client: redis.Redis | None = None
        self._connected = False
    
    async def connect(self) -> None:
        """
        Establish connection pool to Redis.
        
        Raises:
            CacheConnectionException: If connection fails
        """
        try:
            self.pool = ConnectionPool.from_url(
                self.settings.redis_url,
                max_connections=self.settings.redis_max_connections,
                decode_responses=False,  # We'll handle encoding
                socket_keepalive=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.client.ping()
            self._connected = True
            
            logger.info(
                "Redis connected",
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db,
                max_connections=self.settings.redis_max_connections
            )
            
        except RedisConnectionError as e:
            logger.error("Redis connection failed", error=str(e))
            raise CacheConnectionException(f"Failed to connect to Redis: {e}")
        except Exception as e:
            logger.error("Unexpected error connecting to Redis", error=str(e))
            raise CacheConnectionException(f"Unexpected Redis error: {e}")
    
    async def disconnect(self) -> None:
        """
        Close Redis connection pool gracefully.
        """
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        
        self._connected = False
        logger.info("Redis disconnected")
    
    async def get(self, key: str) -> Any | None:
        """
        Get value from Redis cache.
        
        Args:
            key: Cache key
        
        Returns:
            Deserialized value or None if not found
        
        Raises:
            CacheOperationException: If operation fails
        """
        if not self._connected or not self.client:
            logger.warning("Cache get attempted but not connected", key=key)
            return None
        
        try:
            value = await self.client.get(key)
            if value is None:
                logger.debug("Cache miss", key=key)
                return None
            
            # Deserialize JSON
            deserialized = json.loads(value)
            logger.debug("Cache hit", key=key)
            return deserialized
            
        except RedisError as e:
            logger.warning("Cache get failed", key=key, error=str(e))
            # Graceful degradation: return None on cache failure
            return None
        except json.JSONDecodeError as e:
            logger.error("Cache value deserialization failed", key=key, error=str(e))
            # Delete corrupted key
            await self.delete(key)
            return None
    
    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Set value in Redis cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (None = no expiration)
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            CacheOperationException: If operation fails critically
        """
        if not self._connected or not self.client:
            logger.warning("Cache set attempted but not connected", key=key)
            return False
        
        try:
            # Serialize to JSON
            serialized = json.dumps(value)
            
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)
            
            logger.debug("Cache set", key=key, ttl=ttl)
            return True
            
        except (RedisError, TypeError, ValueError) as e:
            logger.warning("Cache set failed", key=key, error=str(e))
            # Graceful degradation: don't fail the request
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis cache.
        
        Args:
            key: Cache key to delete
        
        Returns:
            True if key was deleted, False otherwise
        """
        if not self._connected or not self.client:
            return False
        
        try:
            result = await self.client.delete(key)
            logger.debug("Cache delete", key=key, deleted=bool(result))
            return bool(result)
            
        except RedisError as e:
            logger.warning("Cache delete failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists, False otherwise
        """
        if not self._connected or not self.client:
            return False
        
        try:
            result = await self.client.exists(key)
            return bool(result)
            
        except RedisError as e:
            logger.warning("Cache exists check failed", key=key, error=str(e))
            return False
    
    async def ping(self) -> bool:
        """
        Check Redis connection health.
        
        Returns:
            True if Redis is reachable, False otherwise
        """
        if not self.client:
            return False
        
        try:
            await self.client.ping()
            return True
        except RedisError:
            return False

