import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from src.config.settings import load_meta_config
from src.tools.account import get_account_tool_defs
from src.tools.campaign import get_campaign_tool_defs
from src.utils.logger import logger


def create_server() -> Server:
    server = Server("meta-ads-mcp-server")
    meta_config = load_meta_config()

    all_tools = []
    tool_handlers: dict[str, any] = {}

    if meta_config:
        from src.services.account import AccountService
        from src.services.campaign import CampaignService
        from src.tools.account import _list_ad_accounts
        from src.tools.campaign import (
            _list_campaigns,
            _get_campaign,
            _create_campaign,
            _update_campaign,
            _delete_campaign,
        )

        account_service = AccountService(meta_config)
        campaign_service = CampaignService(meta_config)

        all_tools.extend(get_account_tool_defs())
        all_tools.extend(get_campaign_tool_defs())

        tool_handlers.update({
            "list_ad_accounts": lambda args: _list_ad_accounts(account_service, args),
            "list_campaigns": lambda args: _list_campaigns(campaign_service, args),
            "get_campaign": lambda args: _get_campaign(campaign_service, args),
            "create_campaign": lambda args: _create_campaign(campaign_service, args),
            "update_campaign": lambda args: _update_campaign(campaign_service, args),
            "delete_campaign": lambda args: _delete_campaign(campaign_service, args),
        })

        logger.info(f"Registered {len(all_tools)} tools")
    else:
        logger.warning("No META_ACCESS_TOKEN found - server will start but tools will require configuration")

    @server.list_tools()
    async def list_tools():
        return all_tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if not meta_config:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "Meta Ads MCP Server is not configured with an access token",
                    "help": {
                        "steps": [
                            "1. Get a token from https://developers.facebook.com/tools/explorer/",
                            "2. Request permissions: ads_management, ads_read, business_management",
                            "3. Set META_ACCESS_TOKEN in your environment or Claude Desktop config",
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
            from src.utils.error_handler import handle_meta_api_error
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
