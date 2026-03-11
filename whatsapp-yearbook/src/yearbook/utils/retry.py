from __future__ import annotations

import time
import logging
from typing import Callable, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


def retry(
    func: Callable[..., T],
    *args,
    max_attempts: int = 3,
    delay: float = 2.0,
    exceptions: tuple = (Exception,),
    **kwargs,
) -> T:
    """Retry a function up to max_attempts times on failure."""
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exc = e
            if attempt < max_attempts:
                logger.warning(
                    "Attempt %d/%d failed: %s — retrying in %.1fs",
                    attempt,
                    max_attempts,
                    e,
                    delay,
                )
                time.sleep(delay)
            else:
                logger.error("All %d attempts failed: %s", max_attempts, e)
    raise last_exc  # type: ignore[misc]
