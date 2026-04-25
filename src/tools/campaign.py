from mcp.types import Tool, TextContent

from src.tools.helpers import success_response, extract_args


def get_campaign_tool_defs() -> list[Tool]:
    return [
        Tool(
            name="list_campaigns",
            description="List all campaigns for a Meta Ads account. Returns campaign details including name, status, objective, and budget.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Meta Ads account ID (with or without 'act_' prefix)"},
                    "limit": {"type": "integer", "description": "Max campaigns to return (default: 100)"},
                    "status_filter": {
                        "type": "string",
                        "enum": ["ACTIVE", "PAUSED", "DELETED", "ARCHIVED"],
                        "description": "Filter by status (optional)",
                    },
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="get_campaign",
            description="Get detailed information about a specific campaign by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "string", "description": "The campaign ID"},
                },
                "required": ["campaign_id"],
            },
        ),
        Tool(
            name="create_campaign",
            description="Create a new Meta Ads campaign. Requires name and objective.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Meta Ads account ID"},
                    "name": {"type": "string", "description": "Campaign name"},
                    "objective": {
                        "type": "string",
                        "enum": [
                            "OUTCOME_TRAFFIC", "OUTCOME_SALES", "OUTCOME_LEADS",
                            "OUTCOME_AWARENESS", "OUTCOME_ENGAGEMENT", "OUTCOME_APP_PROMOTION",
                        ],
                        "description": "Campaign objective",
                    },
                    "status": {"type": "string", "enum": ["ACTIVE", "PAUSED"], "description": "Status (default: PAUSED)"},
                    "daily_budget": {"type": "integer", "description": "Daily budget in cents"},
                    "lifetime_budget": {"type": "integer", "description": "Lifetime budget in cents"},
                    "special_ad_categories": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["CREDIT", "EMPLOYMENT", "HOUSING"]},
                        "description": "Special ad categories if applicable",
                    },
                },
                "required": ["account_id", "name", "objective"],
            },
        ),
        Tool(
            name="update_campaign",
            description="Update an existing campaign. Can modify name, status, budget, and bid strategy.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "string", "description": "Campaign ID to update"},
                    "account_id": {"type": "string", "description": "Meta Ads account ID (for rate limiting; optional)"},
                    "name": {"type": "string", "description": "New name"},
                    "status": {"type": "string", "enum": ["ACTIVE", "PAUSED", "ARCHIVED"]},
                    "daily_budget": {"type": "integer", "description": "New daily budget in cents"},
                    "lifetime_budget": {"type": "integer", "description": "New lifetime budget in cents"},
                },
                "required": ["campaign_id"],
            },
        ),
        Tool(
            name="delete_campaign",
            description="Delete (archive) a campaign. This cannot be undone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "string", "description": "Campaign ID to delete"},
                    "account_id": {"type": "string", "description": "Meta Ads account ID (for rate limiting; optional)"},
                },
                "required": ["campaign_id"],
            },
        ),
    ]


async def _list_campaigns(service, args: dict) -> list[TextContent]:
    filtering = None
    if args.get("status_filter"):
        filtering = [{"field": "status", "operator": "IN", "value": [args["status_filter"]]}]
    campaigns = await service.get_campaigns(
        account_id=args["account_id"],
        limit=args.get("limit", 100),
        filtering=filtering,
    )
    return success_response(f"Found {len(campaigns)} campaigns", {"count": len(campaigns), "campaigns": campaigns})


async def _get_campaign(service, args: dict) -> list[TextContent]:
    campaign = await service.get_campaign(args["campaign_id"])
    return success_response("Campaign retrieved", {"campaign": campaign})


async def _create_campaign(service, args: dict) -> list[TextContent]:
    campaign = await service.create_campaign(args["account_id"], extract_args(args, ["account_id"]))
    return success_response("Campaign created", {"campaign": campaign})


async def _update_campaign(service, args: dict) -> list[TextContent]:
    campaign_id = args["campaign_id"]
    account_id = args.get("account_id")
    await service.update_campaign(campaign_id, extract_args(args, ["campaign_id", "account_id"]), account_id=account_id)
    return success_response("Campaign updated", {"campaign_id": campaign_id, "updated": True})


async def _delete_campaign(service, args: dict) -> list[TextContent]:
    campaign_id = args["campaign_id"]
    account_id = args.get("account_id")
    await service.delete_campaign(campaign_id, account_id=account_id)
    return success_response("Campaign deleted", {"campaign_id": campaign_id, "deleted": True})
