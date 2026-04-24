import pytest
from unittest.mock import patch, MagicMock
from src.types.config import MetaAdsConfig


@pytest.fixture
def mock_meta_config():
    return MetaAdsConfig(
        access_token="test-token-123",
        api_version="v21.0",
        app_id="test-app-id",
        app_secret="test-app-secret",
    )


@pytest.fixture(autouse=True)
def patch_facebook_api():
    with patch("facebook_business.api.FacebookAdsApi.init", return_value=MagicMock()):
        yield
