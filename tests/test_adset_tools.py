import json
import pytest
from unittest.mock import AsyncMock

from src.tools.adset import _list_ad_sets, _get_ad_set


@pytest.fixture
def mock_service():
    service = AsyncMock()
    service.get_ad_sets.return_value = [
        {"id": "1", "name": "Ad Set 1", "status": "ACTIVE", "campaign_id": "100"},
        {"id": "2", "name": "Ad Set 2", "status": "PAUSED", "campaign_id": "100"},
    ]
    service.get_ad_set.return_value = {
        "id": "1", "name": "Ad Set 1", "status": "ACTIVE", "campaign_id": "100",
    }
    return service


def _parse_response(result):
    assert len(result) == 1
    assert result[0].type == "text"
    return json.loads(result[0].text)


class TestListAdSets:
    async def test_returns_standard_shape(self, mock_service):
        result = await _list_ad_sets(mock_service, {"account_id": "123"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["data"]["count"] == 2
        assert len(data["data"]["ad_sets"]) == 2

    async def test_passes_campaign_filter(self, mock_service):
        await _list_ad_sets(mock_service, {"account_id": "123", "campaign_id": "100"})
        call_kwargs = mock_service.get_ad_sets.call_args.kwargs
        assert any(f["field"] == "campaign.id" for f in call_kwargs["filtering"])

    async def test_passes_status_filter(self, mock_service):
        await _list_ad_sets(mock_service, {"account_id": "123", "status_filter": "ACTIVE"})
        call_kwargs = mock_service.get_ad_sets.call_args.kwargs
        assert any(f["field"] == "status" for f in call_kwargs["filtering"])

    async def test_no_filtering_when_no_filters(self, mock_service):
        await _list_ad_sets(mock_service, {"account_id": "123"})
        call_kwargs = mock_service.get_ad_sets.call_args.kwargs
        assert call_kwargs["filtering"] is None


class TestGetAdSet:
    async def test_returns_standard_shape(self, mock_service):
        result = await _get_ad_set(mock_service, {"adset_id": "1"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["data"]["ad_set"]["id"] == "1"
