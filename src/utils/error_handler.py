from src.utils.logger import logger

RATE_LIMIT_ERROR_CODES = {4, 17, 80004, 613}
RETRIABLE_ERROR_CODES = {4, 17, 80004, 613}
RETRIABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}

ERROR_CODE_MESSAGES: dict[int, str] = {
    1: "An unknown error occurred",
    2: "Service temporarily unavailable",
    4: "API Too Many Calls - rate limit exceeded",
    10: "Permission denied - check token scopes",
    17: "User request limit reached",
    100: "Invalid parameter",
    190: "Access token has expired or is invalid",
    200: "Permission error - missing required permissions",
    368: "Temporarily blocked for policies violations",
    613: "Rate limit exceeded",
    803: "Some of the aliases you requested do not exist",
    80004: "Too many calls from this ad account",
    2635: "Campaign has been deleted",
}


class MetaAdsError(Exception):
    def __init__(
        self,
        message: str,
        code: int | str = "UNKNOWN",
        error_type: str = "API_ERROR",
        status_code: int = 500,
        fbtrace_id: str | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.error_type = error_type
        self.status_code = status_code
        self.fbtrace_id = fbtrace_id

    @property
    def is_rate_limit(self) -> bool:
        code = int(self.code) if str(self.code).isdigit() else -1
        return code in RATE_LIMIT_ERROR_CODES or self.status_code == 429

    @property
    def is_retriable(self) -> bool:
        if self.is_rate_limit:
            return True
        if self.status_code in RETRIABLE_HTTP_STATUSES:
            return True
        return False

    def to_dict(self) -> dict:
        result = {
            "success": False,
            "error": str(self),
            "code": self.code,
            "type": self.error_type,
        }
        if self.fbtrace_id:
            result["fbtrace_id"] = self.fbtrace_id
        return result


def handle_meta_api_error(error: Exception) -> MetaAdsError:
    if isinstance(error, MetaAdsError):
        return error

    message = "Unknown error occurred"
    code: int | str = "UNKNOWN"
    error_type = "API_ERROR"
    status_code = 500
    fbtrace_id = None

    try:
        body = getattr(error, "body", None) or {}
        api_error = body.get("error", {}) if isinstance(body, dict) else {}

        if api_error:
            message = api_error.get("message", message)
            code = api_error.get("code", code)
            error_type = api_error.get("type", error_type)
            fbtrace_id = api_error.get("fbtrace_id")
            status_code = getattr(error, "http_status", status_code)
        elif hasattr(error, "message"):
            message = error.message
    except Exception as parse_err:
        logger.error(f"Failed to parse Meta API error: {parse_err}")

    return MetaAdsError(message, code, error_type, status_code, fbtrace_id)


def is_retriable_error(error: Exception) -> bool:
    if isinstance(error, MetaAdsError):
        return error.is_retriable
    code = getattr(error, "code", None)
    if code and str(code).isdigit() and int(code) in RETRIABLE_ERROR_CODES:
        return True
    status = getattr(error, "http_status", None) or getattr(error, "status_code", None)
    try:
        if status and int(status) in RETRIABLE_HTTP_STATUSES:
            return True
    except (ValueError, TypeError):
        pass
    return False
