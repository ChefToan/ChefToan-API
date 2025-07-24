# src/services/redis_service.py - FIXED VERSION
import redis
import json
import time
import functools
import datetime
import config

# Global redis client
redis_client = None


# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)


def date_deserializer(dct):
    """Convert ISO date strings back to datetime.date objects"""
    for key, value in dct.items():
        if isinstance(value, str) and len(value) == 10 and value[4] == '-' and value[7] == '-':
            try:
                dct[key] = datetime.date.fromisoformat(value)
            except ValueError:
                pass
    return dct


def init_redis(app):
    """Initialize Redis connection"""
    global redis_client
    redis_client = redis.from_url(config.REDIS_URL)

    # Test connection
    try:
        redis_client.ping()
        print("Redis connection established")
    except redis.ConnectionError:
        print("Redis connection failed - caching disabled")
        config.REDIS_ENABLED = False


def cache_get(key):
    """Get data from cache"""
    if not config.REDIS_ENABLED or redis_client is None:
        return None

    data = redis_client.get(key)
    if data:
        return json.loads(data, object_hook=date_deserializer)
    return None


def cache_get_with_timestamp(key):
    """Get data and timestamp from cache"""
    if not config.REDIS_ENABLED or redis_client is None:
        return None, None

    # Get both the data and its timestamp
    data = redis_client.get(key)
    timestamp = redis_client.get(f"{key}:timestamp")

    if data and timestamp:
        return json.loads(data, object_hook=date_deserializer), float(timestamp)
    return None, None


def cache_set(key, value, timeout=None):
    """Set data in cache"""
    if not config.REDIS_ENABLED or redis_client is None:
        return

    timeout = timeout or config.REDIS_CACHE_TIMEOUT
    redis_client.setex(key, timeout, json.dumps(value, cls=DateTimeEncoder))
    redis_client.setex(f"{key}:timestamp", timeout, time.time())


def cached(timeout=None, use_stale_on_error=False):
    """
    Decorator to cache function results based on arguments.
    FIXED VERSION - Actually uses cached data instead of always calling function!

    Args:
        timeout: Cache expiration time in seconds
        use_stale_on_error: Whether to use stale cached data when function fails
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not config.REDIS_ENABLED or redis_client is None:
                return func(*args, **kwargs)

            # Create a cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache first
            cached_data, timestamp = cache_get_with_timestamp(cache_key)
            cache_timeout = timeout or config.REDIS_CACHE_TIMEOUT

            try:
                # FIXED: Check if we have valid cached data first
                if cached_data is not None and timestamp is not None:
                    # Check if cache is still valid
                    cache_age = time.time() - timestamp
                    if cache_age < cache_timeout:
                        # Cache hit - return cached data immediately
                        print(f"Cache HIT for {func.__name__} (age: {cache_age:.1f}s)")
                        return cached_data
                    else:
                        print(f"Cache EXPIRED for {func.__name__} (age: {cache_age:.1f}s)")

                # Cache miss or expired - call function and cache result
                print(f"Cache MISS for {func.__name__} - calling function")
                result = func(*args, **kwargs)
                cache_set(cache_key, result, cache_timeout)
                return result

            except Exception as e:
                # If we should use stale data on error and we have cached data
                if use_stale_on_error and cached_data is not None:
                    print(
                        f"Error calling {func.__name__}, using stale cached data from "
                        f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}: {str(e)}"
                    )
                    return cached_data
                # Otherwise, re-raise the exception
                raise

        return wrapper

    return decorator


def cache_invalidate(pattern=None):
    """Invalidate cache entries matching a pattern"""
    if not config.REDIS_ENABLED or redis_client is None:
        return

    if pattern:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            print(f"Invalidated {len(keys)} cache entries matching pattern: {pattern}")
    else:
        redis_client.flushdb()
        print("Flushed entire cache database")


def get_cache_stats():
    """Get cache statistics"""
    if not config.REDIS_ENABLED or redis_client is None:
        return {"enabled": False}

    info = redis_client.info()
    return {
        "enabled": True,
        "keys": info.get("db0", {}).get("keys", 0),
        "memory_used": info.get("used_memory_human", "0"),
        "hits": info.get("keyspace_hits", 0),
        "misses": info.get("keyspace_misses", 0),
        "hit_rate": info.get("keyspace_hits", 0) / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)) * 100
    }