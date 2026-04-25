from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.user import User

from src.services.base import MetaAdsService
from src.utils.logger import logger

DEFAULT_FIELDS = [
    "id",
    "name",
    "account_id",
    "account_status",
    "currency",
    "timezone_name",
    "amount_spent",
    "balance",
]


class AccountService(MetaAdsService):
    async def get_ad_accounts(self, limit: int = 100) -> list[dict]:
        async def _op():
            me = User(fbid="me")
            cursor = me.get_ad_accounts(fields=DEFAULT_FIELDS, params={"limit": limit})
            results = await self.paginate_with_limit(cursor, limit)
            logger.debug(f"Fetched {len(results)} ad accounts")
            return [dict(a) for a in results]

        return await self._execute(_op)
