from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet

from src.services.base import MetaAdsService, READ_COST
from src.utils.logger import logger

DEFAULT_FIELDS = [
    "id",
    "name",
    "campaign_id",
    "status",
    "effective_status",
    "daily_budget",
    "lifetime_budget",
    "targeting",
    "optimization_goal",
    "billing_event",
    "bid_amount",
    "start_time",
    "end_time",
    "created_time",
    "updated_time",
]


class AdSetService(MetaAdsService):
    async def get_ad_sets(
        self,
        account_id: str,
        limit: int = 100,
        filtering: list[dict] | None = None,
    ) -> list[dict]:
        async def _op():
            account = AdAccount(self.normalize_account_id(account_id))
            params = {"limit": limit}
            if filtering:
                params["filtering"] = filtering
            cursor = account.get_ad_sets(fields=DEFAULT_FIELDS, params=params)
            results = await self.paginate_with_limit(cursor, limit)
            logger.debug(f"Fetched {len(results)} ad sets for account {account_id}")
            return [dict(a) for a in results]

        return await self._execute(_op, account_id=account_id, cost=READ_COST)

    async def get_ad_set(self, adset_id: str, account_id: str | None = None) -> dict:
        async def _op():
            adset = AdSet(adset_id)
            return dict(adset.api_get(fields=DEFAULT_FIELDS))

        return await self._execute(_op, account_id=account_id, cost=READ_COST)
