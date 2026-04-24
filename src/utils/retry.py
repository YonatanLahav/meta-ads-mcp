import asyncio
import random
from typing import TypeVar, Callable, Awaitable

from src.utils.logger import logger
from src.utils.error_handler import is_retriable_error

T = TypeVar("T")


class ExponentialBackoff:
    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 32.0,
        max_retries: int = 5,
        jitter_factor: float = 0.1,
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.jitter_factor = jitter_factor

    async def execute(self, operation: Callable[[], Awaitable[T]]) -> T:
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                result = await operation()
                if attempt > 0:
                    logger.info(f"Operation succeeded after {attempt + 1} attempts")
                return result
            except Exception as error:
                last_error = error

                if not is_retriable_error(error):
                    raise

                if attempt == self.max_retries - 1:
                    logger.error(f"Max retries ({self.max_retries}) exceeded")
                    raise

                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                jitter = delay * self.jitter_factor * random.random()
                total_delay = delay + jitter

                logger.warning(
                    f"Retriable error, attempt {attempt + 1}/{self.max_retries}, "
                    f"retrying in {total_delay:.1f}s: {error}"
                )
                await asyncio.sleep(total_delay)

        raise last_error or Exception("Max retries exceeded")
