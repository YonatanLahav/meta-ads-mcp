import asyncio
import time

import pytest

from src.utils.rate_limiter import RateLimiter


class TestRateLimiterAcquire:
    async def test_allows_calls_under_limit(self):
        rl = RateLimiter(max_points=10, window_seconds=60)
        await rl.acquire("act_1", cost=1)
        await rl.acquire("act_1", cost=1)
        bucket = rl._bucket("act_1")
        assert bucket.score() == 2

    async def test_tracks_accounts_independently(self):
        rl = RateLimiter(max_points=10, window_seconds=60)
        await rl.acquire("act_1", cost=5)
        await rl.acquire("act_2", cost=3)
        assert rl._bucket("act_1").score() == 5
        assert rl._bucket("act_2").score() == 3

    async def test_delays_when_at_limit(self):
        rl = RateLimiter(max_points=5, window_seconds=0.2)
        for _ in range(5):
            await rl.acquire("act_1", cost=1)

        start = time.monotonic()
        await rl.acquire("act_1", cost=1)
        elapsed = time.monotonic() - start
        assert elapsed >= 0.1

    async def test_write_cost_counted_correctly(self):
        rl = RateLimiter(max_points=10, window_seconds=60)
        await rl.acquire("act_1", cost=3)
        await rl.acquire("act_1", cost=3)
        await rl.acquire("act_1", cost=3)
        assert rl._bucket("act_1").score() == 9


class TestRateLimiterBlock:
    async def test_record_rate_limit_error_blocks_account(self):
        rl = RateLimiter(max_points=100, window_seconds=60, block_seconds=0.2)
        rl.record_rate_limit_error("act_1")

        start = time.monotonic()
        await rl.acquire("act_1", cost=1)
        elapsed = time.monotonic() - start
        assert elapsed >= 0.15

    async def test_block_does_not_affect_other_accounts(self):
        rl = RateLimiter(max_points=100, window_seconds=60, block_seconds=5.0)
        rl.record_rate_limit_error("act_1")

        start = time.monotonic()
        await rl.acquire("act_2", cost=1)
        elapsed = time.monotonic() - start
        assert elapsed < 0.1


class TestBucketPurge:
    async def test_old_calls_expire(self):
        rl = RateLimiter(max_points=5, window_seconds=0.2)
        await rl.acquire("act_1", cost=5)
        assert rl._bucket("act_1").score() == 5

        await asyncio.sleep(0.25)

        rl._bucket("act_1").purge(time.monotonic(), rl.window_seconds)
        assert rl._bucket("act_1").score() == 0
