import asyncio
from typing import Awaitable, Callable, TypeVar

from facebook_business.api import FacebookAdsApi

from src.types.config import MetaAdsConfig
from src.utils.error_handler import handle_meta_api_error
from src.utils.retry import ExponentialBackoff
from src.utils.logger import logger

T = TypeVar("T")


class MetaAdsService:
    def __init__(self, config: MetaAdsConfig):
        self.config = config
        self.api = FacebookAdsApi.init(
            app_id=config.app_id or "",
            app_secret=config.app_secret or "",
            access_token=config.access_token,
            api_version=config.api_version,
        )
        self.backoff = ExponentialBackoff()
        logger.info(f"MetaAdsService initialized (api_version={config.api_version})")

    def normalize_account_id(self, account_id: str) -> str:
        return account_id if account_id.startswith("act_") else f"act_{account_id}"

    async def paginate_with_limit(self, cursor, max_results: int) -> list:
        def _sync():
            results = list(cursor)
            if len(results) >= max_results:
                return results[:max_results]
            while cursor.load_next_page() and len(results) < max_results:
                results.extend(list(cursor))
            return results[:max_results]
        return await asyncio.to_thread(_sync)

    async def _execute(self, operation: Callable[[], Awaitable[T]]) -> T:
        async def _wrapped():
            try:
                return await operation()
            except Exception as e:
                raise handle_meta_api_error(e)
        return await self.backoff.execute(_wrapped)
