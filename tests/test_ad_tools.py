import json
import pytest
from unittest.mock import AsyncMock

from src.tools.ad import _list_ads, _get_ad


@pytest.fixture
def mock_service():
    service = AsyncMock()
    service.get_ads.return_value = [
        {"id": "1", "name": "Ad 1", "status": "ACTIVE", "adset_id": "10"},
        {"id": "2", "name": "Ad 2", "status": "PAUSED", "adset_id": "10"},
    ]
    service.get_ad.return_value = {
        "id": "1", "name": "Ad 1", "status": "ACTIVE", "adset_id": "10",
    }
    return service


def _parse_response(result):
    assert len(result) == 1
    assert result[0].type == "text"
    return json.loads(result[0].text)


class TestListAds:
    async def test_returns_standard_shape(self, mock_service):
        result = await _list_ads(mock_service, {"account_id": "123"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["data"]["count"] == 2
        assert len(data["data"]["ads"]) == 2

    async def test_passes_adset_filter(self, mock_service):
        await _list_ads(mock_service, {"account_id": "123", "adset_id": "10"})
        call_kwargs = mock_service.get_ads.call_args.kwargs
        assert any(f["field"] == "adset.id" for f in call_kwargs["filtering"])

    async def test_passes_campaign_filter(self, mock_service):
        await _list_ads(mock_service, {"account_id": "123", "campaign_id": "100"})
        call_kwargs = mock_service.get_ads.call_args.kwargs
        assert any(f["field"] == "campaign.id" for f in call_kwargs["filtering"])

    async def test_passes_status_filter(self, mock_service):
        await _list_ads(mock_service, {"account_id": "123", "status_filter": "ACTIVE"})
        call_kwargs = mock_service.get_ads.call_args.kwargs
        assert any(f["field"] == "status" for f in call_kwargs["filtering"])

    async def test_no_filtering_when_no_filters(self, mock_service):
        await _list_ads(mock_service, {"account_id": "123"})
        call_kwargs = mock_service.get_ads.call_args.kwargs
        assert call_kwargs["filtering"] is None


class TestGetAd:
    async def test_returns_standard_shape(self, mock_service):
        result = await _get_ad(mock_service, {"ad_id": "1"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["data"]["ad"]["id"] == "1"
