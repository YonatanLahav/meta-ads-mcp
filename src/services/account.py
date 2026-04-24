from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.user import User

from src.services.base import MetaAdsService
from src.utils.retry import ExponentialBackoff
from src.utils.error_handler import handle_meta_api_error
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
    def __init__(self, config):
        super().__init__(config)
        self.backoff = ExponentialBackoff()

    async def get_ad_accounts(
        self,
        limit: int = 100,
        fields: list[str] | None = None,
    ) -> list:
        async def _fetch():
            try:
                me = User(fbid="me")
                cursor = me.get_ad_accounts(fields=fields or DEFAULT_FIELDS, params={"limit": limit})
                results = await self.paginate_with_limit(cursor, limit)
                logger.info(f"Fetched {len(results)} ad accounts")
                return [dict(a) for a in results]
            except Exception as e:
                raise handle_meta_api_error(e)

        return await self.backoff.execute(_fetch)
