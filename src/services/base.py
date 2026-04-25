import asyncio
from typing import Awaitable, Callable, TypeVar

from facebook_business.api import FacebookAdsApi

from src.types.config import MetaAdsConfig
from src.utils.error_handler import MetaAdsError, handle_meta_api_error
from src.utils.rate_limiter import RateLimiter
from src.utils.retry import ExponentialBackoff
from src.utils.logger import logger

T = TypeVar("T")

READ_COST = 1
WRITE_COST = 3


class MetaAdsService:
    def __init__(self, config: MetaAdsConfig, rate_limiter: RateLimiter | None = None):
        self.config = config
        self.api = FacebookAdsApi.init(
            app_id=config.app_id or "",
            app_secret=config.app_secret or "",
            access_token=config.access_token,
            api_version=config.api_version,
        )
        self.backoff = ExponentialBackoff()
        self.rate_limiter = rate_limiter
        logger.info(f"MetaAdsService initialized (api_version={config.api_version})")

    def normalize_account_id(self, account_id: str) -> str:
        return account_id if account_id.startswith("act_") else f"act_{account_id}"

    async def paginate_with_limit(self, cursor, max_results: int) -> list[dict]:
        def _sync():
            results = list(cursor)
            if len(results) >= max_results:
                return results[:max_results]
            while cursor.load_next_page() and len(results) < max_results:
                results.extend(list(cursor))
            return results[:max_results]
        return await asyncio.to_thread(_sync)

    async def _execute(
        self,
        operation: Callable[[], Awaitable[T]],
        account_id: str | None = None,
        cost: int = READ_COST,
    ) -> T:
        normalized_account = self.normalize_account_id(account_id) if account_id else None

        async def _wrapped():
            if self.rate_limiter and normalized_account:
                await self.rate_limiter.acquire(normalized_account, cost)
            try:
                return await operation()
            except Exception as e:
                err = handle_meta_api_error(e)
                if self.rate_limiter and normalized_account and err.is_rate_limit:
                    self.rate_limiter.record_rate_limit_error(normalized_account)
                raise err
        return await self.backoff.execute(_wrapped)
