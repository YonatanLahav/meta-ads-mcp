import json
from mcp.types import TextContent


def success_response(message: str, data: dict) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({
        "success": True,
        "message": message,
        "data": data,
    }, indent=2))]


def extract_args(args: dict, exclude: list[str]) -> dict:
    return {k: v for k, v in args.items() if k not in exclude}
