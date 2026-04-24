import pytest
from unittest.mock import AsyncMock, patch

from src.utils.retry import ExponentialBackoff
from src.utils.error_handler import MetaAdsError


class TestExponentialBackoff:
    @pytest.fixture
    def backoff(self):
        return ExponentialBackoff(base_delay=0.01, max_delay=0.1, max_retries=3)

    async def test_success_on_first_try(self, backoff):
        op = AsyncMock(return_value="ok")
        result = await backoff.execute(op)
        assert result == "ok"
        assert op.await_count == 1

    async def test_retries_on_retriable_error(self, backoff):
        retriable = MetaAdsError("rate limit", code=4)
        op = AsyncMock(side_effect=[retriable, retriable, "ok"])
        with patch("src.utils.retry.asyncio.sleep", new_callable=AsyncMock):
            result = await backoff.execute(op)
        assert result == "ok"
        assert op.await_count == 3

    async def test_raises_immediately_on_non_retriable(self, backoff):
        non_retriable = MetaAdsError("invalid param", code=100, status_code=400)
        op = AsyncMock(side_effect=non_retriable)
        with pytest.raises(MetaAdsError, match="invalid param"):
            await backoff.execute(op)
        assert op.await_count == 1

    async def test_raises_after_max_retries(self, backoff):
        retriable = MetaAdsError("rate limit", code=4)
        op = AsyncMock(side_effect=retriable)
        with patch("src.utils.retry.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(MetaAdsError, match="rate limit"):
                await backoff.execute(op)
        assert op.await_count == 3
