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
from src.resources.accounts import get_account_resource_defs, read_accounts
from src.services.account import AccountService
from src.services.ad import AdService
from src.services.adset import AdSetService
from src.services.audience import AudienceService
from src.services.campaign import CampaignService
from src.services.creative import CreativeService
from src.services.insights import InsightsService
from src.tools.account import get_account_tool_defs, _list_ad_accounts
from src.tools.ad import get_ad_tool_defs, _list_ads, _get_ad
from src.tools.adset import get_adset_tool_defs, _list_ad_sets, _get_ad_set
from src.tools.audience import get_audience_tool_defs, _list_custom_audiences, _get_custom_audience
from src.tools.creative import (
    get_creative_tool_defs,
    _list_ad_creatives,
    _get_ad_creative,
    _get_ad_preview,
    _list_ad_images,
)
from src.tools.campaign import (
    get_campaign_read_tool_defs,
    _list_campaigns,
    _get_campaign,
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
    all_resources: list = []
    tool_handlers: dict[str, Any] = {}
    resource_handlers: dict[str, Any] = {}
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
        adset_service = AdSetService(meta_config, rate_limiter)
        ad_service = AdService(meta_config, rate_limiter)
        creative_service = CreativeService(meta_config, rate_limiter)
        audience_service = AudienceService(meta_config, rate_limiter)
        insights_service = InsightsService(meta_config, rate_limiter)

        all_tools.extend(get_account_tool_defs())
        all_tools.extend(get_campaign_read_tool_defs())
        all_tools.extend(get_adset_tool_defs())
        all_tools.extend(get_ad_tool_defs())
        all_tools.extend(get_creative_tool_defs())
        all_tools.extend(get_audience_tool_defs())
        all_tools.extend(get_insights_tool_defs())

        all_resources.extend(get_account_resource_defs())

        resource_handlers.update({
            "meta-ads://accounts": partial(read_accounts, account_service),
        })

        tool_handlers.update({
            "list_ad_accounts": partial(_list_ad_accounts, account_service),
            "list_campaigns": partial(_list_campaigns, campaign_service),
            "get_campaign": partial(_get_campaign, campaign_service),
            "list_ad_sets": partial(_list_ad_sets, adset_service),
            "get_ad_set": partial(_get_ad_set, adset_service),
            "list_ads": partial(_list_ads, ad_service),
            "get_ad": partial(_get_ad, ad_service),
            "list_ad_creatives": partial(_list_ad_creatives, creative_service),
            "get_ad_creative": partial(_get_ad_creative, creative_service),
            "get_ad_preview": partial(_get_ad_preview, creative_service),
            "list_ad_images": partial(_list_ad_images, creative_service),
            "list_custom_audiences": partial(_list_custom_audiences, audience_service),
            "get_custom_audience": partial(_get_custom_audience, audience_service),
            "get_account_insights": partial(_get_account_insights, insights_service),
            "get_campaign_insights": partial(_get_campaign_insights, insights_service),
            "get_adset_insights": partial(_get_adset_insights, insights_service),
            "get_ad_insights": partial(_get_ad_insights, insights_service),
        })

        logger.info(f"Registered {len(all_tools)} tools, {len(all_resources)} resources")
    else:
        logger.warning("No valid token — server will start but tools will require configuration")

    @server.list_resources()
    async def list_resources():
        return all_resources

    @server.read_resource()
    async def read_resource(uri):
        if not token_valid:
            raise ValueError("Meta Ads MCP Server is not configured — run 'python scripts/auth.py' to authenticate")

        handler = resource_handlers.get(str(uri))
        if not handler:
            raise ValueError(f"Unknown resource: {uri}")

        try:
            return await handler()
        except Exception as e:
            logger.error(f"Resource read failed for {uri}: {e}")
            raise

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
