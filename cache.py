"""Caching utilities for API responses.

Provides simple in-memory caching with TTL (time-to-live) support
to reduce API calls and improve performance.
"""

import time
from typing import Any, Optional, Dict
from functools import wraps


class Cache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, ttl: int = 300):
        """Initialize cache.

        Args:
            ttl: Time-to-live in seconds for cached items
        """
        self.ttl = ttl
        self._cache: Dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        """Set item in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def delete(self, key: str) -> None:
        """Delete specific cache entry.

        Args:
            key: Cache key to delete
        """
        if key in self._cache:
            del self._cache[key]


# Global cache instance
_cache = Cache(ttl=300)


def cached(ttl: int = 300):
    """Decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds
    """
    def decorator(func):
        cache = Cache(ttl=ttl)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{args}:{kwargs}"

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        return wrapper
    return decorator


__all__ = ["Cache", "cached", "_cache"]

