from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.customaudience import CustomAudience

from src.services.base import MetaAdsService, READ_COST
from src.utils.logger import logger

DEFAULT_FIELDS = [
    "id",
    "name",
    "description",
    "subtype",
    "approximate_count_lower_bound",
    "approximate_count_upper_bound",
    "data_source",
    "time_created",
    "time_updated",
]


class AudienceService(MetaAdsService):
    async def get_custom_audiences(
        self,
        account_id: str,
        limit: int = 100,
    ) -> list[dict]:
        async def _op():
            account = AdAccount(self.normalize_account_id(account_id))
            cursor = account.get_custom_audiences(fields=DEFAULT_FIELDS, params={"limit": limit})
            results = await self.paginate_with_limit(cursor, limit)
            logger.debug(f"Fetched {len(results)} audiences for account {account_id}")
            return [dict(a) for a in results]

        return await self._execute(_op, account_id=account_id, cost=READ_COST)

    async def get_custom_audience(self, audience_id: str, account_id: str | None = None) -> dict:
        async def _op():
            audience = CustomAudience(audience_id)
            return dict(audience.api_get(fields=DEFAULT_FIELDS))

        return await self._execute(_op, account_id=account_id, cost=READ_COST)
