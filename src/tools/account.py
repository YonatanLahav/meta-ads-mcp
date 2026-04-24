from mcp.types import Tool, TextContent

from src.tools.helpers import success_response


def get_account_tool_defs() -> list[Tool]:
    return [
        Tool(
            name="list_ad_accounts",
            description="List all ad accounts accessible with the current access token. Use this to discover account IDs needed for other tools.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max accounts to return (default: 100)"},
                },
            },
        ),
    ]


async def _list_ad_accounts(service, args: dict) -> list[TextContent]:
    accounts = await service.get_ad_accounts(limit=args.get("limit", 100))
    return success_response(f"Found {len(accounts)} ad accounts", {"count": len(accounts), "accounts": accounts})
