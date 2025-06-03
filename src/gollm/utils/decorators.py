import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


def timer(func: Callable) -> Callable:
    """Dekorator mierzący czas wykonania funkcji"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        logger.debug(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result

    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Dekorator ponowienia próby w przypadku błędu"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper

    return decorator


def cache_result(ttl_seconds: int = 300):
    """Prosty dekorator cache z TTL"""

    def decorator(func: Callable) -> Callable:
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Utwórz klucz z argumentów
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()

            # Sprawdź czy wynik jest w cache i aktualny
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl_seconds:
                    return result

            # Wykonaj funkcję i zapisz wynik
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)

            return result

        return wrapper

    return decorator
