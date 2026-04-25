import json
import pytest
from unittest.mock import AsyncMock

from src.tools.creative import (
    _list_ad_creatives,
    _get_ad_creative,
    _get_ad_preview,
    _list_ad_images,
)


@pytest.fixture
def mock_service():
    service = AsyncMock()
    service.get_ad_creatives.return_value = [
        {"id": "1", "name": "Creative 1", "title": "Buy Now"},
        {"id": "2", "name": "Creative 2", "title": "Learn More"},
    ]
    service.get_ad_creative.return_value = {
        "id": "1", "name": "Creative 1", "title": "Buy Now", "body": "Great deal",
    }
    service.get_ad_preview.return_value = [
        {"body": "<div>Preview HTML</div>"},
    ]
    service.get_ad_images.return_value = [
        {"id": "1", "hash": "abc123", "url": "https://example.com/img.jpg", "width": 1200, "height": 628},
    ]
    return service


def _parse_response(result):
    assert len(result) == 1
    assert result[0].type == "text"
    return json.loads(result[0].text)


class TestListAdCreatives:
    async def test_returns_standard_shape(self, mock_service):
        result = await _list_ad_creatives(mock_service, {"account_id": "123"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["data"]["count"] == 2
        assert len(data["data"]["creatives"]) == 2


class TestGetAdCreative:
    async def test_returns_standard_shape(self, mock_service):
        result = await _get_ad_creative(mock_service, {"creative_id": "1"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["data"]["creative"]["id"] == "1"


class TestGetAdPreview:
    async def test_returns_preview_html(self, mock_service):
        result = await _get_ad_preview(mock_service, {"ad_id": "1"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["data"]["count"] == 1
        assert "<div>" in data["data"]["previews"][0]["body"]

    async def test_passes_ad_format(self, mock_service):
        await _get_ad_preview(mock_service, {"ad_id": "1", "ad_format": "INSTAGRAM_STANDARD"})
        call_kwargs = mock_service.get_ad_preview.call_args.kwargs
        assert call_kwargs["ad_format"] == "INSTAGRAM_STANDARD"


class TestListAdImages:
    async def test_returns_standard_shape(self, mock_service):
        result = await _list_ad_images(mock_service, {"account_id": "123"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["data"]["count"] == 1
        assert data["data"]["images"][0]["hash"] == "abc123"
