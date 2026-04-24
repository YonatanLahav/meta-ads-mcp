import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from src.config.settings import load_meta_config
from src.tools.campaign import register_campaign_tools
from src.utils.logger import logger


def create_server() -> Server:
    server = Server("meta-ads-mcp-server")
    meta_config = load_meta_config()

    all_tools = []
    tool_handlers: dict[str, any] = {}

    if meta_config:
        campaign_service = __import__(
            "src.services.campaign", fromlist=["CampaignService"]
        ).CampaignService(meta_config)

        from src.tools.campaign import (
            _list_campaigns,
            _get_campaign,
            _create_campaign,
            _update_campaign,
            _delete_campaign,
        )

        campaign_tools = register_campaign_tools.__wrapped__(meta_config) if hasattr(register_campaign_tools, "__wrapped__") else None

        # Build tool list and handler map
        tool_defs = _build_campaign_tool_defs()
        all_tools.extend(tool_defs)

        tool_handlers.update({
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


def _build_campaign_tool_defs():
    from mcp.types import Tool
    return [
        Tool(
            name="list_campaigns",
            description="List all campaigns for a Meta Ads account.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Meta Ads account ID (with or without 'act_' prefix)"},
                    "limit": {"type": "integer", "description": "Max campaigns to return (default: 100)"},
                    "status_filter": {"type": "string", "enum": ["ACTIVE", "PAUSED", "DELETED", "ARCHIVED"], "description": "Filter by status"},
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="get_campaign",
            description="Get detailed information about a specific campaign by ID.",
            inputSchema={
                "type": "object",
                "properties": {"campaign_id": {"type": "string", "description": "The campaign ID"}},
                "required": ["campaign_id"],
            },
        ),
        Tool(
            name="create_campaign",
            description="Create a new Meta Ads campaign.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Meta Ads account ID"},
                    "name": {"type": "string", "description": "Campaign name"},
                    "objective": {"type": "string", "enum": ["OUTCOME_TRAFFIC", "OUTCOME_SALES", "OUTCOME_LEADS", "OUTCOME_AWARENESS", "OUTCOME_ENGAGEMENT", "OUTCOME_APP_PROMOTION"]},
                    "status": {"type": "string", "enum": ["ACTIVE", "PAUSED"]},
                    "daily_budget": {"type": "integer", "description": "Daily budget in cents"},
                    "lifetime_budget": {"type": "integer", "description": "Lifetime budget in cents"},
                    "special_ad_categories": {"type": "array", "items": {"type": "string", "enum": ["CREDIT", "EMPLOYMENT", "HOUSING"]}},
                },
                "required": ["account_id", "name", "objective"],
            },
        ),
        Tool(
            name="update_campaign",
            description="Update an existing campaign.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "string", "description": "Campaign ID to update"},
                    "name": {"type": "string"},
                    "status": {"type": "string", "enum": ["ACTIVE", "PAUSED", "ARCHIVED"]},
                    "daily_budget": {"type": "integer"},
                    "lifetime_budget": {"type": "integer"},
                },
                "required": ["campaign_id"],
            },
        ),
        Tool(
            name="delete_campaign",
            description="Delete (archive) a campaign. Cannot be undone.",
            inputSchema={
                "type": "object",
                "properties": {"campaign_id": {"type": "string", "description": "Campaign ID to delete"}},
                "required": ["campaign_id"],
            },
        ),
    ]


async def run():
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
