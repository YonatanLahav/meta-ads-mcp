from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.user import User

from src.services.base import MetaAdsService
from src.utils.logger import logger

DEFAULT_FIELDS = [
    AdAccount.Field.id,
    AdAccount.Field.name,
    AdAccount.Field.account_id,
    AdAccount.Field.account_status,
    AdAccount.Field.currency,
    AdAccount.Field.timezone_name,
    AdAccount.Field.amount_spent,
    AdAccount.Field.balance,
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
