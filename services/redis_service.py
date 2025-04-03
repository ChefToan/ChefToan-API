import redis
import json
import time
import functools
import datetime
from flask import current_app

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
        return json.loads(data, object_hook=date_deserializer)
    return None


def cache_get_with_timestamp(key):
    """Get data and timestamp from cache"""
    if not current_app.config['REDIS_ENABLED'] or redis_client is None:
        return None, None

    # Get both the data and its timestamp
    data = redis_client.get(key)
    timestamp = redis_client.get(f"{key}:timestamp")

    if data and timestamp:
        return json.loads(data, object_hook=date_deserializer), float(timestamp)
    return None, None


def cache_set(key, value, timeout=None):
    """Set data in cache"""
    if not current_app.config['REDIS_ENABLED'] or redis_client is None:
        return

    timeout = timeout or current_app.config['REDIS_CACHE_TIMEOUT']
    redis_client.setex(key, timeout, json.dumps(value, cls=DateTimeEncoder))
    redis_client.setex(f"{key}:timestamp", timeout, time.time())


def cached(timeout=None, use_stale_on_error=False):
    """
    Decorator to cache function results based on arguments.

    Args:
        timeout: Cache expiration time in seconds
        use_stale_on_error: Whether to use stale cached data when function fails
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not current_app.config['REDIS_ENABLED'] or redis_client is None:
                return func(*args, **kwargs)

            # Create a cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache first
            cached_data, timestamp = cache_get_with_timestamp(cache_key)
            cache_timeout = timeout or current_app.config['REDIS_CACHE_TIMEOUT']

            try:
                # If not in cache or cache is expired, call the function
                if cached_data is None:
                    result = func(*args, **kwargs)
                    cache_set(cache_key, result, cache_timeout)
                    return result

                # Call the function and update cache
                result = func(*args, **kwargs)
                cache_set(cache_key, result, cache_timeout)
                return result

            except Exception as e:
                # If we should use stale data on error and we have cached data
                if use_stale_on_error and cached_data is not None:
                    current_app.logger.warning(
                        f"Error calling {func.__name__}, using stale cached data from "
                        f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}: {str(e)}"
                    )
                    return cached_data
                # Otherwise, re-raise the exception
                raise

        return wrapper

    return decorator