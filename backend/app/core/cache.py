import redis
import json
from typing import Any, Optional
from app.core.config import settings

class RedisCache:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
        except Exception as e:
            print(f"Redis connection error: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration"""
        if not self.redis_client:
            return False
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, expire, serialized_value)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def setex(self, key: str, expire: int, value: str) -> bool:
        """Set value with expiration (string value)"""
        if not self.redis_client:
            return False
        try:
            return self.redis_client.setex(key, expire, value)
        except Exception as e:
            print(f"Cache setex error: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """Delete keys from cache"""
        if not self.redis_client:
            return 0
        try:
            return self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache delete error: {e}")
            return 0
    
    def keys(self, pattern: str) -> list:
        """Get keys matching pattern"""
        if not self.redis_client:
            return []
        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            print(f"Cache keys error: {e}")
            return []
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

# Global cache instance
cache = RedisCache()

def get_redis_client():
    """Get Redis client instance"""
    return cache