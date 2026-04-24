from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adspixel import AdsPixel
from facebook_business.adobjects.customaudience import CustomAudience

from src.types.config import MetaAdsConfig
from src.utils.logger import logger


class MetaAdsService:
    def __init__(self, config: MetaAdsConfig):
        self.config = config
        self.api = FacebookAdsApi.init(
            app_id=config.app_id or "",
            app_secret=config.app_secret or "",
            access_token=config.access_token,
            api_version=config.api_version,
        )
        self.AdAccount = AdAccount
        self.Campaign = Campaign
        self.AdSet = AdSet
        self.Ad = Ad
        self.AdCreative = AdCreative
        self.AdsPixel = AdsPixel
        self.CustomAudience = CustomAudience

        logger.info(f"MetaAdsService initialized (api_version={config.api_version})")

    def normalize_account_id(self, account_id: str) -> str:
        return account_id if account_id.startswith("act_") else f"act_{account_id}"

    def paginate_all(self, cursor) -> list:
        results = list(cursor)
        while cursor.load_next_page():
            results.extend(list(cursor))
        return results

    def paginate_with_limit(self, cursor, max_results: int) -> list:
        results = list(cursor)
        if len(results) >= max_results:
            return results[:max_results]
        while cursor.load_next_page() and len(results) < max_results:
            results.extend(list(cursor))
        return results[:max_results]
