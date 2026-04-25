try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import asyncio
import json
from functools import partial
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from src.config.settings import load_meta_config
from src.services.account import AccountService
from src.services.campaign import CampaignService
from src.services.insights import InsightsService
from src.tools.account import get_account_tool_defs, _list_ad_accounts
from src.tools.campaign import (
    get_campaign_tool_defs,
    _list_campaigns,
    _get_campaign,
    _create_campaign,
    _update_campaign,
    _delete_campaign,
)
from src.tools.insights import (
    get_insights_tool_defs,
    _get_account_insights,
    _get_campaign_insights,
    _get_adset_insights,
    _get_ad_insights,
)
from src.utils.error_handler import handle_meta_api_error
from src.utils.logger import logger
from src.utils.rate_limiter import RateLimiter
from src.utils.token_manager import ensure_valid_token


def create_server() -> Server:
    server = Server("meta-ads-mcp-server")
    meta_config = load_meta_config()

    all_tools: list = []
    tool_handlers: dict[str, Any] = {}
    token_valid = False

    if meta_config:
        valid_token = ensure_valid_token(
            meta_config.access_token,
            meta_config.app_id,
            meta_config.app_secret,
            meta_config.api_version,
        )
        if valid_token:
            meta_config = meta_config.model_copy(update={"access_token": valid_token})
            token_valid = True
        else:
            logger.warning("Token invalid — tools will fail until a valid token is provided")

    if meta_config and token_valid:
        rate_limiter = RateLimiter()
        account_service = AccountService(meta_config)
        campaign_service = CampaignService(meta_config, rate_limiter)
        insights_service = InsightsService(meta_config, rate_limiter)

        all_tools.extend(get_account_tool_defs())
        all_tools.extend(get_campaign_tool_defs())
        all_tools.extend(get_insights_tool_defs())

        tool_handlers.update({
            "list_ad_accounts": partial(_list_ad_accounts, account_service),
            "list_campaigns": partial(_list_campaigns, campaign_service),
            "get_campaign": partial(_get_campaign, campaign_service),
            "create_campaign": partial(_create_campaign, campaign_service),
            "update_campaign": partial(_update_campaign, campaign_service),
            "delete_campaign": partial(_delete_campaign, campaign_service),
            "get_account_insights": partial(_get_account_insights, insights_service),
            "get_campaign_insights": partial(_get_campaign_insights, insights_service),
            "get_adset_insights": partial(_get_adset_insights, insights_service),
            "get_ad_insights": partial(_get_ad_insights, insights_service),
        })

        logger.info(f"Registered {len(all_tools)} tools")
    else:
        logger.warning("No valid token — server will start but tools will require configuration")

    @server.list_tools()
    async def list_tools():
        return all_tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if not token_valid:
            error_msg = "Meta Ads MCP Server is not configured" if not meta_config else "Access token is invalid or expired"
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": error_msg,
                    "help": {
                        "steps": [
                            "1. Run 'python scripts/auth.py' to authenticate, OR",
                            "2. Get a token from https://developers.facebook.com/tools/explorer/",
                            "3. Set META_ACCESS_TOKEN in .env or Claude Desktop config",
                        ]
                    },
                }, indent=2),
            )]

        handler = tool_handlers.get(name)
        if not handler:
            return [TextContent(type="text", text=json.dumps({"success": False, "error": f"Unknown tool: {name}"}, indent=2))]

        try:
            return await handler(arguments)
        except Exception as e:
            meta_error = handle_meta_api_error(e)
            return [TextContent(type="text", text=json.dumps(meta_error.to_dict(), indent=2))]

    return server


async def run():
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
