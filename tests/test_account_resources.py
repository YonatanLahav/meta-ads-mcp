import json
import pytest
from unittest.mock import AsyncMock

from src.resources.accounts import get_account_resource_defs, read_accounts, ACCOUNTS_URI


class TestAccountResourceDefs:
    def test_returns_single_resource(self):
        defs = get_account_resource_defs()
        assert len(defs) == 1

    def test_resource_uri(self):
        resource = get_account_resource_defs()[0]
        assert str(resource.uri) == ACCOUNTS_URI

    def test_resource_mime_type(self):
        resource = get_account_resource_defs()[0]
        assert resource.mimeType == "application/json"


class TestReadAccounts:
    async def test_returns_json_string(self):
        service = AsyncMock()
        service.get_ad_accounts.return_value = [
            {"id": "act_1", "name": "Account 1"},
            {"id": "act_2", "name": "Account 2"},
        ]
        result = await read_accounts(service)
        data = json.loads(result)
        assert data["count"] == 2
        assert len(data["accounts"]) == 2

    async def test_returns_empty_list(self):
        service = AsyncMock()
        service.get_ad_accounts.return_value = []
        result = await read_accounts(service)
        data = json.loads(result)
        assert data["count"] == 0
        assert data["accounts"] == []

    async def test_propagates_service_error(self):
        service = AsyncMock()
        service.get_ad_accounts.side_effect = Exception("API error")
        with pytest.raises(Exception, match="API error"):
            await read_accounts(service)
