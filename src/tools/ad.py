from mcp.types import Tool, TextContent

from src.tools.helpers import success_response


def get_ad_tool_defs() -> list[Tool]:
    return [
        Tool(
            name="list_ads",
            description="List ads for a Meta Ads account. Returns ad name, status, creative reference, and parent ad set/campaign IDs. Optionally filter by ad set, campaign, or status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Meta Ads account ID (with or without 'act_' prefix)"},
                    "adset_id": {"type": "string", "description": "Filter by ad set ID (optional)"},
                    "campaign_id": {"type": "string", "description": "Filter by campaign ID (optional)"},
                    "status_filter": {
                        "type": "string",
                        "enum": ["ACTIVE", "PAUSED", "DELETED", "ARCHIVED"],
                        "description": "Filter by status (optional)",
                    },
                    "limit": {"type": "integer", "description": "Max ads to return (default: 100)"},
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="get_ad",
            description="Get detailed information about a specific ad by ID. Returns ad name, status, creative reference, and parent ad set/campaign IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_id": {"type": "string", "description": "The ad ID"},
                },
                "required": ["ad_id"],
            },
        ),
    ]


async def _list_ads(service, args: dict) -> list[TextContent]:
    filtering = []
    if args.get("adset_id"):
        filtering.append({"field": "adset.id", "operator": "EQUAL", "value": args["adset_id"]})
    if args.get("campaign_id"):
        filtering.append({"field": "campaign.id", "operator": "EQUAL", "value": args["campaign_id"]})
    if args.get("status_filter"):
        filtering.append({"field": "effective_status", "operator": "IN", "value": [args["status_filter"]]})
    ads = await service.get_ads(
        account_id=args["account_id"],
        limit=args.get("limit", 100),
        filtering=filtering or None,
    )
    return success_response(f"Found {len(ads)} ads", {"count": len(ads), "ads": ads})


async def _get_ad(service, args: dict) -> list[TextContent]:
    ad = await service.get_ad(args["ad_id"])
    return success_response("Ad retrieved", {"ad": ad})
