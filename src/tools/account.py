import json
from mcp.types import Tool, TextContent

from src.services.account import AccountService


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


async def _list_ad_accounts(service: AccountService, args: dict) -> list[TextContent]:
    accounts = await service.get_ad_accounts(limit=args.get("limit", 100))
    return [TextContent(type="text", text=json.dumps({
        "success": True,
        "message": f"Found {len(accounts)} ad accounts",
        "data": {"count": len(accounts), "accounts": accounts},
    }, indent=2))]
