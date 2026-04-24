from facebook_business.adobjects.campaign import Campaign

from src.services.base import MetaAdsService
from src.utils.retry import ExponentialBackoff
from src.utils.error_handler import handle_meta_api_error
from src.utils.logger import logger

DEFAULT_FIELDS = [
    Campaign.Field.id,
    Campaign.Field.name,
    Campaign.Field.status,
    Campaign.Field.objective,
    Campaign.Field.daily_budget,
    Campaign.Field.lifetime_budget,
    Campaign.Field.created_time,
    Campaign.Field.updated_time,
]


class CampaignService(MetaAdsService):
    def __init__(self, config):
        super().__init__(config)
        self.backoff = ExponentialBackoff()

    async def get_campaigns(
        self,
        account_id: str,
        limit: int = 100,
        fields: list[str] | None = None,
        filtering: list[dict] | None = None,
    ) -> list:
        async def _fetch():
            try:
                account = self.AdAccount(self.normalize_account_id(account_id))
                params = {"limit": limit}
                if filtering:
                    params["filtering"] = filtering
                cursor = account.get_campaigns(fields=fields or DEFAULT_FIELDS, params=params)
                results = self.paginate_with_limit(cursor, limit)
                logger.info(f"Fetched {len(results)} campaigns for {account_id}")
                return [dict(c) for c in results]
            except Exception as e:
                raise handle_meta_api_error(e)

        return await self.backoff.execute(_fetch)

    async def get_campaign(self, campaign_id: str, fields: list[str] | None = None) -> dict:
        async def _fetch():
            try:
                campaign = self.Campaign(campaign_id)
                result = campaign.api_get(fields=fields or DEFAULT_FIELDS)
                return dict(result)
            except Exception as e:
                raise handle_meta_api_error(e)

        return await self.backoff.execute(_fetch)

    async def create_campaign(self, account_id: str, data: dict) -> dict:
        async def _create():
            try:
                account = self.AdAccount(self.normalize_account_id(account_id))
                result = account.create_campaign(
                    fields=[Campaign.Field.id, Campaign.Field.name],
                    params=data,
                )
                logger.info(f"Campaign created: {result.get('id')}")
                return dict(result)
            except Exception as e:
                raise handle_meta_api_error(e)

        return await self.backoff.execute(_create)

    async def update_campaign(self, campaign_id: str, updates: dict) -> dict:
        async def _update():
            try:
                campaign = self.Campaign(campaign_id)
                campaign.api_update(params=updates)
                logger.info(f"Campaign updated: {campaign_id}")
                return {"id": campaign_id, "updated": True}
            except Exception as e:
                raise handle_meta_api_error(e)

        return await self.backoff.execute(_update)

    async def delete_campaign(self, campaign_id: str) -> dict:
        async def _delete():
            try:
                campaign = self.Campaign(campaign_id)
                campaign.api_delete()
                logger.info(f"Campaign deleted: {campaign_id}")
                return {"id": campaign_id, "deleted": True}
            except Exception as e:
                raise handle_meta_api_error(e)

        return await self.backoff.execute(_delete)
