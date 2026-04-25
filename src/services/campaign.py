from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign

from src.services.base import MetaAdsService, READ_COST, WRITE_COST
from src.utils.logger import logger

DEFAULT_FIELDS = [
    "id",
    "name",
    "status",
    "effective_status",
    "objective",
    "daily_budget",
    "lifetime_budget",
    "created_time",
    "updated_time",
]


class CampaignService(MetaAdsService):
    async def get_campaigns(
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
            cursor = account.get_campaigns(fields=DEFAULT_FIELDS, params=params)
            results = await self.paginate_with_limit(cursor, limit)
            logger.debug(f"Fetched {len(results)} campaigns for account {account_id}")
            return [dict(c) for c in results]

        return await self._execute(_op, account_id=account_id, cost=READ_COST)

    async def get_campaign(self, campaign_id: str, account_id: str | None = None) -> dict:
        async def _op():
            campaign = Campaign(campaign_id)
            return dict(campaign.api_get(fields=DEFAULT_FIELDS))

        return await self._execute(_op, account_id=account_id, cost=READ_COST)

    async def create_campaign(self, account_id: str, data: dict) -> dict:
        async def _op():
            account = AdAccount(self.normalize_account_id(account_id))
            result = account.create_campaign(params=data)
            logger.debug(f"Campaign created: {result.get('id')}")
            return dict(result)

        return await self._execute(_op, account_id=account_id, cost=WRITE_COST)

    async def update_campaign(self, campaign_id: str, updates: dict, account_id: str | None = None) -> dict:
        async def _op():
            campaign = Campaign(campaign_id)
            campaign.api_update(params=updates)
            logger.debug(f"Campaign updated: {campaign_id}")
            return {"id": campaign_id, "updated": True}

        return await self._execute(_op, account_id=account_id, cost=WRITE_COST)

    async def delete_campaign(self, campaign_id: str, account_id: str | None = None) -> dict:
        async def _op():
            campaign = Campaign(campaign_id)
            campaign.api_delete()
            logger.debug(f"Campaign deleted: {campaign_id}")
            return {"id": campaign_id, "deleted": True}

        return await self._execute(_op, account_id=account_id, cost=WRITE_COST)
