from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.ad import Ad

from src.services.base import MetaAdsService, READ_COST
from src.utils.logger import logger

DEFAULT_CREATIVE_FIELDS = [
    "id",
    "name",
    "title",
    "body",
    "image_url",
    "image_hash",
    "call_to_action_type",
    "object_story_spec",
    "status",
    "created_time",
    "updated_time",
]

DEFAULT_IMAGE_FIELDS = [
    "id",
    "hash",
    "url",
    "url_128",
    "width",
    "height",
    "created_time",
    "status",
]


class CreativeService(MetaAdsService):
    async def get_ad_creatives(
        self,
        account_id: str,
        limit: int = 100,
    ) -> list[dict]:
        async def _op():
            account = AdAccount(self.normalize_account_id(account_id))
            cursor = account.get_ad_creatives(fields=DEFAULT_CREATIVE_FIELDS, params={"limit": limit})
            results = await self.paginate_with_limit(cursor, limit)
            logger.debug(f"Fetched {len(results)} creatives for account {account_id}")
            return [dict(c) for c in results]

        return await self._execute(_op, account_id=account_id, cost=READ_COST)

    async def get_ad_creative(self, creative_id: str, account_id: str | None = None) -> dict:
        async def _op():
            creative = AdCreative(creative_id)
            return dict(creative.api_get(fields=DEFAULT_CREATIVE_FIELDS))

        return await self._execute(_op, account_id=account_id, cost=READ_COST)

    async def get_ad_preview(
        self,
        ad_id: str,
        ad_format: str = "DESKTOP_FEED_STANDARD",
        account_id: str | None = None,
    ) -> list[dict]:
        async def _op():
            ad = Ad(ad_id)
            previews = ad.get_previews(params={"ad_format": ad_format})
            return [dict(p) for p in previews]

        return await self._execute(_op, account_id=account_id, cost=READ_COST)

    async def get_ad_images(
        self,
        account_id: str,
        limit: int = 100,
    ) -> list[dict]:
        async def _op():
            account = AdAccount(self.normalize_account_id(account_id))
            cursor = account.get_ad_images(fields=DEFAULT_IMAGE_FIELDS, params={"limit": limit})
            results = await self.paginate_with_limit(cursor, limit)
            logger.debug(f"Fetched {len(results)} images for account {account_id}")
            return [dict(i) for i in results]

        return await self._execute(_op, account_id=account_id, cost=READ_COST)
