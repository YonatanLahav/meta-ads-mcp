from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adsinsights import AdsInsights

from src.services.base import MetaAdsService, READ_COST
from src.utils.logger import logger

DEFAULT_FIELDS = [
    "campaign_id",
    "campaign_name",
    "adset_id",
    "adset_name",
    "ad_id",
    "ad_name",
    "spend",
    "impressions",
    "clicks",
    "cpc",
    "cpm",
    "ctr",
    "reach",
    "frequency",
    "actions",
    "cost_per_action_type",
    "date_start",
    "date_stop",
]


class InsightsService(MetaAdsService):
    async def get_account_insights(
        self,
        account_id: str,
        date_preset: str = "last_7d",
        time_range: dict | None = None,
        level: str = "campaign",
        filtering: list[dict] | None = None,
        limit: int = 50,
    ) -> list[dict]:
        async def _op():
            account = AdAccount(self.normalize_account_id(account_id))
            params = {"level": level, "limit": limit}
            if time_range:
                params["time_range"] = time_range
            else:
                params["date_preset"] = date_preset
            if filtering:
                params["filtering"] = filtering
            cursor = account.get_insights(fields=DEFAULT_FIELDS, params=params)
            results = await self.paginate_with_limit(cursor, limit)
            logger.debug(f"Fetched {len(results)} insight rows for account {account_id}")
            return [dict(r) for r in results]

        return await self._execute(_op, account_id=account_id, cost=READ_COST)

    async def get_campaign_insights(
        self,
        campaign_id: str,
        date_preset: str = "last_7d",
        time_range: dict | None = None,
        breakdowns: list[str] | None = None,
        account_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        async def _op():
            campaign = Campaign(campaign_id)
            params = {"limit": limit}
            if time_range:
                params["time_range"] = time_range
            else:
                params["date_preset"] = date_preset
            if breakdowns:
                params["breakdowns"] = breakdowns
            cursor = campaign.get_insights(fields=DEFAULT_FIELDS, params=params)
            results = await self.paginate_with_limit(cursor, limit)
            logger.debug(f"Fetched {len(results)} insight rows for campaign {campaign_id}")
            return [dict(r) for r in results]

        return await self._execute(_op, account_id=account_id, cost=READ_COST)

    async def get_adset_insights(
        self,
        adset_id: str,
        date_preset: str = "last_7d",
        time_range: dict | None = None,
        breakdowns: list[str] | None = None,
        account_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        async def _op():
            adset = AdSet(adset_id)
            params = {"limit": limit}
            if time_range:
                params["time_range"] = time_range
            else:
                params["date_preset"] = date_preset
            if breakdowns:
                params["breakdowns"] = breakdowns
            cursor = adset.get_insights(fields=DEFAULT_FIELDS, params=params)
            results = await self.paginate_with_limit(cursor, limit)
            logger.debug(f"Fetched {len(results)} insight rows for ad set {adset_id}")
            return [dict(r) for r in results]

        return await self._execute(_op, account_id=account_id, cost=READ_COST)

    async def get_ad_insights(
        self,
        ad_id: str,
        date_preset: str = "last_7d",
        time_range: dict | None = None,
        breakdowns: list[str] | None = None,
        account_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        async def _op():
            ad = Ad(ad_id)
            params = {"limit": limit}
            if time_range:
                params["time_range"] = time_range
            else:
                params["date_preset"] = date_preset
            if breakdowns:
                params["breakdowns"] = breakdowns
            cursor = ad.get_insights(fields=DEFAULT_FIELDS, params=params)
            results = await self.paginate_with_limit(cursor, limit)
            logger.debug(f"Fetched {len(results)} insight rows for ad {ad_id}")
            return [dict(r) for r in results]

        return await self._execute(_op, account_id=account_id, cost=READ_COST)
