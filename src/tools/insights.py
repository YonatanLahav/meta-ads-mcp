from mcp.types import Tool, TextContent

from src.tools.helpers import success_response

DATE_PRESET_ENUM = [
    "today", "yesterday", "last_3d", "last_7d", "last_14d",
    "last_28d", "last_30d", "last_90d", "this_month", "last_month",
]

BREAKDOWN_ENUM = [
    "age", "gender", "country", "region", "dma",
    "device_platform", "publisher_platform", "platform_position",
    "impression_device",
]

TIME_RANGE_SCHEMA = {
    "type": "object",
    "properties": {
        "since": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
        "until": {"type": "string", "description": "End date (YYYY-MM-DD)"},
    },
    "required": ["since", "until"],
}


def get_insights_tool_defs() -> list[Tool]:
    return [
        Tool(
            name="get_account_insights",
            description="Get performance insights for an ad account. Returns spend, impressions, clicks, conversions, CPA, and more. Use 'level' to aggregate by campaign, ad set, or ad. IMPORTANT: For adset or ad level, always provide campaign_id to avoid timeouts on large accounts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Meta Ads account ID"},
                    "date_preset": {"type": "string", "enum": DATE_PRESET_ENUM, "description": "Predefined date range (default: last_7d). Cannot be used with time_range."},
                    "time_range": {**TIME_RANGE_SCHEMA, "description": "Custom date range. Cannot be used with date_preset."},
                    "level": {"type": "string", "enum": ["account", "campaign", "adset", "ad"], "description": "Aggregation level (default: campaign)"},
                    "campaign_id": {"type": "string", "description": "Filter results to a specific campaign (recommended for adset/ad level)"},
                    "adset_id": {"type": "string", "description": "Filter results to a specific ad set (recommended for ad level)"},
                    "limit": {"type": "integer", "description": "Max rows to return (default: 50)"},
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="get_campaign_insights",
            description="Get performance insights for a specific campaign. Returns spend, impressions, clicks, conversions, CPA, and more. Supports breakdowns by age, gender, country, device, placement.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "string", "description": "Campaign ID"},
                    "date_preset": {"type": "string", "enum": DATE_PRESET_ENUM, "description": "Predefined date range (default: last_7d). Cannot be used with time_range."},
                    "time_range": {**TIME_RANGE_SCHEMA, "description": "Custom date range. Cannot be used with date_preset."},
                    "breakdowns": {
                        "type": "array",
                        "items": {"type": "string", "enum": BREAKDOWN_ENUM},
                        "description": "Break down results by dimension (e.g. age, gender, country)",
                    },
                    "limit": {"type": "integer", "description": "Max rows to return (default: 100)"},
                },
                "required": ["campaign_id"],
            },
        ),
        Tool(
            name="get_adset_insights",
            description="Get performance insights for a specific ad set. Returns spend, impressions, clicks, conversions, CPA, and more. Supports breakdowns by age, gender, country, device, placement.",
            inputSchema={
                "type": "object",
                "properties": {
                    "adset_id": {"type": "string", "description": "Ad set ID"},
                    "date_preset": {"type": "string", "enum": DATE_PRESET_ENUM, "description": "Predefined date range (default: last_7d). Cannot be used with time_range."},
                    "time_range": {**TIME_RANGE_SCHEMA, "description": "Custom date range. Cannot be used with date_preset."},
                    "breakdowns": {
                        "type": "array",
                        "items": {"type": "string", "enum": BREAKDOWN_ENUM},
                        "description": "Break down results by dimension (e.g. age, gender, country)",
                    },
                    "limit": {"type": "integer", "description": "Max rows to return (default: 100)"},
                },
                "required": ["adset_id"],
            },
        ),
        Tool(
            name="get_ad_insights",
            description="Get performance insights for a specific ad. Returns spend, impressions, clicks, conversions, CPA, and more. Supports breakdowns by age, gender, country, device, placement.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_id": {"type": "string", "description": "Ad ID"},
                    "date_preset": {"type": "string", "enum": DATE_PRESET_ENUM, "description": "Predefined date range (default: last_7d). Cannot be used with time_range."},
                    "time_range": {**TIME_RANGE_SCHEMA, "description": "Custom date range. Cannot be used with date_preset."},
                    "breakdowns": {
                        "type": "array",
                        "items": {"type": "string", "enum": BREAKDOWN_ENUM},
                        "description": "Break down results by dimension (e.g. age, gender, country)",
                    },
                    "limit": {"type": "integer", "description": "Max rows to return (default: 100)"},
                },
                "required": ["ad_id"],
            },
        ),
    ]


async def _get_account_insights(service, args: dict) -> list[TextContent]:
    filtering = []
    if args.get("campaign_id"):
        filtering.append({"field": "campaign.id", "operator": "EQUAL", "value": args["campaign_id"]})
    if args.get("adset_id"):
        filtering.append({"field": "adset.id", "operator": "EQUAL", "value": args["adset_id"]})
    insights = await service.get_account_insights(
        account_id=args["account_id"],
        date_preset=args.get("date_preset", "last_7d"),
        time_range=args.get("time_range"),
        level=args.get("level", "campaign"),
        filtering=filtering or None,
        limit=args.get("limit", 50),
    )
    return success_response(f"Retrieved {len(insights)} insight rows", {"count": len(insights), "insights": insights})


async def _get_campaign_insights(service, args: dict) -> list[TextContent]:
    insights = await service.get_campaign_insights(
        campaign_id=args["campaign_id"],
        date_preset=args.get("date_preset", "last_7d"),
        time_range=args.get("time_range"),
        breakdowns=args.get("breakdowns"),
        limit=args.get("limit", 100),
    )
    return success_response(f"Retrieved {len(insights)} insight rows", {"count": len(insights), "insights": insights})


async def _get_adset_insights(service, args: dict) -> list[TextContent]:
    insights = await service.get_adset_insights(
        adset_id=args["adset_id"],
        date_preset=args.get("date_preset", "last_7d"),
        time_range=args.get("time_range"),
        breakdowns=args.get("breakdowns"),
        limit=args.get("limit", 100),
    )
    return success_response(f"Retrieved {len(insights)} insight rows", {"count": len(insights), "insights": insights})


async def _get_ad_insights(service, args: dict) -> list[TextContent]:
    insights = await service.get_ad_insights(
        ad_id=args["ad_id"],
        date_preset=args.get("date_preset", "last_7d"),
        time_range=args.get("time_range"),
        breakdowns=args.get("breakdowns"),
        limit=args.get("limit", 100),
    )
    return success_response(f"Retrieved {len(insights)} insight rows", {"count": len(insights), "insights": insights})
