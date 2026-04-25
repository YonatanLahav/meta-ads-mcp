import asyncio
import time
from dataclasses import dataclass, field

from src.utils.logger import logger

DEFAULT_WINDOW_SECONDS = 300
DEFAULT_MAX_POINTS = 190
DEFAULT_BLOCK_SECONDS = 60


@dataclass
class _AccountBucket:
    calls: list[tuple[float, int]] = field(default_factory=list)
    blocked_until: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def purge(self, now: float, window: float):
        cutoff = now - window
        self.calls = [(ts, pts) for ts, pts in self.calls if ts > cutoff]

    def score(self) -> int:
        return sum(pts for _, pts in self.calls)


class RateLimiter:
    def __init__(
        self,
        max_points: int = DEFAULT_MAX_POINTS,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
        block_seconds: float = DEFAULT_BLOCK_SECONDS,
    ):
        self.max_points = max_points
        self.window_seconds = window_seconds
        self.block_seconds = block_seconds
        self._buckets: dict[str, _AccountBucket] = {}

    def _bucket(self, account_id: str) -> _AccountBucket:
        if account_id not in self._buckets:
            self._buckets[account_id] = _AccountBucket()
        return self._buckets[account_id]

    async def acquire(self, account_id: str, cost: int = 1):
        bucket = self._bucket(account_id)

        async with bucket.lock:
            now = time.monotonic()

            if bucket.blocked_until > now:
                wait = bucket.blocked_until - now
                logger.warning(
                    f"Rate limiter: account {account_id} blocked for {wait:.1f}s"
                )
                await asyncio.sleep(wait)
                now = time.monotonic()

            bucket.purge(now, self.window_seconds)

            while bucket.score() + cost > self.max_points:
                wait = self._earliest_expiry(bucket, now, cost)
                logger.warning(
                    f"Rate limiter: account {account_id} at {bucket.score()}/{self.max_points} points, "
                    f"delaying {wait:.1f}s"
                )
                await asyncio.sleep(wait)
                now = time.monotonic()
                bucket.purge(now, self.window_seconds)

            bucket.calls.append((now, cost))

    def record_rate_limit_error(self, account_id: str):
        bucket = self._bucket(account_id)
        bucket.blocked_until = time.monotonic() + self.block_seconds
        logger.warning(
            f"Rate limiter: account {account_id} hit API rate limit, "
            f"blocking for {self.block_seconds}s"
        )

    def _earliest_expiry(self, bucket: _AccountBucket, now: float, cost: int) -> float:
        target = self.max_points - cost
        cumulative = bucket.score()
        for ts, pts in sorted(bucket.calls):
            cumulative -= pts
            if cumulative <= target:
                return max((ts + self.window_seconds) - now, 0.1)
        return self.window_seconds
