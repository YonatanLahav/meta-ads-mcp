from src.utils.error_handler import (
    MetaAdsError,
    handle_meta_api_error,
    is_retriable_error,
    RETRIABLE_ERROR_CODES,
)


class TestMetaAdsError:
    def test_is_retriable_with_retriable_code(self):
        for code in RETRIABLE_ERROR_CODES:
            err = MetaAdsError("test", code=code)
            assert err.is_retriable is True

    def test_is_not_retriable_with_normal_code(self):
        for code in [100, 190, 200, 368]:
            err = MetaAdsError("test", code=code, status_code=400)
            assert err.is_retriable is False

    def test_is_retriable_with_retriable_status(self):
        for status in [429, 500, 502, 503, 504]:
            err = MetaAdsError("test", code=100, status_code=status)
            assert err.is_retriable is True

    def test_to_dict(self):
        err = MetaAdsError("bad request", code=100, error_type="OAuthException", status_code=400)
        result = err.to_dict()
        assert result == {
            "success": False,
            "error": "bad request",
            "code": 100,
            "type": "OAuthException",
        }

    def test_to_dict_with_fbtrace(self):
        err = MetaAdsError("err", fbtrace_id="trace123")
        result = err.to_dict()
        assert result["fbtrace_id"] == "trace123"


class TestHandleMetaApiError:
    def test_returns_existing_meta_ads_error(self):
        original = MetaAdsError("original", code=42)
        result = handle_meta_api_error(original)
        assert result is original

    def test_parses_api_error_body(self):
        err = Exception("api error")
        err.body = {
            "error": {
                "message": "Rate limit hit",
                "code": 4,
                "type": "OAuthException",
                "fbtrace_id": "abc123",
                "error_subcode": 2446079,
            }
        }
        err.http_status = 429
        result = handle_meta_api_error(err)
        assert isinstance(result, MetaAdsError)
        assert str(result) == "Rate limit hit"
        assert result.code == 4
        assert result.fbtrace_id == "abc123"
        assert result.status_code == 429

    def test_handles_plain_exception(self):
        err = Exception("something broke")
        result = handle_meta_api_error(err)
        assert isinstance(result, MetaAdsError)
        assert result.code == "UNKNOWN"


class TestIsRetriableError:
    def test_meta_ads_error_delegates(self):
        err = MetaAdsError("rate limit", code=4)
        assert is_retriable_error(err) is True

    def test_raw_exception_with_retriable_code(self):
        err = Exception("rate limit")
        err.code = 4
        assert is_retriable_error(err) is True

    def test_raw_exception_with_retriable_status(self):
        err = Exception("server error")
        err.http_status = 502
        assert is_retriable_error(err) is True

    def test_non_retriable_exception(self):
        err = Exception("bad request")
        assert is_retriable_error(err) is False
