from mcp.types import Tool, TextContent

from src.tools.helpers import success_response


def get_audience_tool_defs() -> list[Tool]:
    return [
        Tool(
            name="list_custom_audiences",
            description="List custom and lookalike audiences for a Meta Ads account. Returns audience name, type, approximate size, data source, and status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Meta Ads account ID (with or without 'act_' prefix)"},
                    "limit": {"type": "integer", "description": "Max audiences to return (default: 100)"},
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="get_custom_audience",
            description="Get detailed information about a specific custom audience by ID. Returns name, subtype, approximate size, data source, rules, and status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "audience_id": {"type": "string", "description": "The custom audience ID"},
                },
                "required": ["audience_id"],
            },
        ),
    ]


async def _list_custom_audiences(service, args: dict) -> list[TextContent]:
    audiences = await service.get_custom_audiences(
        account_id=args["account_id"],
        limit=args.get("limit", 100),
    )
    return success_response(f"Found {len(audiences)} audiences", {"count": len(audiences), "audiences": audiences})


async def _get_custom_audience(service, args: dict) -> list[TextContent]:
    audience = await service.get_custom_audience(args["audience_id"])
    return success_response("Audience retrieved", {"audience": audience})
