from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.ad import Ad

from src.services.base import MetaAdsService, READ_COST
from src.utils.logger import logger

DEFAULT_FIELDS = [
    Ad.Field.id,
    Ad.Field.name,
    Ad.Field.adset_id,
    Ad.Field.campaign_id,
    Ad.Field.status,
    Ad.Field.creative,
    Ad.Field.created_time,
    Ad.Field.updated_time,
]


class AdService(MetaAdsService):
    async def get_ads(
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
            cursor = account.get_ads(fields=DEFAULT_FIELDS, params=params)
            results = await self.paginate_with_limit(cursor, limit)
            logger.debug(f"Fetched {len(results)} ads for account {account_id}")
            return [dict(a) for a in results]

        return await self._execute(_op, account_id=account_id, cost=READ_COST)

    async def get_ad(self, ad_id: str, account_id: str | None = None) -> dict:
        async def _op():
            ad = Ad(ad_id)
            return dict(ad.api_get(fields=DEFAULT_FIELDS))

        return await self._execute(_op, account_id=account_id, cost=READ_COST)
