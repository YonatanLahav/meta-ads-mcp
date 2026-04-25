from mcp.types import Tool, TextContent

from src.tools.helpers import success_response


def get_creative_tool_defs() -> list[Tool]:
    return [
        Tool(
            name="list_ad_creatives",
            description="List ad creatives for a Meta Ads account. Returns creative name, title, body text, image URL, call-to-action type, and object story spec.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Meta Ads account ID (with or without 'act_' prefix)"},
                    "limit": {"type": "integer", "description": "Max creatives to return (default: 100)"},
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="get_ad_creative",
            description="Get detailed information about a specific ad creative by ID. Returns title, body text, image URL/hash, call-to-action type, and full object story spec.",
            inputSchema={
                "type": "object",
                "properties": {
                    "creative_id": {"type": "string", "description": "The ad creative ID"},
                },
                "required": ["creative_id"],
            },
        ),
        Tool(
            name="get_ad_preview",
            description="Get an HTML preview of how an ad renders in a specific placement. Returns HTML that can be displayed to visualize the ad.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_id": {"type": "string", "description": "The ad ID to preview"},
                    "ad_format": {
                        "type": "string",
                        "enum": [
                            "DESKTOP_FEED_STANDARD",
                            "MOBILE_FEED_STANDARD",
                            "INSTAGRAM_STANDARD",
                            "INSTAGRAM_STORY",
                        ],
                        "description": "Ad placement format (default: DESKTOP_FEED_STANDARD)",
                    },
                },
                "required": ["ad_id"],
            },
        ),
        Tool(
            name="list_ad_images",
            description="List uploaded images for a Meta Ads account. Returns image URLs, dimensions, hashes, and upload dates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Meta Ads account ID (with or without 'act_' prefix)"},
                    "limit": {"type": "integer", "description": "Max images to return (default: 100)"},
                },
                "required": ["account_id"],
            },
        ),
    ]


async def _list_ad_creatives(service, args: dict) -> list[TextContent]:
    creatives = await service.get_ad_creatives(
        account_id=args["account_id"],
        limit=args.get("limit", 100),
    )
    return success_response(f"Found {len(creatives)} creatives", {"count": len(creatives), "creatives": creatives})


async def _get_ad_creative(service, args: dict) -> list[TextContent]:
    creative = await service.get_ad_creative(args["creative_id"])
    return success_response("Creative retrieved", {"creative": creative})


async def _get_ad_preview(service, args: dict) -> list[TextContent]:
    previews = await service.get_ad_preview(
        ad_id=args["ad_id"],
        ad_format=args.get("ad_format", "DESKTOP_FEED_STANDARD"),
    )
    return success_response(f"Retrieved {len(previews)} preview(s)", {"count": len(previews), "previews": previews})


async def _list_ad_images(service, args: dict) -> list[TextContent]:
    images = await service.get_ad_images(
        account_id=args["account_id"],
        limit=args.get("limit", 100),
    )
    return success_response(f"Found {len(images)} images", {"count": len(images), "images": images})
