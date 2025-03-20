import redis
import json
import functools
from flask import current_app

# Global redis client
redis_client = None


def init_redis(app):
    """Initialize Redis connection"""
    global redis_client
    redis_client = redis.from_url(app.config['REDIS_URL'])

    # Test connection
    try:
        redis_client.ping()
        app.logger.info("Redis connection established")
    except redis.ConnectionError:
        app.logger.warning("Redis connection failed - caching disabled")
        app.config['REDIS_ENABLED'] = False


def cache_get(key):
    """Get data from cache"""
    if not current_app.config['REDIS_ENABLED'] or redis_client is None:
        return None

    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None


def cache_set(key, value, timeout=None):
    """Set data in cache"""
    if not current_app.config['REDIS_ENABLED'] or redis_client is None:
        return

    timeout = timeout or current_app.config['REDIS_CACHE_TIMEOUT']
    redis_client.setex(key, timeout, json.dumps(value))


def cached(timeout=None):
    """Decorator to cache function results based on arguments"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not current_app.config['REDIS_ENABLED'] or redis_client is None:
                return func(*args, **kwargs)

            # Create a cache key from function name and arguments
            # For player data, the key will usually include the player tag
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache first
            cached_data = cache_get(cache_key)
            if cached_data is not None:
                return cached_data

            # If not in cache, call the function
            result = func(*args, **kwargs)

            # Save the result to cache
            cache_timeout = timeout or current_app.config['REDIS_CACHE_TIMEOUT']
            cache_set(cache_key, result, cache_timeout)

            return result

        return wrapper

    return decorator