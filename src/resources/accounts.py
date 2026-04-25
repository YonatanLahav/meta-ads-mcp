import json

from mcp.types import Resource

from src.services.account import AccountService

ACCOUNTS_URI = "meta-ads://accounts"


def get_account_resource_defs() -> list[Resource]:
    return [
        Resource(
            uri=ACCOUNTS_URI,
            name="Ad Accounts",
            description="List all Meta Ads accounts accessible with the current token. Provides account IDs, names, account_status, currency, timezone_name, amount_spent, and balance.",
            mimeType="application/json",
        ),
    ]


async def read_accounts(account_service: AccountService) -> str:
    accounts = await account_service.get_ad_accounts()
    return json.dumps({"count": len(accounts), "accounts": accounts}, indent=2)
