from mcp.types import Tool, TextContent

from src.tools.helpers import success_response


def get_adset_tool_defs() -> list[Tool]:
    return [
        Tool(
            name="list_ad_sets",
            description="List ad sets for a Meta Ads account. Returns targeting, budget, optimization goal, billing event, and schedule. Optionally filter by campaign or status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Meta Ads account ID (with or without 'act_' prefix)"},
                    "campaign_id": {"type": "string", "description": "Filter by campaign ID (optional)"},
                    "status_filter": {
                        "type": "string",
                        "enum": ["ACTIVE", "PAUSED", "DELETED", "ARCHIVED"],
                        "description": "Filter by status (optional)",
                    },
                    "limit": {"type": "integer", "description": "Max ad sets to return (default: 100)"},
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="get_ad_set",
            description="Get detailed information about a specific ad set by ID. Returns targeting, budget, optimization goal, billing event, and schedule.",
            inputSchema={
                "type": "object",
                "properties": {
                    "adset_id": {"type": "string", "description": "The ad set ID"},
                },
                "required": ["adset_id"],
            },
        ),
    ]


async def _list_ad_sets(service, args: dict) -> list[TextContent]:
    filtering = []
    if args.get("campaign_id"):
        filtering.append({"field": "campaign.id", "operator": "EQUAL", "value": args["campaign_id"]})
    if args.get("status_filter"):
        filtering.append({"field": "status", "operator": "IN", "value": [args["status_filter"]]})
    ad_sets = await service.get_ad_sets(
        account_id=args["account_id"],
        limit=args.get("limit", 100),
        filtering=filtering or None,
    )
    return success_response(f"Found {len(ad_sets)} ad sets", {"count": len(ad_sets), "ad_sets": ad_sets})


async def _get_ad_set(service, args: dict) -> list[TextContent]:
    ad_set = await service.get_ad_set(args["adset_id"])
    return success_response("Ad set retrieved", {"ad_set": ad_set})
