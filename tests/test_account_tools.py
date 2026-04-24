import json
import pytest
from unittest.mock import AsyncMock

from src.tools.account import _list_ad_accounts, get_account_tool_defs


@pytest.fixture
def mock_service():
    service = AsyncMock()
    service.get_ad_accounts.return_value = [
        {"id": "act_1", "name": "Account 1", "currency": "USD"},
        {"id": "act_2", "name": "Account 2", "currency": "EUR"},
    ]
    return service


def _parse_response(result):
    assert len(result) == 1
    assert result[0].type == "text"
    return json.loads(result[0].text)


class TestListAdAccounts:
    async def test_returns_standard_shape(self, mock_service):
        result = await _list_ad_accounts(mock_service, {})
        data = _parse_response(result)
        assert data["success"] is True
        assert "message" in data
        assert data["data"]["count"] == 2
        assert len(data["data"]["accounts"]) == 2

    async def test_passes_limit(self, mock_service):
        await _list_ad_accounts(mock_service, {"limit": 50})
        mock_service.get_ad_accounts.assert_awaited_once_with(limit=50)

    async def test_defaults_limit_to_100(self, mock_service):
        await _list_ad_accounts(mock_service, {})
        mock_service.get_ad_accounts.assert_awaited_once_with(limit=100)


class TestAccountToolDefs:
    def test_returns_one_tool(self):
        tools = get_account_tool_defs()
        assert len(tools) == 1

    def test_tool_name(self):
        tools = get_account_tool_defs()
        assert tools[0].name == "list_ad_accounts"

    def test_schema_structure(self):
        tool = get_account_tool_defs()[0]
        assert tool.description
        assert tool.inputSchema["type"] == "object"
        assert "limit" in tool.inputSchema["properties"]
