import json
import pytest
from unittest.mock import AsyncMock

from src.tools.audience import _list_custom_audiences, _get_custom_audience


@pytest.fixture
def mock_service():
    service = AsyncMock()
    service.get_custom_audiences.return_value = [
        {"id": "1", "name": "Purchasers", "subtype": "CUSTOM", "approximate_count_lower_bound": 45000, "approximate_count_upper_bound": 55000},
        {"id": "2", "name": "Lookalike 1%", "subtype": "LOOKALIKE", "approximate_count_lower_bound": 1800000, "approximate_count_upper_bound": 2200000},
    ]
    service.get_custom_audience.return_value = {
        "id": "1", "name": "Purchasers", "subtype": "CUSTOM", "approximate_count_lower_bound": 45000, "approximate_count_upper_bound": 55000,
    }
    return service


def _parse_response(result):
    assert len(result) == 1
    assert result[0].type == "text"
    return json.loads(result[0].text)


class TestListCustomAudiences:
    async def test_returns_standard_shape(self, mock_service):
        result = await _list_custom_audiences(mock_service, {"account_id": "123"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["data"]["count"] == 2
        assert len(data["data"]["audiences"]) == 2


class TestGetCustomAudience:
    async def test_returns_standard_shape(self, mock_service):
        result = await _get_custom_audience(mock_service, {"audience_id": "1"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["data"]["audience"]["id"] == "1"
        assert data["data"]["audience"]["subtype"] == "CUSTOM"
