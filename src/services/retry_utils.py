# src/services/retry_utils.py
import time
import requests
from functools import wraps
from flask import current_app


def retry_request(max_retries=3, backoff_factor=0.5, status_forcelist=(500, 502, 503, 504)):
    """
    Decorator to retry requests with exponential backoff.

    Args:
        max_retries: Maximum number of retries
        backoff_factor: Factor to apply to delay between retries
        status_forcelist: Status codes that trigger a retry
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    status_code = e.response.status_code
                    if status_code not in status_forcelist or retries == max_retries:
                        # If not in our list or we've exhausted retries, re-raise
                        raise

                    wait_time = backoff_factor * (2 ** retries)
                    current_app.logger.warning(
                        f"Request failed with status {status_code}. "
                        f"Retrying in {wait_time:.2f} seconds... "
                        f"(Attempt {retries + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    retries += 1
                except requests.exceptions.ConnectionError as e:
                    if retries == max_retries:
                        raise

                    wait_time = backoff_factor * (2 ** retries)
                    current_app.logger.warning(
                        f"Connection error: {str(e)}. "
                        f"Retrying in {wait_time:.2f} seconds... "
                        f"(Attempt {retries + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    retries += 1

        return wrapper

    return decorator