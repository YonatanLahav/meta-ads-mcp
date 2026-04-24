import json
from mcp.types import TextContent


def success_response(message: str, data: dict) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({
        "success": True,
        "message": message,
        "data": data,
    }, indent=2))]
