import json
from mcp.types import TextContent


class _SDKEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "export_all_data"):
            return obj.export_all_data()
        return super().default(obj)


def success_response(message: str, data: dict) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({
        "success": True,
        "message": message,
        "data": data,
    }, indent=2, cls=_SDKEncoder))]


def extract_args(args: dict, exclude: list[str]) -> dict:
    return {k: v for k, v in args.items() if k not in exclude}
