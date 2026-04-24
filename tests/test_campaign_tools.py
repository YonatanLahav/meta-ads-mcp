import json
import pytest
from unittest.mock import AsyncMock

from src.tools.campaign import (
    _list_campaigns,
    _get_campaign,
    _create_campaign,
    _update_campaign,
    _delete_campaign,
)


@pytest.fixture
def mock_service():
    service = AsyncMock()
    service.get_campaigns.return_value = [
        {"id": "1", "name": "Campaign 1", "status": "ACTIVE"},
        {"id": "2", "name": "Campaign 2", "status": "PAUSED"},
    ]
    service.get_campaign.return_value = {"id": "1", "name": "Campaign 1", "status": "ACTIVE"}
    service.create_campaign.return_value = {"id": "3", "name": "New Campaign"}
    service.update_campaign.return_value = {"id": "1", "updated": True}
    service.delete_campaign.return_value = {"id": "1", "deleted": True}
    return service


def _parse_response(result):
    assert len(result) == 1
    assert result[0].type == "text"
    return json.loads(result[0].text)


class TestListCampaigns:
    async def test_returns_standard_shape(self, mock_service):
        result = await _list_campaigns(mock_service, {"account_id": "123"})
        data = _parse_response(result)
        assert data["success"] is True
        assert "message" in data
        assert data["data"]["count"] == 2
        assert len(data["data"]["campaigns"]) == 2

    async def test_passes_status_filter(self, mock_service):
        await _list_campaigns(mock_service, {"account_id": "123", "status_filter": "ACTIVE"})
        call_kwargs = mock_service.get_campaigns.call_args.kwargs
        assert call_kwargs["filtering"] == [{"field": "status", "operator": "IN", "value": ["ACTIVE"]}]


class TestGetCampaign:
    async def test_returns_standard_shape(self, mock_service):
        result = await _get_campaign(mock_service, {"campaign_id": "1"})
        data = _parse_response(result)
        assert data["success"] is True
        assert "message" in data
        assert data["data"]["campaign"]["id"] == "1"


class TestCreateCampaign:
    async def test_returns_standard_shape(self, mock_service):
        result = await _create_campaign(mock_service, {
            "account_id": "123", "name": "New", "objective": "OUTCOME_TRAFFIC",
        })
        data = _parse_response(result)
        assert data["success"] is True
        assert data["message"] == "Campaign created"
        assert "campaign" in data["data"]

    async def test_excludes_account_id_from_service_call(self, mock_service):
        await _create_campaign(mock_service, {
            "account_id": "123", "name": "New", "objective": "OUTCOME_TRAFFIC",
        })
        call_args = mock_service.create_campaign.call_args
        assert call_args[0][0] == "123"
        assert "account_id" not in call_args[0][1]


class TestUpdateCampaign:
    async def test_returns_standard_shape(self, mock_service):
        result = await _update_campaign(mock_service, {"campaign_id": "1", "name": "Updated"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["message"] == "Campaign updated"
        assert data["data"]["campaign_id"] == "1"
        assert data["data"]["updated"] is True

    async def test_does_not_mutate_args(self, mock_service):
        args = {"campaign_id": "1", "name": "Updated"}
        await _update_campaign(mock_service, args)
        assert "campaign_id" in args


class TestDeleteCampaign:
    async def test_returns_standard_shape(self, mock_service):
        result = await _delete_campaign(mock_service, {"campaign_id": "1"})
        data = _parse_response(result)
        assert data["success"] is True
        assert data["message"] == "Campaign deleted"
        assert data["data"]["campaign_id"] == "1"
        assert data["data"]["deleted"] is True
